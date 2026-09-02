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

TEST guild: `Insane TEST` / `519209364280573954`.

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
| COG loading / startup | DONE | PARTIAL | PENDING |
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
| Discord Activities | SNAKE + AUTHORITATIVE REPLAY + TRUSTED REWARDS | NOT TESTED | PENDING REAL ACTIVITY BOUNDARY |
| PvP | REMOVED | — | — |
| Collecting | REMOVED FOR NOW | — | — |

## 8. XP / LEVELS

Implemented in `cogs/xp.py` + `databases/xp.py`: persistent guild/user XP, message XP/cooldown, message count, counted voice XP, AFK exclusion, levels, `/level`, `/xp_ranking`, level-up DM, voice-session recovery, message economy reward and profile integration.

Defaults: message XP 15–25; message cooldown 60s; voice 5/min; level threshold `100 * level²`; message economy reward 2.

`databases/xp.py` supports `add_xp(guild_id, user_id, amount, reward_id=None)`. Supplying a reward ID makes trusted Activity XP rewards idempotent.

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

Implemented: `messages_1000`, `voice_10h`, `rich_10000`, `shop_purchase`, `active_7_days`.

## 13. PROFILE

`/profile` generates a 1000×460 PNG via Pillow with avatar, display name, level/XP, total XP, coins/rare currency, message count, voice XP, achievement count and bio.

`/profile_customize`: background color, accent color, bio, reset. Guild/user scoped persistence; colors normalized; bio max 70 chars.

QA candidates: long names and Unicode/Cyrillic fallback.

## 14. VOICE

VoiceStats tracks persistent total/channel seconds and active sessions; AFK/bots excluded; restart recovery, channel moves and `on_ready` reconciliation.

Voice rooms provide private/user-created rooms, controls, access/co-owner management, persistence and cleanup.

## 15. VERIFICATION / MODERATION / TICKETS

Verification: arithmetic panel, role transition and owner synchronization.

Moderation: `/warn`, `/timeout`, `/kick`, `/ban`, `/unban`, `/history`; persistent actions, settings, hierarchy checks, history, logging, modal actions and interaction hardening.

Tickets: panel → modal → private thread → support → close confirmation → transcript → archive/lock; persistent state and ready recovery.

## 16. LOGGING / SERVER MANAGER / REBUILD

Logging groups: chat / guild / moderation / setup / system / voice. Runtime mapping uses `.logging_channels.json` with `server_logs` compatibility.

Full rebuild on 2026-09-01 completed without the previous Unknown Channel / 404 logging errors.

Server Manager handles active guild targeting, managed permissions, synchronization, `/sync_server`, `/channel_create`.

Rebuild is owner-only, TEST-restricted, confirmed, mapping-aware and database-preserving.

## 17. MINI-GAMES

`cogs/minigames.py` provides `/minigame` with `Математика`, `Реакция`, `Память`.

Rules: one active game per guild/user; 30-second cooldown after success/failure; only initiating user operates buttons; expired games give no reward; XP-disabled servers cannot start; existing XP/economy rewards; no gambling/betting; success +15 XP and +25 coins when economy enabled; memory hides after 3 seconds; wrong answer gives no reward.

No runtime QA yet.

## 18. SOCIAL / FRIENDS / ROMANTIC

`databases/social.py` + `cogs/social.py` provide persistent guild-scoped friend and romantic relationships.

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

Self/duplicate/reverse checks; romance requires friendship and mutual acceptance; ending romance preserves friendship; normalized pairs. No rewards attached yet.

## 19. DISCORD ACTIVITIES

### Roadmap

Initial: Snake, Sudoku, Wordle. Future: 2048, Minesweeper, Tetris, Flappy Bird, Connect Four, Chess, Checkers.

Activities must be real Discord Activities, not slash-command simulations.

### Persistence / rewards

`databases/activities.py` stores an idempotent result ledger keyed by `result_id`, with activity key, guild/user IDs, XP/coin rewards and timestamp.

`utils/activity_registry.py` contains Activity definitions.

`utils/activity_rewards.py` exposes `TrustedActivityResult` and `apply_trusted_result()`. It validates the trusted payload, persists the result idempotently, and applies XP/economy rewards using persistent reward IDs. It can recover after a partial cross-database application.

The reward layer must only receive already-trusted results.

### Client

`activities/client/src/main.js` authenticates with the Discord Embedded App SDK, sends the one-time OAuth code to the backend, loads the server session, verifies user/instance/guild/channel identity, starts a server-issued Snake game, and submits the completed replay.

`activities/client/src/snake.js` implements a real local Snake engine: 20×20 board, 120ms ticks, deterministic xorshift32 food generation, server-issued seed/game/result IDs, input trace, score and finish reason.

Restart requests a fresh server-issued game.

### OAuth/session backend

`activities/server.py` provides a dependency-free threaded backend.

OAuth flow:

```text
Discord Activity SDK authorize
→ backend exchanges one-time code
→ Discord /users/@me
→ opaque HttpOnly server session
→ session bound to instance_id + guild_id + channel_id
```

Environment:

```text
DISCORD_ACTIVITY_HOST=127.0.0.1
DISCORD_ACTIVITY_PORT=8080
DISCORD_ACTIVITY_CLIENT_ID=<server-side Discord application client ID>
DISCORD_ACTIVITY_CLIENT_SECRET=<server-side Discord application client secret>
```

Client secret is never exposed to the browser. Sessions are currently in memory and expire after one hour.

### Snake authoritative validation

`POST /api/activities/snake/start` requires the authenticated session and creates a server-issued cryptographic 32-bit seed, `game_id`, and `result_id`. The game is bound to user, instance, guild and channel and expires after 15 minutes.

`POST /api/activities/snake/result` requires the matching game/result/seed/context and a complete input trace. The backend replays Snake with the same deterministic PRNG and board rules and verifies legal directions, ticks, collisions, food, score and finish reason. The accepted game is consumed so it cannot be submitted twice.

Limits:

```text
SNAKE_MAX_SCORE = 397
SNAKE_MAX_INPUTS = 20000
SNAKE_MAX_TICKS = 100000
SNAKE_GAME_TTL = 900
```

### Snake trusted reward integration — IMPLEMENTED

Only after replay validation succeeds, `activities/server.py` creates a `TrustedActivityResult` bound to the authenticated user/guild and server-issued result ID. Reward amounts are calculated on the backend as:

```text
XP = score * 15
coins = score * 25
```

The result is passed to `apply_trusted_result()` from `utils/activity_rewards.py`.

Reward chain:

```text
Discord identity/session
→ server-issued game
→ deterministic replay validation
→ TrustedActivityResult
→ persistent idempotent Activity result
→ persistent idempotent XP
→ persistent idempotent coins
```

Reward amounts are never accepted from the browser. The response includes `xp_reward`, `coin_reward`, and `reward_applied`.

**Implementation is complete; runtime QA is still pending.**

### Activity startup fix — IMPLEMENTED 2026-09-02

Runtime startup exposed a COG registration error in `cogs.activity_server`: `ActivityServerCog` was a plain class, while `disnake` requires objects passed to `bot.add_cog()` to derive from `commands.Cog`.

The lifecycle COG was corrected to inherit from `commands.Cog` and import `commands` from `disnake.ext`. No Activity backend logic, routes, validation, reward logic, configuration or database behavior was changed.

The reported startup failure was:

```text
TypeError: cogs must derive from Cog
```

Commit:

```text
e8604abdfe11fcd8d2b935640989e0e0a74596ca → Fix ActivityServerCog disnake Cog inheritance
```

Runtime verification after this fix is still pending.

## 20. SECURITY STATUS

Current Activity security boundary prevents a client from simply submitting an arbitrary score. A result must correspond to a server-issued game, seed and result ID, authenticated user/context, and a valid deterministic replay.

Still not implemented:
- persistent active-game storage across backend restarts;
- independent external verification of Activity instance state beyond the authenticated SDK/session context;
- Sudoku;
- Wordle;
- full real Discord Activity runtime QA.

## 21. RECENT ACTIVITY CHECKPOINTS

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
4a5d6e3bc569c67bb75109a8a9b53afd7f2315a0 → PROJECT_STATE after Snake validation foundation
66564974132545bccff6b50c585984012d8e6642 → Snake seed binding hardening
7e5e1302287243bdaf08ba5573b49f5b79ab8e48 → Snake trusted reward integration
e8604abdfe11fcd8d2b935640989e0e0a74596ca → ActivityServerCog disnake Cog inheritance
```

## 22. CURRENT IMPLEMENTATION ORDER

1. Runtime QA of Snake end-to-end, including reward persistence and duplicate submission.
2. Sudoku UI/game.
3. Sudoku authoritative backend validation + rewards.
4. Wordle UI/game.
5. Wordle authoritative backend validation + rewards.
6. Remaining planned Activities.
7. Complete real Discord Activity boundary checks.
8. Full sequential QA of all systems.
9. Integration regression and technical cleanup.

## 23. IMPORTANT CURRENT NOTES

- Raw client-submitted Snake scores never directly grant rewards.
- `activity_rewards.py` is downstream of authoritative validation.
- XP and Economy reward IDs use the trusted `result_id`, so retrying the same validated result does not intentionally duplicate rewards.
- Activity games/results are currently in memory; a backend restart invalidates active games.
- Runtime databases must never be reset.
- Activities must remain real Discord Activities.
- Current Activity implementation is **NOT QA PASSED** until exercised in the real Discord Activity environment.
- The 2026-09-02 startup failure was caused by `ActivityServerCog` not inheriting from `commands.Cog`; this has been fixed in commit `e8604abdfe11fcd8d2b935640989e0e0a74596ca`.

## 24. ACTIVITY LOCAL LAUNCH CHECKPOINT — 2026-09-02

Local Activity client setup completed.

Client:
- Node.js installed and available:
  - Node `v24.20.0`
  - npm `11.19.0`
- `npm install` completed successfully.
- `npm run build` completed successfully with Vite `8.2.2`.
- Production build generated in `activities/client/dist/`.
- Vite development server starts successfully at:
  `http://localhost:5173/`

Cloudflare Tunnel:
- `cloudflared` installed for Windows x64.
- Version: `2026.8.3`.
- Quick Tunnel successfully established:
  `https://downloads-graphical-james-sailing.trycloudflare.com`
- Tunnel successfully connects to local Activity client on port `5173`.
- QUIC connectivity and Cloudflare API pre-checks passed.
- Tunnel is currently a temporary Quick Tunnel and does not provide a stable production URL.

Discord Developer Portal:
- Activity URL Mapping configured and saved.
- Public Activity URL currently points through the Cloudflare Quick Tunnel.
- URL mapping changes confirmed saved.

Current local launch state:
```text
Discord bot             → running
Activity backend        → 127.0.0.1:8080
Vite client             → 127.0.0.1:5173
Cloudflare Tunnel       → public HTTPS → localhost:5173
Discord URL Mapping     → saved
```

Next step:
- Launch the Activity from Discord on the TEST server.
- Verify that the real Discord Activity opens correctly.
- Then perform runtime testing of SDK authentication → backend session → Snake start → gameplay → authoritative result submission → XP/coin reward.
- This is still `RUNTIME QA PENDING`.

The local Activity client, backend, tunnel and Discord URL Mapping are therefore considered configured for the next real Discord Activity runtime check, but **no successful real Activity launch has yet been recorded**.
