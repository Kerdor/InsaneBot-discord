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

### User development priority

1. Implement all agreed/planned systems first.
2. Do not start full system-by-system QA until planned implementation is complete.
3. Then perform integration cleanup, sequential QA, regression and technical cleanup.
4. Update `PROJECT_STATE.md` after every implementation/QA action.

## 2. PRODUCT CONCEPT

InsaneBot is a Discord **community/progression bot**, not a traditional RPG.

Core loop:

```text
Discord activity → XP / Economy → Levels / Rankings / Quests / Achievements / Profile
messages / voice / daily / quests / shop / mini-games / future Activities
```

Do not add without explicit approval: talismans, combat items, loot boxes, RPG equipment/inventory, meaningless RPG stats, combat systems without community purpose, PvP, collecting.

Planned directions: mini-games, real Discord Activities, social interactions, Friends, Romantic relationships, richer profile cosmetics.

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
| Discord Activities | BACKEND LIFECYCLE FOUNDATION | NOT TESTED | PENDING REAL BOUNDARY |
| PvP | REMOVED | — | — |
| Collecting | REMOVED FOR NOW | — | — |

## 8. XP / LEVELS

Implemented in `cogs/xp.py` + `databases/xp.py`: persistent guild/user XP, message XP/cooldown, message count, counted voice XP, AFK exclusion, levels, `/level`, `/xp_ranking`, level-up DM, voice-session recovery, message economy reward, profile integration.

Defaults: message XP 15–25; message cooldown 60s; voice 5/min; level threshold `100 * level²`; message economy reward 2.

`databases/xp.py` has `add_xp(guild_id, user_id, amount, reward_id=None)` for generic progression XP. A supplied reward ID gives persistent idempotency for trusted Activity rewards.

## 9. ECONOMY / DAILY

Implemented `/balance`, `/daily`, `/pay`, `/rich`; persistent coins and rare currency, message rewards, daily, transfers, ranking, settings and Admin Panel adjustment.

`economy_rewards` provides idempotent trusted reward application through `add_reward_balance()`. Rare currency has persistence but no complete earning/spending loop yet.

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

Persistent per guild/user/date; UTC date; capped progress; one claim; bots/webhooks excluded; AFK excluded; voice recovery. Known integration risk: quest completion and economy reward are separate persistence operations.

## 12. ACHIEVEMENTS

Implemented: `messages_1000`, `voice_10h`, `rich_10000`, `shop_purchase`, `active_7_days`. Reuses XP, VoiceStats and Economy sources.

## 13. PROFILE

`/profile` generates a 1000×460 PNG via Pillow with avatar, display name, level/XP, total XP, coins/rare currency, message count, voice XP, achievement count and bio.

`/profile_customize`: background color, accent color, bio, reset. Guild/user scoped persistence; colors normalized; bio max 70 chars. Long names and Unicode/Cyrillic remain QA candidates.

## 14. VOICE

VoiceStats tracks persistent total/channel seconds and active sessions; AFK/bots excluded; restart recovery, channel moves and `on_ready` reconciliation.

Voice rooms provide private/user-created rooms, controls, access/co-owner management, persistence and cleanup.

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

No XP/economy rewards are attached yet. No runtime QA.

## 19. DISCORD ACTIVITIES

Initial Activity release is intentionally limited to:

```text
Snake
Sudoku
Wordle
```

Future backlog: 2048, Minesweeper/Saper, Tetris, Flappy Bird, Connect Four, Chess, Checkers.

### Persistent result ledger

`databases/activities.py` stores:

```text
result_id
activity_key
guild_id
user_id
xp_reward
coin_reward
received_at
```

`result_id` is the primary key and duplicate results are ignored. API helpers:
`has_result`, `record_result`, `get_result`, `get_user_results`.

### Activity registry

`utils/activity_registry.py` defines `ActivityDefinition` and the initial/future activity catalog. Initial keys are `snake`, `sudoku`, `wordle`.

### Trusted reward pipeline

`utils/activity_rewards.py` accepts only trusted `TrustedActivityResult` data. It validates the result, persists it idempotently, verifies reused result IDs have identical payloads, and applies XP/Economy using the same result ID as reward ID.

The pipeline safely retries after partial failure. Absolute atomicity across Activity, XP and Economy SQLite databases is not claimed.

### Client package

`activities/client/package.json` uses `@discord/embedded-app-sdk` and Vite.

`activities/client/index.html` is the Vite entry page.

`activities/client/src/main.js`:

1. reads `VITE_DISCORD_CLIENT_ID`;
2. creates `DiscordSDK`;
3. waits for `ready()`;
4. calls `authorize()` with `identify`;
5. posts the one-time code to `/api/discord/token`;
6. receives the backend access token;
7. calls `authenticate()`;
8. displays connected/failed status.

The browser never receives the Discord client secret.

### OAuth backend

`activities/server.py` provides a dependency-free `ThreadingHTTPServer` for `POST /api/discord/token`.

It requires server-side `DISCORD_ACTIVITY_CLIENT_ID` and `DISCORD_ACTIVITY_CLIENT_SECRET`, validates the request, exchanges the authorization code with Discord, returns only the access token, disables caching, and never logs the code/token.

### Activity backend lifecycle — IMPLEMENTED FOUNDATION

Commit `4632635f78b56cd6b66cb2f1a1c1d7975131e717` added `cogs/activity_server.py`.

The COG creates the Activity HTTP server and runs `serve_forever()` in a daemon thread. `cog_unload()` shuts it down cleanly.

Commit `c38fff4767db250725d497398d4f84319cf1eac9` switched host/port handling to environment variables with safe defaults:

```text
DISCORD_ACTIVITY_HOST=127.0.0.1
DISCORD_ACTIVITY_PORT=8080
```

The port is validated to `1..65535`.

Commit `46e5cac3d285483a24834ee347d7b1231d4d27c6` added `cogs.activity_server` to the configured COG load order and exposed the same host/port configuration through `BotConfig.ACTIVITY_HOST` / `BotConfig.ACTIVITY_PORT`.

This means the backend is now started by the same application startup path as the Discord bot. **Runtime verification has not been performed yet.**

### Activity Vite development proxy

`activities/client/vite.config.js` proxies `/api/*` to `http://127.0.0.1:8080` during Vite development.

### Final security boundary

```text
Discord Activity iframe
        ↓
Embedded App SDK authorize()
        ↓
one-time authorization code
        ↓
InsaneBot backend /api/discord/token
        ↓
Discord OAuth token exchange using server-side secret
        ↓
SDK authenticate()
        ↓
verified Activity/session identity
        ↓
validated game result
        ↓
utils/activity_rewards.py
        ↓
idempotent XP / Economy / Activity persistence
```

The final game-result endpoint must never trust arbitrary browser-supplied `user_id`, `guild_id`, reward amounts or completion claims. Backend identity/session binding, guild verification and game-specific anti-cheat validation are still required.

## 20. CURRENT ACTIVITY NEXT STEPS

1. Runtime-check the new Activity backend lifecycle only after implementation phase reaches a suitable checkpoint.
2. Implement authenticated Activity session handling and identity/guild binding.
3. Implement a secure game-result boundary that validates game-specific completion before `activity_rewards.py`.
4. Implement the first actual Activity UI: **Snake**.
5. Add Sudoku and Wordle after the Activity boundary is stable.
6. Configure Discord Developer Portal Activity URL mapping and production networking later.

Do not claim an Activity is a real Discord Activity until the Discord Embedded App SDK boundary and Developer Portal mapping are actually functional.

## 21. KNOWN AUDIT / IMPLEMENTATION ITEMS

High priority:

- quest completion/reward atomicity;
- moderation punishment vs logging failure;
- TEST verification role-create condition;
- profile card long names and Unicode/Cyrillic fallback;
- Activity authenticated identity/guild verification;
- Activity game-result validation and anti-cheat boundary;
- Activity reward atomicity across separate SQLite databases.

Additional:

- exact `active_7_days` semantics;
- voice achievement timing;
- legacy `get_roles.py`;
- disabled `reaction_logs.py`;
- guild-only command behavior;
- permission/role hierarchy edges;
- interaction acknowledgement;
- duplicate event handling;
- mini-game reward integration/concurrency;
- social command and relationship concurrency/edge cases;
- Activity registry validation;
- Activity URL mapping / Developer Portal configuration;
- authenticated Activity session handling;
- production networking/tunnel configuration.

## 22. RECENT IMPLEMENTATION CHECKPOINTS

```text
27c49fd4c0ff0cf42c83d0e3851ed1eec1698d70 → persistent social database
e90ab1944b3d93ca091b7ac2ccac964df9d532d4 → social commands/COG
89b0027ee6f19570393cecf012837a70bb11f72 → load social COG
1fd67f7fbb319a61b691022c6e7c1801c57e5a9c → Activity result ledger
5946224802115e94940c5f2ab87f7bc6729731ab → Activity roadmap expanded
9e584c6d80add5497c118db0aec0d5a23b0bc2da → Activity registry
a5d8bf9c138f5cb28e231b5d565572a479e9ca3d → Activity result lookup/history
0f1f501f4cab242453f88fd390d74312b36cfade → trusted Activity reward pipeline
082cab6e5fd383d4de31c34d1773cafd50cf0aa3 → XP reward idempotency
3348a0793009dcae7d9cf9fdb120a2ac897ec4f2 → Economy reward idempotency
86196954830ed8f1b2eaec3d584753fedb903c3d → Activity reward retry recovery
9680d41c2e7a64df751f13d7430d7232a1c4b12a → Activity client package foundation
66c87d300dbb83b8c2d0caa743f4839de65ee8a5 → Activity client authentication foundation
ac68eee9d9ef9f3c99889aa8b31931ea1a01c688 → Activity Vite development proxy
e493e67a8a8c36ac1be51b3bed6a70482a12a48a → Activity backend package marker
49d9129702ff6269a19079b989868c705be0ff44 → previous PROJECT_STATE checkpoint
4632635f78b56cd6b66cb2f1a1c1d7975131e717 → Activity backend lifecycle COG
c38fff4767db250725d497398d4f84319cf1eac9 → Activity backend environment host/port handling
46e5cac3d285483a24834ee347d7b1231d4d27c6 → Activity COG/config load integration
CURRENT STATE UPDATE → Activity backend lifecycle integration checkpoint
```

## 23. DEVELOPMENT STOP POINT

Current implementation stop point is **after wiring the Activity OAuth backend into the InsaneBot startup path**.

The next implementation target is the **authenticated Activity session/result boundary**, then the first real Activity UI (**Snake**).

No Activity runtime QA has been claimed yet.
