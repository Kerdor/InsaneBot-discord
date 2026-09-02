"""Minimal HTTP backend for Discord Activity authentication.

The Activity frontend sends the one-time authorization code received from the
Embedded App SDK here. The backend exchanges that code with Discord using the
application client secret, which must never be exposed to the browser.
"""

from __future__ import annotations

import json
import os
import secrets
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlencode
from urllib.request import Request, urlopen


DISCORD_TOKEN_URL = "https://discord.com/api/oauth2/token"
DISCORD_USER_URL = "https://discord.com/api/users/@me"
ACTIVITY_SESSION_TTL = 3600


class ActivityRequestHandler(BaseHTTPRequestHandler):
    """Handle the private backend endpoints used by the Activity client."""

    server_version = "InsaneBotActivity/0.1"

    def _send_json(self, status: int, payload: dict, headers: dict | None = None) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        for name, value in (headers or {}).items():
            self.send_header(name, value)
        self.end_headers()
        self.wfile.write(body)

    def _get_session(self) -> dict | None:
        cookie = self.headers.get("Cookie", "")
        prefix = "insanebot_activity_session="
        session_id = next(
            (
                item.split("=", 1)[1]
                for item in cookie.split(";")
                if item.strip().startswith(prefix)
            ),
            None,
        )
        if not session_id:
            return None

        sessions = self.server.activity_sessions
        with self.server.activity_sessions_lock:
            session = sessions.get(session_id)
            if session is None:
                return None
            if session["expires_at"] <= time.time():
                sessions.pop(session_id, None)
                return None
            return dict(session)

    def do_GET(self) -> None:
        """Return the identity bound to the current Activity session."""
        if self.path != "/api/discord/session":
            self._send_json(404, {"error": "Not found"})
            return

        session = self._get_session()
        if session is None:
            self._send_json(401, {"error": "Activity session is not authenticated"})
            return

        self._send_json(
            200,
            {
                "user_id": session["user_id"],
                "username": session["username"],
                "instance_id": session["instance_id"],
                "guild_id": session["guild_id"],
                "channel_id": session["channel_id"],
                "expires_at": session["expires_at"],
            },
        )

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
            instance_id = payload.get("instance_id")
            guild_id = payload.get("guild_id")
            channel_id = payload.get("channel_id")

            if not isinstance(code, str) or not code.strip():
                self._send_json(400, {"error": "Authorization code is required"})
                return
            if not isinstance(instance_id, str) or not instance_id.strip():
                self._send_json(400, {"error": "Activity instance ID is required"})
                return
            if not isinstance(guild_id, str) or not guild_id.strip():
                self._send_json(400, {"error": "Activity guild ID is required"})
                return
            if not isinstance(channel_id, str) or not channel_id.strip():
                self._send_json(400, {"error": "Activity channel ID is required"})
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

            user_request = Request(
                DISCORD_USER_URL,
                headers={"Authorization": f"Bearer {access_token}"},
                method="GET",
            )
            with urlopen(user_request, timeout=10) as response:
                user_payload = json.loads(response.read().decode("utf-8"))

            user_id = user_payload.get("id")
            username = user_payload.get("username")
            if not isinstance(user_id, str) or not user_id:
                self._send_json(502, {"error": "Discord did not return a valid user identity"})
                return
            if not isinstance(username, str):
                username = "Discord user"

            session_id = secrets.token_urlsafe(32)
            expires_at = time.time() + ACTIVITY_SESSION_TTL
            with self.server.activity_sessions_lock:
                self.server.activity_sessions[session_id] = {
                    "user_id": user_id,
                    "username": username,
                    "instance_id": instance_id,
                    "guild_id": guild_id,
                    "channel_id": channel_id,
                    "expires_at": expires_at,
                }

            self._send_json(
                200,
                {"access_token": access_token},
                {
                    "Set-Cookie": (
                        f"insanebot_activity_session={session_id}; "
                        "HttpOnly; Path=/api/discord; SameSite=Lax"
                    )
                },
            )
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
    server = ThreadingHTTPServer((host, port), ActivityRequestHandler)
    server.activity_sessions = {}
    server.activity_sessions_lock = threading.Lock()
    return server
