# InsaneBot-discord — PROJECT STATE / MASTER ROADMAP

Repository: https://github.com/Kerdor/InsaneBot-discord  
Branch: `main`  
State date: 2026-09-02  
Current phase: **IMPLEMENTATION FIRST**

> This file is the authoritative hand-off document. GitHub `main` is the final source of truth when source and this document disagree.

## 1. BINDING DEVELOPMENT RULES

- Inspect current `main` and this file before serious changes.
- Preserve architecture and existing behavior unless a change is required.
- Make the smallest correct change.
- No unnecessary dependencies.
- Never use `...` as omitted code.
- Changed functions must be complete when manual replacement is required.
- Never delete/reset runtime databases.
- Normal changes go directly to `main`.
- **Update `PROJECT_STATE.md` after every project action/change.**
- `IMPLEMENTED` does not mean `QA PASSED`.
- CI success is not runtime QA.
- Do not start full system-by-system QA until planned implementation is complete.
- User prefers technical-editor/developer work: identify the problem briefly, preserve logic/architecture, make minimal changes, and give exact ready-to-use code when manual replacement is needed.

## 2. PRODUCT CONCEPT

InsaneBot is a Discord **community/progression bot**, not a traditional RPG.

Core loop:

```text
Discord activity → XP / Economy → Levels / Rankings / Quests / Achievements / Profile
messages / voice / daily / quests / shop / mini-games / future Activities
```

Do not add without explicit approval: talismans, combat items, loot boxes, RPG equipment/inventory, meaningless RPG stats, combat systems without community purpose, PvP, collecting.

Planned product directions: mini-games, Discord Activities, social interactions, Friends, Romantic relationships, richer profile cosmetics.

## 3. TECHNOLOGY / ARCHITECTURE

Python; `disnake>=2.12.1,<3`; Pillow `>=11,<13`; built-in `sqlite3`.

Main structure:

```text
config.py
main.py
dev_runner.py
server_structure.py
logs.py
cogs/
  owner.py owner_dump.py rebuild_command.py rebuild_test_server.py
  server_manager.py verification.py moderation.py tickets.py xp.py economy.py shop.py quests.py achievements.py minigames.py social.py activity_server.py admin_panel.py
  user_cmd/create_voice.py
  logging/{chat_logs,guild_logs,moderation_logs,setup_logs,system_logs,voice_stats}.py
  logging/reaction_logs.py (disabled)
databases/
  xp.py economy.py shop.py quests.py achievements.py
  profile_customization.py moderation.py tickets.py voice_stats.py voice_rooms.py social.py activities.py
utils/profile_card.py activity_registry.py activity_rewards.py
activities/
  __init__.py
  server.py
  client/package.json
  client/index.html
  client/src/main.js
  client/src/snake.js
  client/vite.config.js
```

Legacy `get_roles.py` remains unloaded. `reaction_logs.py` remains intentionally disabled.

## 4. TEST / MAIN

```text
ENVIRONMENT=test
MAIN_GUILD_ID=1217530337664434246
TEST_GUILD_ID=519209364280573954
TEST_GUILDS=[519209364280573954]
```

TEST guild: `Insane TEST` / `519209364280573954`. Production must not silently consume TEST mappings.

Historical isolation/logging fixes:

```text
f4321d9aa022b7085c19b510cf965d073d4ed544 → TEST/MAIN isolation
f19eedcf4f3bbc1476aabc9f17f6f355602e5590 → logging map compatibility
```

## 5. ACTIVE COG LOAD ORDER

```text
cogs.owner
cogs.owner_dump
cogs.rebuild_command
cogs.server_manager
cogs.verification
cogs.user_cmd.create_voice
cogs.tickets
cogs.moderation
cogs.xp
cogs.economy
cogs.logging.chat_logs
cogs.logging.guild_logs
cogs.logging.moderation_logs
cogs.logging.setup_logs
cogs.logging.voice_stats
cogs.logging.system_logs
cogs.shop
cogs.quests
cogs.achievements
cogs.minigames
cogs.social
cogs.activity_server
cogs.admin_panel
```

## 6. DATABASE MAP

```text
xp.py → xp.db
economy.py → economy.db
shop.py → economy.db
settings.py → settings.db
moderation.py → moderation.db
tickets.py → tickets.db
quests.py → quests.db
achievements.py → achievements.db
profile_customization.py → profile_customization.db
social.py → social.db
activities.py → activities.db
voice_stats.py → Insane.sqlite3
voice_rooms.py → configured persistence
```

Runtime databases are real state and must never be reset.

## 7. MASTER SYSTEM STATUS

| System | Implementation | Runtime | QA |
|---|---|---|---|
| Configuration / TEST-MAIN | DONE | PARTIAL | PENDING |
| COG loading / startup | DONE | HISTORICALLY VERIFIED | PENDING |
| Owner/admin | DONE | PARTIAL | PENDING |
| Server Manager | DONE | PARTIAL | PENDING |
| Rebuild | DONE | PARTIAL | PENDING |
| Verification | DONE | LIVE VERIFIED | PENDING |
| Moderation | DONE | PARTIAL | PENDING |
| Tickets | DONE | PARTIAL | PENDING |
| Logging | DONE | PARTIAL | PENDING |
| Voice statistics | DONE | PARTIAL | PENDING |
| Voice rooms | DONE | PARTIAL | PENDING |
| XP / Levels | DONE | PARTIAL | PENDING |
| Economy / Daily | DONE | PARTIAL | PENDING |
| Shop | DONE | TESTED | PENDING REGRESSION |
| Quests | DONE | NOT STARTED | PENDING |
| Achievements | DONE | NOT STARTED | PENDING |
| Profile Card | DONE | NOT STARTED | PENDING |
| Profile customization | DONE | NOT STARTED | PENDING |
| Mini-games | DONE | NOT TESTED | PENDING AFTER IMPLEMENTATION |
| Social / Friends / Romantic | DONE | NOT TESTED | PENDING AFTER IMPLEMENTATION |
| Discord Activities | SNAKE DETERMINISTIC REPLAY + SESSION/INSTANCE/GUILD BOUNDARY | NOT TESTED | PENDING REAL ACTIVITY BOUNDARY |
| PvP | REMOVED | — | — |
| Collecting | REMOVED FOR NOW | — | — |

## 8. XP / LEVELS

Implemented in `cogs/xp.py` + `databases/xp.py`: persistent guild/user XP, message XP/cooldown, message count, counted voice XP, AFK exclusion, levels, `/level`, `/xp_ranking`, level-up DM, voice-session recovery, message economy reward and profile integration.

Defaults: message XP 15–25; message cooldown 60s; voice 5/min; level threshold `100 * level²`; message economy reward 2.

`databases/xp.py` has `add_xp(guild_id, user_id, amount, reward_id=None)`. When `reward_id` is supplied, a persistent reward ledger prevents duplicate trusted Activity XP rewards across retries. Existing callers without `reward_id` retain original behavior.

## 9. ECONOMY / DAILY

Implemented `/balance`, `/daily`, `/pay`, `/rich`; persistent coins and rare currency, message rewards, daily, transfers, ranking, settings and Admin Panel adjustment.

Rare currency has persistence but no complete earning/spending loop yet.

`economy_rewards` provides idempotent trusted reward application through `add_reward_balance()`.

## 10. SHOP

Implemented `/shop` and `/buy`. Validates item/role/duplicate, charges economy, assigns role, refunds assignment failure and emits `shop_purchase` for achievements.

Runtime scenarios were tested 2026-08-31; regression QA remains pending.

## 11. QUESTS

Daily quests:

```text
messages_10 → 10 messages → 50 coins
voice_30 → 30 counted voice minutes → 100 coins
voice_sessions_3 → 3 counted voice joins → 75 coins
```

Persistent per guild/user/date; UTC date; capped progress; one claim; bots/webhooks excluded; AFK excluded; voice recovery.

Known integration risk: quest completion and economy reward are separate persistence operations.

## 12. ACHIEVEMENTS

Implemented:

```text
messages_1000
voice_10h
rich_10000
shop_purchase
active_7_days
```

Reuses XP, VoiceStats and Economy sources. Shop purchase consumes successful purchase event.

## 13. PROFILE

`/profile` generates a 1000×460 PNG via Pillow with avatar, display name, level/XP, total XP, coins/rare currency, message count, voice XP, achievement count and bio.

`/profile_customize`: background color, accent color, bio, reset. Guild/user scoped persistence; colors normalized; bio max 70 chars.

QA candidates: long names and Unicode/Cyrillic fallback.

## 14. VOICE

VoiceStats tracks persistent total/channel seconds and active sessions; AFK/bots excluded; restart recovery, channel moves and `on_ready` reconciliation.

Voice rooms provide private/user-created rooms, controls, access/co-owner management, persistence and cleanup. These systems remain separate.

## 15. VERIFICATION / MODERATION / TICKETS

Verification: arithmetic panel, role transition and owner synchronization. TEST role-create condition remains audit candidate.

Moderation: `/warn`, `/timeout`, `/kick`, `/ban`, `/unban`, `/history`; persistent actions, settings, hierarchy checks, history, logging, modal actions and interaction hardening.

Tickets: panel → modal → private thread → support → close confirmation → transcript → archive/lock; persistent state and ready recovery.

Historical fixes include role hierarchy, ticket parent privacy, ticket interaction timeout, moderation timeout, moderation modal COG reuse and verification persistent view.

## 16. LOGGING / SERVER MANAGER / REBUILD

Logging groups: chat / guild / moderation / setup / system / voice. Runtime mapping uses `.logging_channels.json` with `server_logs` compatibility.

Full rebuild on 2026-09-01 completed without the previous Unknown Channel / 404 logging errors.

Server Manager handles active guild targeting, managed permissions, synchronization, `/sync_server`, `/channel_create`.

Rebuild is owner-only, TEST-restricted, confirmed, mapping-aware and database-preserving.

## 17. MINI-GAMES — IMPLEMENTED

Files: `cogs/minigames.py`, `databases/xp.py`, `config.py`.

Command: `/minigame` with `Математика`, `Реакция`, `Память`.

Rules: one active game per guild/user; 30-second cooldown after success/failure; only initiating user can operate buttons; expired games give no reward; XP-disabled servers cannot start; rewards use existing XP/economy; no gambling/betting; success gives +15 XP and +25 coins when economy enabled; memory sequence hides after 3 seconds; wrong answer ends without reward.

No runtime QA yet. Known audit candidates: reward text when economy is disabled, timeout cooldown semantics, `_reward` dependency on XP COG and concurrency/restart behavior.

## 18. SOCIAL / FRIENDS / ROMANTIC — IMPLEMENTED

Files: `databases/social.py`, `cogs/social.py`, `config.py`.

Persistent `social.db` stores friend requests, normalized friendships, romantic requests and normalized romantic relationships.

Commands:

```text
/friends
/friends add <member>
/friends accept <member>
/friends remove <member>

/relationship
/relationship propose <member>
/relationship accept <member>
/relationship end <member>
```

Rules: self-add/proposal rejected; friend request requires acceptance; duplicate/reverse requests rejected; romantic proposal requires friendship; romance requires mutual acceptance; ending romance preserves friendship; all state is guild-scoped and persistent; pairs are normalized.

No XP/economy rewards are attached yet.

## 19. DISCORD ACTIVITIES — CURRENT IMPLEMENTATION

### 19.1 Activity roadmap

Initial activities:

```text
Snake
Sudoku
Wordle
```

Future activities:

```text
2048
Minesweeper
Tetris
Flappy Bird
Connect Four
Chess
Checkers
```

Activities must be real Discord Activities, not slash-command simulations.

### 19.2 Activity persistence / trusted reward foundation

`databases/activities.py` contains a persistent idempotent result ledger:

```text
result_id
activity_key
guild_id
user_id
xp_reward
coin_reward
received_at
```

`result_id` is the primary key. Exposed operations:

```text
has_result(result_id)
record_result(result_id, activity_key, guild_id, user_id, xp_reward, coin_reward)
get_result(result_id)
get_user_results(guild_id, user_id, activity_key=None, limit=100)
```

`utils/activity_registry.py` contains the Activity definition registry. `utils/activity_rewards.py` contains the trusted-result reward application layer.

The trusted reward layer:
- validates trusted Activity result data;
- persists results idempotently;
- verifies reused result IDs have identical payloads;
- applies XP and Economy through persistent reward ledgers;
- can recover from partial application on retry;
- does not claim cross-database atomicity.

**Important:** `activity_rewards.py` must only receive already-trusted results. External identity/session verification and game anti-cheat validation happen before it.

### 19.3 Activity client

`activities/client/package.json` uses the official `@discord/embedded-app-sdk` dependency and Vite build scripts.

`activities/client/index.html` is the Vite entry page.

`activities/client/vite.config.js` proxies `/api/*` to `http://127.0.0.1:8080` for local development.

`activities/client/src/main.js`:

1. Reads `VITE_DISCORD_CLIENT_ID`.
2. Creates `DiscordSDK`.
3. Waits for `discordSdk.ready()`.
4. Calls SDK `authorize` with `identify` scope.
5. Sends the one-time code plus SDK `instanceId`, `guildId`, `channelId` to `/api/discord/token`.
6. Receives the backend-issued Discord access token.
7. Calls `discordSdk.commands.authenticate({ access_token })` once.
8. Loads `/api/discord/session` with credentials.
9. Verifies user, Activity instance, guild and channel identity against SDK values.
10. Requests `/api/activities/snake/start` for a server-issued Snake game.
11. Passes the server-issued `seed`, `game_id` and `result_id` to the Snake client.
12. Sends Snake finish data to `/api/activities/snake/result`.

The browser never receives the Discord application client secret.

### 19.4 Activity OAuth/session backend

`activities/server.py` provides a dependency-free `ThreadingHTTPServer` backend.

After exchanging the Discord authorization code, it:
- calls Discord `/users/@me`;
- obtains the authenticated Discord user ID and username from Discord;
- requires Activity `instance_id`, `guild_id`, `channel_id`;
- creates a cryptographically random opaque server-side session ID;
- stores user identity + Activity instance/guild/channel + one-hour expiry;
- sends the session as an `HttpOnly` cookie scoped to `/api/discord`;
- exposes `GET /api/discord/session`;
- rejects missing/unknown/expired sessions with 401;
- does not store the Discord access token in the session;
- keeps sessions in memory for the current implementation.

Environment:

```text
DISCORD_ACTIVITY_HOST=127.0.0.1
DISCORD_ACTIVITY_PORT=8080
DISCORD_ACTIVITY_CLIENT_ID=<server-side Discord application client ID>
DISCORD_ACTIVITY_CLIENT_SECRET=<server-side Discord application client secret>
```

`DISCORD_ACTIVITY_CLIENT_SECRET` must remain server-side and must never be placed in Vite client environment variables.

### 19.5 Snake local engine — deterministic replay implemented

`activities/client/src/snake.js` remains a local real-time Snake engine, but it now has a deterministic replay boundary.

Game rules remain:
- 20×20 board;
- initial snake `(10,10),(9,10),(8,10)`;
- initial direction right;
- fixed 120ms tick;
- wall/self collision;
- food only on free cells;
- score increments on food;
- win when the board is filled.

Changes now implemented:
- food generation uses a deterministic `xorshift32` PRNG;
- server-issued seed is used for the game;
- game ID and result ID are bound to the current server-issued game;
- completed tick count is recorded;
- accepted direction inputs are recorded as `{tick, direction}` events;
- finish callback returns reason, score, tick count, seed, game ID, result ID and full input trace;
- restart requests a fresh server-issued game instead of inventing a result ID client-side.

The client-side random seed fallback remains only for a raw local `SnakeGame.reset()` call; the actual Activity flow always supplies the server-issued seed.

### 19.6 Snake authoritative replay validation — IMPLEMENTED

`POST /api/activities/snake/start` now:
- requires an authenticated Activity session;
- generates a cryptographically random 32-bit seed;
- generates server-side `game_id` and `result_id`;
- stores the game bound to user, Activity instance, guild and channel;
- applies a 15-minute game TTL;
- returns `game_id`, `result_id`, `seed`.

`POST /api/activities/snake/result` now requires:

```text
game_id
result_id
activity_key
score
reason
tick_count
seed
inputs
instance_id
guild_id
channel_id
```

Validation includes:
- authenticated session required;
- result/activity identity validation;
- instance/guild/channel must match the authenticated session;
- game must exist and not be expired;
- game must belong to the same user and Activity context;
- result ID must equal the server-issued result ID;
- input trace and tick limits are enforced;
- direction names must be valid;
- illegal reverse-direction transitions are rejected;
- the backend replays Snake from the server-issued seed using the same deterministic xorshift32 PRNG and free-cell ordering as the client;
- wall collisions and self collisions are replayed;
- food consumption and score are replayed;
- final tick count, score and finish reason must exactly match the authoritative replay;
- accepted games are consumed so the same game cannot be submitted twice.

Current limits:

```text
SNAKE_MAX_SCORE = 397
SNAKE_MAX_INPUTS = 20000
SNAKE_MAX_TICKS = 100000
SNAKE_GAME_TTL = 900 seconds
```

The result is currently stored in the backend's in-memory `activity_results` map. **Rewards are intentionally not wired here yet.** This is the security/validation boundary that must precede `activity_rewards.py`.

### 19.7 Security status

Current chain:

```text
Discord SDK
  ↓
authorize
  ↓
server OAuth exchange
  ↓
Discord /users/@me identity
  ↓
HttpOnly server session
  ↓
instance_id + guild_id + channel_id binding
  ↓
server-issued Snake seed/game_id/result_id
  ↓
deterministic client replay data
  ↓
authoritative server replay
  ↓
validated trusted Activity result
```

This is substantially stronger than the previous score-only endpoint: a browser can no longer simply submit an arbitrary plausible score and have it accepted without a matching server-issued game and replay.

Still not implemented:
- independent Discord-side verification of the Activity instance ID beyond the authenticated Activity context;
- persistent storage of active Activity game sessions;
- Activity result reward wiring;
- Sudoku implementation;
- Wordle implementation;
- full real Discord Activity boundary/runtime QA.

## 20. RECENT ACTIVITY CHECKPOINTS

```text
1fd67f7fbb319a61b691022c6e7c1801c57e5a9c → Activity result ledger
5946224802115e94940c5f2ab87f7bc6729731ab → Activity roadmap expanded
9e584c6d80add5497c118db0aec0d5a23b0bc2da → Activity registry
0f1f501f4cab242453f88fd390d74312b36cfade → trusted Activity reward pipeline
082cab6e5fd383d4de31c34d1773cafd50cf0aa3 → XP reward idempotency
3348a0793009dcae7d9cf9fdb120a2ac897ec4f2 → Economy reward idempotency
86196954830ed8f1b2eaec3d584753fedb903c3d → Activity reward pipeline wiring/retry recovery
9680d41c2e7a64df751f13d7430d7232a1c4b12a → Activity client package foundation
66c87d300dbb83b8c2d0caa743f4839de65ee8a5 → Activity client authentication foundation
ac68eee9d9ef9f3c99889aa8b31931ea1a01c688 → Activity Vite dev proxy
4632635f78b56cd6b66cb2f1a1c1d7975131e717 → Activity backend lifecycle COG foundation
c38fff4767db250725d497398d4f84319cf1eac9 → Activity lifecycle/config integration
46e5cac3d285483a24834ee347d7b1231d4d27c6 → Activity COG load integration
5b283447339a59d7ce4c81b916f517d94abe16d5 → Activity session groundwork
ff7790043a234c97654da9aeb6d1c2e1ced6b2d3 → Activity client session preparation
71a0076ab26869e5f0e7dcb334f7fe0441bab4a8 → Activity client authentication flow correction
c336d8bf63438d1f64420328fe01ef8bb59638ee → server-side authenticated Activity session
844cdf33a6edc9c6bf0ebe95c13ca5da65bbbc0d6 → Activity lifecycle checkpoint
f174c78fe5d31ac35bcba4381511f11b5b1b56b3 → integrate Snake UI into Activity client
668f85df25022e560cf49451c202d1e4c4d69c3f → Snake Activity interface styling
e8adfabd1803b9890452c88e328dac5f97f82c2c → Activity instance/guild binding in client
a0e29816a2e6effd88d5878a78ca36def1af15b8 → Activity instance/guild binding in backend
3c62e09eeb98f06ad7af4d3d6e5222d06a508d54 → Snake client completion/result callback
b27608d81ed8bdbf33eb188131722906429700b7 → Snake result submission from Activity client
00e58c1e267e0da6997c017059451df9130232a2 → Snake backend result validation endpoint
4a5d6e3bc569c67bb75109a8a9b53afd7f2315a0 → PROJECT_STATE update after Snake validation foundation
640ac0b3306271b23f5dbf0c8c4ff5866322b518 → deterministic Snake engine and input trace
68029850727f69f42514bd4de061c91dccf5779d → authoritative Snake replay validation boundary
b9d92a282c455f0ed85e028d0bfe06f178d26da8 → server-issued Snake result ID binding
0b19754e43544b9fe0d5b54ff5e404d3ad838da2 → Activity client final server-issued game binding
```

## 21. CURRENT IMPLEMENTATION ORDER

Do not start broad QA yet. Continue implementation in this order:

1. **Snake → trusted reward pipeline**: after authoritative replay validation, convert only validated results into `TrustedActivityResult` and apply configured XP/coins idempotently.
2. **Sudoku UI/game**.
3. **Sudoku authoritative backend validation + rewards**.
4. **Wordle UI/game**.
5. **Wordle authoritative backend validation + rewards**.
6. Remaining planned Activities.
7. Complete real Discord Activity boundary/runtime checks.
8. Full sequential QA of all systems.
9. Integration regression and technical cleanup.

## 22. IMPORTANT CURRENT NOTES

- No Activity rewards should be granted from raw client-submitted Snake scores.
- `activity_rewards.py` is deliberately downstream of the authoritative validation boundary.
- Do not reset or recreate existing runtime databases while continuing Activity work.
- Do not turn Activities into slash-command simulations.
- Do not call current Activity implementation `QA PASSED` until it has been exercised in the real Discord Activity environment.
- Current implementation has not been runtime-tested in the real Discord Activity boundary.
