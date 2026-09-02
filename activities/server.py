"""Minimal HTTP backend for Discord Activity authentication.

The Activity frontend sends the one-time authorization code received from the
Embedded App SDK here. The backend exchanges that code with Discord using the
application client secret, which must never be exposed to the browser.
"""

from __future__ import annotations

import json
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlencode
from urllib.request import Request, urlopen


DISCORD_TOKEN_URL = "https://discord.com/api/oauth2/token"


class ActivityRequestHandler(BaseHTTPRequestHandler):
    """Handle the private backend endpoint used by the Activity client."""

    server_version = "InsaneBotActivity/0.1"

    def _send_json(self, status: int, payload: dict) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self) -> None:
        """Exchange a Discord Activity authorization code for an access token."""
        if self.path != "/api/discord/token":
            self._send_json(404, {"error": "Not found"})
            return

        client_id = os.getenv("DISCORD_ACTIVITY_CLIENT_ID", "").strip()
        client_secret = os.getenv("DISCORD_ACTIVITY_CLIENT_SECRET", "").strip()
        if not client_id or not client_secret:
            self._send_json(503, {"error": "Activity OAuth is not configured"})
            return

        try:
            content_length = int(self.headers.get("Content-Length", "0"))
            if content_length <= 0 or content_length > 16 * 1024:
                self._send_json(400, {"error": "Invalid request body"})
                return

            payload = json.loads(self.rfile.read(content_length).decode("utf-8"))
            code = payload.get("code", "")
            if not isinstance(code, str) or not code.strip():
                self._send_json(400, {"error": "Authorization code is required"})
                return

            form = urlencode(
                {
                    "client_id": client_id,
                    "client_secret": client_secret,
                    "grant_type": "authorization_code",
                    "code": code,
                }
            ).encode("utf-8")
            request = Request(
                DISCORD_TOKEN_URL,
                data=form,
                headers={"Content-Type": "application/x-www-form-urlencoded"},
                method="POST",
            )

            with urlopen(request, timeout=10) as response:
                discord_payload = json.loads(response.read().decode("utf-8"))

            access_token = discord_payload.get("access_token")
            if not isinstance(access_token, str) or not access_token:
                self._send_json(502, {"error": "Discord did not return an access token"})
                return

            self._send_json(200, {"access_token": access_token})
        except ValueError:
            self._send_json(400, {"error": "Invalid JSON request"})
        except Exception as exc:
            print(f"[ACTIVITY AUTH] Token exchange failed: {type(exc).__name__}: {exc}")
            self._send_json(502, {"error": "Discord token exchange failed"})

    def log_message(self, format: str, *args) -> None:
        """Keep the standard HTTP server quiet except for application diagnostics."""
        return


def create_activity_server(host: str, port: int) -> ThreadingHTTPServer:
    """Create the Activity backend server without starting its serving loop."""
    return ThreadingHTTPServer((host, port), ActivityRequestHandler)
