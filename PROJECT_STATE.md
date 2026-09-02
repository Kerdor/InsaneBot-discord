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
  server_manager.py verification.py moderation.py tickets.py xp.py economy.py shop.py quests.py achievements.py minigames.py social.py admin_panel.py
  user_cmd/create_voice.py
  logging/{chat_logs,guild_logs,moderation_logs,setup_logs,system_logs,voice_stats}.py
  logging/reaction_logs.py (disabled)
databases/
  xp.py economy.py shop.py quests.py achievements.py
  profile_customization.py moderation.py tickets.py voice_stats.py voice_rooms.py social.py activities.py
utils/profile_card.py activity_registry.py activity_rewards.py
activities/
  client/package.json
  client/index.html
  client/src/main.js
  server.py
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
| Discord Activities | FOUNDATION + CLIENT AUTH FOUNDATION | NOT TESTED | PENDING REAL BOUNDARY |
| PvP | REMOVED | — | — |
| Collecting | REMOVED FOR NOW | — | — |

## 8. XP / LEVELS

Implemented in `cogs/xp.py` + `databases/xp.py`: persistent guild/user XP, message XP/cooldown, message count, counted voice XP, AFK exclusion, levels, `/level`, `/xp_ranking`, level-up DM, voice-session recovery, message economy reward, profile integration.

Defaults: message XP 15–25; message cooldown 60s; voice 5/min; level threshold `100 * level²`; message economy reward 2.

`databases/xp.py` has `add_xp(guild_id, user_id, amount, reward_id=None)` for generic progression XP. When `reward_id` is supplied, a persistent reward ledger prevents duplicate trusted Activity XP rewards across retries. Existing callers without `reward_id` retain original behavior.

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

Persistent per guild/user/date; UTC date; capped progress; one claim; bots/webhooks excluded; AFK excluded; voice recovery. Known integration risk: quest completion and economy reward are separate persistence operations.

## 12. ACHIEVEMENTS

Implemented: `messages_1000`, `voice_10h`, `rich_10000`, `shop_purchase`, `active_7_days`.

Reuses XP, VoiceStats and Economy sources. Shop purchase consumes successful purchase event.

## 13. PROFILE

`/profile` generates a 1000×460 PNG via Pillow with avatar, display name, level/XP, total XP, coins/rare currency, message count, voice XP, achievement count and bio.

`/profile_customize`: background color, accent color, bio, reset. Guild/user scoped persistence; colors normalized; bio max 70 chars. Long names and Unicode/Cyrillic remain QA candidates.

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

Rules: one active game per guild/user; 30-second cooldown after success/failure; only initiating user can operate buttons; expired games give no reward; XP-disabled servers cannot start; rewards use existing XP/economy; no gambling/betting; success gives +15 XP and +25 coins when economy enabled; existing XP level calculation is reused; memory sequence hides after 3 seconds; wrong answer ends without reward.

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

## 19. DISCORD ACTIVITIES — FOUNDATION IMPLEMENTED

A persistent idempotent result ledger exists in `databases/activities.py`.

Stored fields:

```text
result_id
activity_key
guild_id
user_id
xp_reward
coin_reward
received_at
```

`result_id` is the primary key and duplicate results are ignored.

The Activity persistence layer exposes:

```text
has_result(result_id)
record_result(result_id, activity_key, guild_id, user_id, xp_reward, coin_reward)
get_result(result_id)
get_user_results(guild_id, user_id, activity_key=None, limit=100)
```

A static Activity registry exists in `utils/activity_registry.py`. Initial release: Snake, Sudoku, Wordle. Future list: 2048, Minesweeper, Tetris, Flappy Bird, Connect Four, Chess, Checkers.

A trusted-result application layer exists in `utils/activity_rewards.py`. It validates trusted Activity result data, persists it idempotently, verifies reused result IDs have identical payloads, and applies XP/Economy through their persistent reward ledgers.

The pipeline passes `result.result_id` as the reward ID to XP and Economy. Retries can therefore recover after partial application without duplicating already-applied rewards. Absolute cross-database transaction atomicity is not claimed because Activity, XP and Economy remain separate SQLite databases.

Important security boundary: the trusted-result layer does **not** verify an external Activity itself. External identity/guild verification, signature/session verification and anti-cheat validation must happen before this layer is called.

### Activity client package — IMPLEMENTED

`activities/client/package.json` contains the official `@discord/embedded-app-sdk` dependency and Vite build scripts.

### Activity client authentication — FOUNDATION IMPLEMENTED

`activities/client/index.html` is the Vite entry page.

`activities/client/src/main.js` now:

1. Reads `VITE_DISCORD_CLIENT_ID` from the Vite environment.
2. Creates `new DiscordSDK(clientId)`.
3. Waits for `discordSdk.ready()`.
4. Calls the SDK `authorize` command for an authorization code with `identify` scope.
5. Sends the one-time code to `/api/discord/token`.
6. Receives the backend-issued Discord access token.
7. Calls `discordSdk.commands.authenticate({ access_token })`.
8. Shows a basic connected/failed status.

The browser never receives the Discord application client secret.

### Activity OAuth backend — FOUNDATION IMPLEMENTED

`activities/server.py` provides a minimal dependency-free `ThreadingHTTPServer` handler for `POST /api/discord/token`.

It:

- requires `DISCORD_ACTIVITY_CLIENT_ID` and `DISCORD_ACTIVITY_CLIENT_SECRET` on the server;
- validates the request body and authorization code;
- exchanges the code with Discord's OAuth token endpoint using `application/x-www-form-urlencoded`;
- returns only the resulting access token to the Activity client;
- disables caching on the token response;
- does not log the authorization code or access token;
- does not expose the client secret to the browser.

This backend is currently a standalone server module. It has **not yet been wired into the bot lifecycle**, and the Vite development proxy has not yet been added. Therefore Activity authentication is implementation-foundation only and is not runtime-verified.

### Planned final Activity boundary

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

The final game-result endpoint must not trust arbitrary browser-supplied `user_id`, `guild_id`, reward amounts or completion claims. The backend must bind the result to the authenticated Activity session and validate game-specific rules before calling the trusted reward pipeline.

## 20. KNOWN AUDIT / IMPLEMENTATION ITEMS

High priority:

- quest completion/reward atomicity;
- moderation punishment vs logging failure;
- TEST verification role-create condition;
- profile card long names and Unicode/Cyrillic fallback.

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
- Activity signature/identity/guild verification and reward integration;
- Activity reward atomicity across the separate XP/Economy/Activity SQLite databases;
- Activity reward idempotency/recovery across all reward stores;
- Activity registry validation and initial-game implementation details;
- Activity backend lifecycle integration;
- Activity Vite development proxy;
- Activity environment configuration for client ID/secret;
- Activity URL mapping and Developer Portal configuration;
- authenticated session handling;
- game-specific server-side result validation;
- initial Snake/Sudoku/Wordle implementation.

Do not fix speculative issues without inspecting source/behavior first.

## 21. QA STATE

```text
Detailed QA started: NO
Current QA system: NONE
Current phase: IMPLEMENTATION FIRST
```

Previously runtime verified: verification basics/role hierarchy; shop scenarios from 2026-08-31; full rebuild/logging recovery 2026-09-01; latest known logging-map Check workflow.

These are not full QA.

## 22. CURRENT DEVELOPMENT ORDER

```text
1. Implement remaining planned systems.
2. Integrate each new system where appropriate.
3. Update PROJECT_STATE.md after every action.
4. When implementation is complete:
   → integration cleanup
   → detailed QA, one system at a time
   → full regression
   → technical cleanup
```

Current checkpoint:

```text
Core community/progression systems → IMPLEMENTED
Mini-games → IMPLEMENTED / QA PENDING
Social / Friends / Romantic → IMPLEMENTED / QA PENDING
Discord Activities → CLIENT + AUTH FOUNDATION / BACKEND LIFECYCLE + UI + GAMES REMAIN
Activity registry → IMPLEMENTED / QA PENDING
Activity XP reward idempotency → IMPLEMENTED
Activity Economy reward idempotency → IMPLEMENTED
Activity reward pipeline wiring → IMPLEMENTED / QA PENDING
Activity client package → IMPLEMENTED
Activity client authentication → FOUNDATION IMPLEMENTED
Activity OAuth backend → FOUNDATION IMPLEMENTED / NOT WIRED TO BOT
Activity frontend UI → MINIMAL STATUS ONLY
Initial Activities → Snake, Sudoku, Wordle
Future Activities → 2048, Minesweeper, Tetris, Flappy Bird, Connect Four, Chess, Checkers
Full QA → NOT STARTED
```

## 23. RECENT CHECKPOINT

```text
27c49fd4c0ff0cf42c83d0e3851ed1eec1698d70 → persistent social database
e90ab1944b3d93ca091b7ac2ccac964df9d532d4 → social commands/COG
89b0027ee6f19570393cecf012837a70bb11f72 → load social COG
1fd67f7fbb319a61b691022c6e7c1801c57e5a9c → Activity result ledger
5946224802115e94940c5f2ab87f7bc6729731ab → Activity roadmap expanded with initial and future games
9e584c6d80add5497c118db0aec0d5a23b0bc2da → Activity registry
a5d8bf9c138f5cb28e231b5d565572a479e9ca3d → Activity result lookup/history layer
0f1f501f4cab242453f88fd390d74312b36cfade → trusted Activity reward pipeline
082cab6e5fd383d4de31c34d1773cafd50cf0aa3 → XP reward idempotency
3348a0793009dcae7d9cf9fdb120a2ac897ec4f2 → Economy reward idempotency
86196954830ed8f1b2eaec3d584753fedb903c3d → Activity reward pipeline wiring / retry recovery
9680d41c2e7a64df751f13d7430d7232a1c4b12a → Discord Activity client package foundation
52cfd3be6cb1c6dd630b54250e8cca64162fbf5f → Discord Activity client authentication foundation
94ac969005a2850b80c71b0b035976a816d3eaf9 → Discord Activity client entry page
d99ce4f68b881faab87cf499f9a56ea7cf5e1e77 → Discord Activity OAuth token exchange backend
CURRENT STATE UPDATE → Activity OAuth/backend foundation checkpoint
```

## 24. NEW-CHAT CONTINUATION

On every new chat:

1. Read this file.
2. Inspect current GitHub `main`.
3. Identify the current implementation target.
4. Inspect connected systems.
5. Make the smallest necessary change.
6. Validate source/imports/references as far as available.
7. Update this file immediately after the action.
8. Continue from the new checkpoint.

Never claim runtime success without runtime evidence. Never reset databases. Never use abbreviated replacement code.
