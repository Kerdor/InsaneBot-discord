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
- **Update PROJECT_STATE.md after every project action/change.**
- `IMPLEMENTED` does not mean `QA PASSED`.
- CI success is not runtime QA.

### User development priority

1. Implement all agreed/planned systems first.
2. Do not start full system-by-system QA until planned implementation is complete.
3. Then perform integration cleanup, sequential QA, regression and technical cleanup.
4. Update this file after every implementation/QA action.

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
  server_manager.py verification.py moderation.py tickets.py
  xp.py economy.py shop.py quests.py achievements.py minigames.py social.py admin_panel.py
  user_cmd/create_voice.py
  logging/{chat_logs,guild_logs,moderation_logs,setup_logs,system_logs,voice_stats}.py
  logging/reaction_logs.py (disabled)
databases/
  xp.py economy.py shop.py quests.py achievements.py
  profile_customization.py moderation.py tickets.py voice_stats.py voice_rooms.py social.py
utils/profile_card.py
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
Production must not silently consume TEST mappings.

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
| Discord Activities | NOT STARTED | — | — |
| PvP | REMOVED | — | — |
| Collecting | REMOVED FOR NOW | — | — |

## 8. XP / LEVELS

Implemented in `cogs/xp.py` + `databases/xp.py`: persistent guild/user XP, message XP/cooldown, message count, counted voice XP, AFK exclusion, levels, `/level`, `/xp_ranking`, level-up DM, voice-session recovery, message economy reward, profile integration.

Defaults: message XP 15–25; message cooldown 60s; voice 5/min; level threshold `100 * level²`; message economy reward 2.

`databases/xp.py` also has `add_xp(guild_id, user_id, amount)` for generic progression XP without modifying message/voice counters.

## 9. ECONOMY / DAILY

Implemented `/balance`, `/daily`, `/pay`, `/rich`; persistent coins and rare currency, message rewards, daily, transfers, ranking, settings and Admin Panel adjustment.

Rare currency has persistence but no complete earning/spending loop yet.

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

## 18. SOCIAL / FRIENDS / ROMANTIC — NEW IMPLEMENTATION

Status: `IMPLEMENTED / RUNTIME NOT TESTED / QA PENDING`.

Files:

```text
databases/social.py
cogs/social.py
config.py
```

Persistent `social.db` stores:

- friend requests;
- normalized friendships;
- romantic requests;
- normalized romantic relationships.

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

Rules currently implemented:

- self-add/proposal is rejected;
- friend request requires mutual acceptance;
- duplicate/reverse friend requests are rejected;
- romantic proposal requires an existing friendship;
- romantic relationship requires mutual acceptance;
- ending romance preserves friendship;
- all state is guild-scoped and persistent;
- relationship pairs are normalized to avoid duplicate direction records.

No XP/economy rewards are attached yet; this avoids inventing a progression balance before QA/integration design.

## 19. DISCORD ACTIVITIES — PLANNED / BLOCKED UNTIL REAL BOUNDARY

Target:

```text
verified Activity result
        ↓
trusted integration
        ↓
XP / Economy / Quests / Achievements / Rankings / Profile
```

Before implementation: identity verification, guild verification, anti-cheat, reward calculation, idempotency, persistence and retry/failure semantics must be defined.

Do not fake external Activity results or mark an Activity integration complete without a real verified boundary.

## 20. KNOWN AUDIT ITEMS

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
- social command and relationship concurrency/edge cases.

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
Discord Activities → PLANNED / requires real verified external boundary
Full QA → NOT STARTED
```

## 23. RECENT CHECKPOINT

```text
27c49fd4c0ff0cf42c83d0e3851ed1eec1698d70 → persistent social database
 e90ab1944b3d93ca091b7ac2ccac964df9d532d4 → social commands/COG
89b002e7ee6f19570393cecf012837a70bb11f72 → load social COG
CURRENT STATE UPDATE → this commit
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
