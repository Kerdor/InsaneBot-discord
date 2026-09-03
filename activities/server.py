"""Minimal HTTP backend for Discord Activity authentication and results."""

from __future__ import annotations

import json
import os
import secrets
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from utils.activity_rewards import TrustedActivityResult, apply_trusted_result


DISCORD_TOKEN_URL = "https://discord.com/api/oauth2/token"
DISCORD_USER_URL = "https://discord.com/api/users/@me"
ACTIVITY_SESSION_TTL = 3600
SNAKE_MAX_SCORE = 397
SNAKE_MAX_INPUTS = 20000
SNAKE_MAX_TICKS = 100000
SNAKE_GAME_TTL = 900
SNAKE_GRID_SIZE = 20
SNAKE_XP_PER_POINT = 15
SNAKE_COINS_PER_POINT = 25
SNAKE_DIRECTIONS = {
    "ArrowUp": (0, -1),
    "ArrowDown": (0, 1),
    "ArrowLeft": (-1, 0),
    "ArrowRight": (1, 0),
}


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
        with self.server.activity_sessions_lock:
            session = self.server.activity_sessions.get(session_id)
            if session is None:
                return None
            if session["expires_at"] <= time.time():
                self.server.activity_sessions.pop(session_id, None)
                return None
            return dict(session)

    def do_GET(self) -> None:
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
        if self.path == "/api/discord/token":
            self._handle_token_exchange()
            return
        if self.path == "/api/activity/log":
            self._handle_activity_log()
            return
        if self.path == "/api/activities/snake/start":
            self._handle_snake_start()
            return
        if self.path == "/api/activities/snake/result":
            self._handle_snake_result()
            return
        self._send_json(404, {"error": "Not found"})

    def _read_json_body(self) -> dict | None:
        content_length = int(self.headers.get("Content-Length", "0"))
        if content_length <= 0 or content_length > 256 * 1024:
            return None
        payload = json.loads(self.rfile.read(content_length).decode("utf-8"))
        return payload if isinstance(payload, dict) else None

    def _handle_activity_log(self) -> None:
        try:
            payload = self._read_json_body()
            if payload is None:
                self._send_json(400, {"error": "Invalid diagnostic log body"})
                return
            message = payload.get("message")
            if not isinstance(message, str) or not message.strip() or len(message) > 500:
                self._send_json(400, {"error": "Invalid diagnostic log message"})
                return
            entry = {
                "time": payload.get("time") if isinstance(payload.get("time"), str) else "",
                "message": message.strip(),
            }
            data = payload.get("data")
            if data is not None:
                try:
                    serialized_data = json.dumps(data, ensure_ascii=False, separators=(",", ":"))
                except (TypeError, ValueError):
                    serialized_data = "<unserializable>"
                if len(serialized_data) > 4000:
                    serialized_data = serialized_data[:4000] + "..."
                entry["data"] = serialized_data
            log_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "logs"))
            os.makedirs(log_dir, exist_ok=True)
            log_file = os.path.join(log_dir, "activity_client.log")
            with open(log_file, "a", encoding="utf-8") as handle:
                handle.write(json.dumps(entry, ensure_ascii=False) + "\n")
            self._send_json(204, {})
        except (ValueError, UnicodeDecodeError):
            self._send_json(400, {"error": "Invalid diagnostic log JSON"})
        except OSError as exc:
            print(f"[ACTIVITY LOG] Write failed: {type(exc).__name__}: {exc}")
            self._send_json(500, {"error": "Diagnostic log write failed"})

    def _handle_snake_start(self) -> None:
        session = self._get_session()
        if session is None:
            self._send_json(401, {"error": "Activity session is not authenticated"})
            return
        game_id = secrets.token_urlsafe(24)
        result_id = secrets.token_urlsafe(24)
        seed = secrets.randbits(32)
        game = {
            "game_id": game_id,
            "result_id": result_id,
            "seed": seed,
            "user_id": session["user_id"],
            "instance_id": session["instance_id"],
            "guild_id": session["guild_id"],
            "channel_id": session["channel_id"],
            "created_at": time.time(),
        }
        with self.server.activity_games_lock:
            self.server.activity_games[game_id] = game
        self._send_json(200, {"game_id": game_id, "result_id": result_id, "seed": seed})

    def _handle_snake_result(self) -> None:
        session = self._get_session()
        if session is None:
            self._send_json(401, {"error": "Activity session is not authenticated"})
            return
        try:
            payload = self._read_json_body()
            if payload is None:
                self._send_json(400, {"error": "Invalid request body"})
                return
            game_id = payload.get("game_id")
            result_id = payload.get("result_id")
            activity_key = payload.get("activity_key")
            score = payload.get("score")
            reason = payload.get("reason")
            tick_count = payload.get("tick_count")
            seed = payload.get("seed")
            inputs = payload.get("inputs")
            instance_id = payload.get("instance_id")
            guild_id = payload.get("guild_id")
            channel_id = payload.get("channel_id")
            if not isinstance(game_id, str) or not game_id.strip() or len(game_id) > 128:
                self._send_json(400, {"error": "Valid game ID is required"})
                return
            if not isinstance(result_id, str) or not result_id.strip() or len(result_id) > 128:
                self._send_json(400, {"error": "Valid result ID is required"})
                return
            if activity_key != "snake":
                self._send_json(400, {"error": "Invalid Activity key"})
                return
            if reason not in {"game_over", "win"}:
                self._send_json(400, {"error": "Invalid Snake finish reason"})
                return
            if not isinstance(score, int) or isinstance(score, bool) or not 0 <= score <= SNAKE_MAX_SCORE:
                self._send_json(400, {"error": "Invalid Snake score"})
                return
            if not isinstance(tick_count, int) or isinstance(tick_count, bool) or not 1 <= tick_count <= SNAKE_MAX_TICKS:
                self._send_json(400, {"error": "Invalid Snake tick count"})
                return
            if not isinstance(seed, int) or isinstance(seed, bool) or not 0 <= seed <= 0xFFFFFFFF:
                self._send_json(400, {"error": "Invalid Snake seed"})
                return
            if not isinstance(inputs, list) or len(inputs) > SNAKE_MAX_INPUTS:
                self._send_json(400, {"error": "Invalid Snake input trace"})
                return
            if instance_id != session["instance_id"]:
                self._send_json(403, {"error": "Activity instance identity mismatch"})
                return
            if guild_id != session["guild_id"]:
                self._send_json(403, {"error": "Activity guild identity mismatch"})
                return
            if channel_id != session["channel_id"]:
                self._send_json(403, {"error": "Activity channel identity mismatch"})
                return
            with self.server.activity_games_lock:
                game = self.server.activity_games.get(game_id)
                if game is None:
                    self._send_json(404, {"error": "Snake game not found or already submitted"})
                    return
                if game["created_at"] + SNAKE_GAME_TTL <= time.time():
                    self.server.activity_games.pop(game_id, None)
                    self._send_json(410, {"error": "Snake game expired"})
                    return
                if game["result_id"] != result_id or game["seed"] != seed:
                    self._send_json(403, {"error": "Snake game identity mismatch"})
                    return
                if game["user_id"] != session["user_id"]:
                    self._send_json(403, {"error": "Snake game user mismatch"})
                    return
                if game["instance_id"] != session["instance_id"] or game["guild_id"] != session["guild_id"] or game["channel_id"] != session["channel_id"]:
                    self._send_json(403, {"error": "Snake game context mismatch"})
                    return
                validation = self._replay_snake(game["seed"], inputs, tick_count)
                if validation is None:
                    self._send_json(400, {"error": "Snake replay validation failed"})
                    return
                expected_score, expected_reason = validation
                if expected_score != score or expected_reason != reason:
                    self._send_json(400, {"error": "Snake result does not match server replay"})
                    return
                trusted_result = TrustedActivityResult(
                    result_id=result_id,
                    activity_key="snake",
                    guild_id=int(session["guild_id"]),
                    user_id=int(session["user_id"]),
                    xp_reward=score * SNAKE_XP_PER_POINT,
                    coin_reward=score * SNAKE_COINS_PER_POINT,
                )
                reward_applied = apply_trusted_result(trusted_result)
                result = {
                    "result_id": result_id,
                    "activity_key": "snake",
                    "guild_id": session["guild_id"],
                    "user_id": session["user_id"],
                    "score": score,
                    "xp_reward": trusted_result.xp_reward,
                    "coin_reward": trusted_result.coin_reward,
                    "reward_applied": reward_applied,
                    "instance_id": session["instance_id"],
                    "channel_id": session["channel_id"],
                    "game_id": game_id,
                    "reason": reason,
                    "tick_count": tick_count,
                }
                self.server.activity_results[result_id] = result
                self.server.activity_games.pop(game_id, None)
            self._send_json(200, {"accepted": True, "result": result})
        except (ValueError, UnicodeDecodeError):
            self._send_json(400, {"error": "Invalid JSON request"})
        except Exception as exc:
            print(f"[ACTIVITY RESULT] Snake validation/reward failed: {type(exc).__name__}: {exc}")
            self._send_json(500, {"error": "Snake result processing failed"})

    @staticmethod
    def _next_snake_random(state: int) -> tuple[int, float]:
        state &= 0xFFFFFFFF
        state ^= (state << 13) & 0xFFFFFFFF
        state ^= state >> 17
        state ^= (state << 5) & 0xFFFFFFFF
        state &= 0xFFFFFFFF
        return state, state / 4294967296

    @classmethod
    def _snake_food(cls, snake: list[tuple[int, int]], random_state: int) -> tuple[tuple[int, int], int]:
        occupied = set(snake)
        free_cells = [
            (x, y)
            for y in range(SNAKE_GRID_SIZE)
            for x in range(SNAKE_GRID_SIZE)
            if (x, y) not in occupied
        ]
        if not free_cells:
            return (0, 0), random_state
        random_state, random_value = cls._next_snake_random(random_state)
        return free_cells[int(random_value * len(free_cells))], random_state

    @classmethod
    def _replay_snake(cls, seed: int, inputs: list, tick_count: int) -> tuple[int, str] | None:
        if not isinstance(seed, int) or isinstance(seed, bool) or not 0 <= seed <= 0xFFFFFFFF:
            return None
        snake = [(10, 10), (9, 10), (8, 10)]
        direction = (1, 0)
        next_direction = (1, 0)
        random_state = seed
        food, random_state = cls._snake_food(snake, random_state)
        normalized_inputs = []
        last_tick = -1
        for item in inputs:
            if not isinstance(item, dict):
                return None
            input_tick = item.get("tick")
            input_direction = item.get("direction")
            if not isinstance(input_tick, int) or isinstance(input_tick, bool) or input_tick < 0 or input_tick >= tick_count or input_tick < last_tick or input_direction not in SNAKE_DIRECTIONS:
                return None
            dx, dy = SNAKE_DIRECTIONS[input_direction]
            if (dx, dy) == (-direction[0], -direction[1]) or (dx, dy) == (-next_direction[0], -next_direction[1]):
                return None
            next_direction = (dx, dy)
            normalized_inputs.append((input_tick, next_direction))
            last_tick = input_tick
        input_index = 0
        score = 0
        for current_tick in range(tick_count):
            while input_index < len(normalized_inputs) and normalized_inputs[input_index][0] == current_tick:
                next_direction = normalized_inputs[input_index][1]
                input_index += 1
            direction = next_direction
            head_x, head_y = snake[0]
            next_head = (head_x + direction[0], head_y + direction[1])
            if next_head[0] < 0 or next_head[0] >= SNAKE_GRID_SIZE or next_head[1] < 0 or next_head[1] >= SNAKE_GRID_SIZE:
                if current_tick + 1 != tick_count:
                    return None
                return score, "game_over"
            if next_head in snake[:-1]:
                if current_tick + 1 != tick_count:
                    return None
                return score, "game_over"
            snake.insert(0, next_head)
            if next_head == food:
                score += 1
                food, random_state = cls._snake_food(snake, random_state)
                if len(snake) == SNAKE_GRID_SIZE * SNAKE_GRID_SIZE:
                    if current_tick + 1 != tick_count:
                        return None
                    return score, "win"
            else:
                snake.pop()
        return None

    def _handle_token_exchange(self) -> None:
        client_id = os.getenv("DISCORD_ACTIVITY_CLIENT_ID", "").strip()
        client_secret = os.getenv("DISCORD_ACTIVITY_CLIENT_SECRET", "").strip()
        if not client_id or not client_secret:
            self._send_json(503, {"error": "Activity OAuth is not configured"})
            return
        try:
            payload = self._read_json_body()
            if payload is None:
                self._send_json(400, {"error": "Invalid request body"})
                return
            code = payload.get("code", "")
            instance_id = payload.get("instance_id")
            guild_id = payload.get("guild_id")
            channel_id = payload.get("channel_id")
            if not isinstance(code, str) or not code.strip() or not isinstance(instance_id, str) or not instance_id.strip() or not isinstance(guild_id, str) or not guild_id.strip() or not isinstance(channel_id, str) or not channel_id.strip():
                self._send_json(400, {"error": "Authorization code and Activity context are required"})
                return
            form = urlencode({"client_id": client_id, "client_secret": client_secret, "grant_type": "authorization_code", "code": code}).encode("utf-8")
            request = Request(DISCORD_TOKEN_URL, data=form, headers={"Content-Type": "application/x-www-form-urlencoded"}, method="POST")
            with urlopen(request, timeout=10) as response:
                discord_payload = json.loads(response.read().decode("utf-8"))
            access_token = discord_payload.get("access_token")
            if not isinstance(access_token, str) or not access_token:
                self._send_json(502, {"error": "Discord did not return an access token"})
                return
            user_request = Request(DISCORD_USER_URL, headers={"Authorization": f"Bearer {access_token}"}, method="GET")
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
                self.server.activity_sessions[session_id] = {"user_id": user_id, "username": username, "instance_id": instance_id, "guild_id": guild_id, "channel_id": channel_id, "expires_at": expires_at}
            self._send_json(200, {"access_token": access_token}, {"Set-Cookie": f"insanebot_activity_session={session_id}; HttpOnly; Path=/api/discord; SameSite=Lax"})
        except (ValueError, UnicodeDecodeError):
            self._send_json(400, {"error": "Invalid JSON request"})
        except Exception as exc:
            print(f"[ACTIVITY AUTH] Token exchange failed: {type(exc).__name__}: {exc}")
            self._send_json(502, {"error": "Discord token exchange failed"})

    def log_message(self, format: str, *args) -> None:
        return


def create_activity_server(host: str, port: int) -> ThreadingHTTPServer:
    server = ThreadingHTTPServer((host, port), ActivityRequestHandler)
    server.activity_sessions = {}
    server.activity_sessions_lock = threading.Lock()
    server.activity_games = {}
    server.activity_games_lock = threading.Lock()
    server.activity_results = {}
    return server
