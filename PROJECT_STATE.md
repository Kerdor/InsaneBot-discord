# InsaneBot-discord — PROJECT STATE / MASTER ROADMAP

Repository: https://github.com/Kerdor/InsaneBot-discord  
Branch: `main`  
State date: 2026-09-02  
Current source branch: `main`

> **This file is the authoritative hand-off document for the project.** It describes the product concept, binding decisions, current architecture, implementation state, documentation state, known technical issues, QA state and exact next steps. A new development chat must be able to continue from this file without requiring the user to re-explain the project from zero.
>
> The source code on GitHub `main` is always the final authority for implementation details. If this document and the source disagree, inspect the source and then correct this file.

---

# 1. BINDING DEVELOPMENT RULES

- Act as a technical editor/developer.
- Inspect current GitHub `main` before code changes.
- Do not guess about implementation when source can be inspected.
- Preserve architecture, names, function order and formatting unless change is necessary.
- Make the smallest necessary code change.
- Do not add libraries without a real requirement.
- Do not perform unrelated refactors.
- Never use `...` as omitted code in replacement snippets.
- If a function is changed for manual replacement, provide the complete function.
- Check callers, imports, events and references after changes.
- Prefer `БЫЛО → СТАЛО` for focused changes.
- Python indentation: 4 spaces.
- Never destructively reset/delete runtime databases.
- Normal project changes go directly to `main`.
- After code/config fixes, update this file with the current state and verification result.
- `IMPLEMENTED` never means `QA PASSED` automatically.
- CI success is not runtime QA.
- Comments/docstrings must explain purpose, architecture, constraints and non-obvious integration points; avoid obvious line-by-line comments.

---

# 2. PRODUCT CONCEPT — LOCKED

InsaneBot is a **Discord community/progression bot**, not a traditional RPG.

Core loop:

```text
Discord activity
   ├─ messages
   ├─ voice
   ├─ daily
   ├─ quests
   ├─ shop activity
   └─ future mini-games / Activities
          ↓
   XP / Economy
          ↓
   Levels / Rankings / Quests / Achievements / Profile
```

The systems must reinforce one another and reuse existing persistent state.

## Explicitly NOT part of the current concept

- talismans;
- consumable combat items;
- loot boxes;
- RPG equipment/inventory;
- meaningless RPG statistics;
- combat systems without a strong community purpose;
- PvP;
- collecting.

The shop is primarily for Discord/community benefits such as roles.

## Future only

- mini-games;
- Discord Activities;
- social interactions;
- Friends;
- Romantic relationships;
- richer profile cosmetics.

Do not start these before the current core is integrated and QA-tested unless explicitly requested.

---

# 3. STATUS DEFINITIONS

- `PLANNED` — agreed, not implemented.
- `IN PROGRESS` — currently being implemented.
- `IMPLEMENTED` — source implementation exists.
- `INTEGRATION CHECK` — implementation exists and cross-system verification is required.
- `RUNTIME TESTED` — manually tested against the running bot for listed scenarios.
- `QA PASSED` — detailed QA and regression checks completed.
- `QA PENDING` — implementation exists but detailed QA is incomplete.
- `POSTPONED` — deliberately postponed.
- `REMOVED` — deliberately removed from roadmap.
- `BLOCKED` — blocked by a stated dependency/decision.

Target for current core:

`IMPLEMENTED → INTEGRATION CHECK → RUNTIME TESTED → QA PASSED`

---

# 4. CURRENT REPOSITORY / ARCHITECTURE

```text
.
├── .env.example
├── .gitattributes
├── .gitignore
├── .python-version
├── PROJECT_STATE.md
├── config.py
├── dev_runner.py
├── logs.py
├── main.py
├── requirements.txt
├── server_structure.py
├── cogs/
│   ├── achievements.py
│   ├── admin_panel.py
│   ├── economy.py
│   ├── moderation.py
│   ├── owner.py
│   ├── owner_dump.py
│   ├── quests.py
│   ├── rebuild_command.py
│   ├── rebuild_test_server.py
│   ├── server_manager.py
│   ├── shop.py
│   ├── tickets.py
│   ├── verification.py
│   ├── xp.py
│   ├── logging/
│   │   ├── __init__.py
│   │   ├── base_logger.py
│   │   ├── chat_logs.py
│   │   ├── guild_logs.py
│   │   ├── moderation_logs.py
│   │   ├── reaction_logs.py
│   │   ├── setup_logs.py
│   │   ├── system_logs.py
│   │   └── voice_stats.py
│   └── user_cmd/
│       ├── create_voice.py
│       └── get_roles.py
├── databases/
│   ├── Insane.sqlite3
│   ├── achievements.py
│   ├── economy.py
│   ├── moderation.py
│   ├── profile_customization.py
│   ├── quests.py
│   ├── settings.py
│   ├── shop.py
│   ├── tickets.py
│   ├── voice_rooms.py
│   ├── voice_stats.py
│   └── xp.py
└── utils/
    └── profile_card.py
```

`README.md` is currently absent.

`cogs/user_cmd/get_roles.py` exists but is not loaded and is treated as legacy/dead code unless explicitly reintroduced.

`cogs/logging/reaction_logs.py` exists but is intentionally disabled/not loaded.

---

# 5. TECHNOLOGY

- Python version: controlled by `.python-version`.
- Discord: `disnake>=2.12.1,<3`.
- Profile card rendering: `Pillow>=11,<13`.
- Persistence: built-in Python `sqlite3`.
- No other framework is required.

Do not add dependencies without a real requirement.

---

# 6. TEST / PRODUCTION MODEL

Current development environment:

```text
ENVIRONMENT=test
MAIN_GUILD_ID=1217530337664434246
TEST_GUILD_ID=519209364280573954
TEST_GUILDS=[519209364280573954]
```

TEST guild:

```text
Insane TEST
519209364280573954
```

TEST development must never accidentally modify MAIN.

`config.py` selects the active guild by environment and validates server/logging maps against the active guild.

Important rule:

**Production must never silently consume a TEST server map.**

Relevant fixes:

```text
f4321d9aa022b7085c19b510cf965d073d4ed544
→ TEST/MAIN config and server-map isolation

f19eedcf4f3bbc1476aabc9f17f6f355602e5590
→ logging map compatibility: old server_logs/current guild_logs
```

The latest known Check workflow for the logging-map commit completed successfully.

---

# 7. STARTUP / COG LOADING

Entrypoint:

```text
main.py
```

Development runner:

```text
dev_runner.py
```

Configured active COGs:

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
cogs.admin_panel
```

`main.py` creates the Disnake bot, loads COGs, performs explicit TEST command synchronization, starts the client and exposes owner-only dynamic COG loading commands.

Expected progression commands include:

```text
/level
/xp_ranking
/balance
/daily
/pay
/rich
/shop
/buy
/profile
/profile_customize
/quests
/achievements
/voice
/voice_ranking
```

Command sync still requires detailed runtime QA after major additions.

---

# 8. DEVELOPMENT RUNNER

`dev_runner.py`:

- starts `main.py`;
- polls Git every 5 seconds;
- executes `git pull`;
- detects HEAD changes;
- restarts the bot process after an update;
- exits on Ctrl+C/process termination.

Status: `IMPLEMENTED / QA PENDING`.

---

# 9. DATABASE ARCHITECTURE

Persistent systems are SQLite-backed.

```text
databases/xp.py                  → xp.db
databases/economy.py             → economy.db
databases/shop.py                → economy.db
databases/settings.py            → settings.db
databases/moderation.py          → moderation.db
databases/tickets.py             → tickets.db
databases/quests.py              → quests.db
databases/achievements.py        → achievements.db
databases/profile_customization.py → profile_customization.db
databases/voice_stats.py         → Insane.sqlite3
databases/voice_rooms.py         → configured voice-room persistence
```

Runtime databases are user/server state. Never reset them to make tests pass. Schema changes must use safe migration logic.

---

# 10. MASTER SYSTEM STATUS

| System | Implementation | Runtime | QA | Status |
|---|---|---|---|---|
| Configuration / TEST-MAIN | DONE | PARTIAL | PENDING | `IMPLEMENTED / QA PENDING` |
| COG loading / startup | DONE | HISTORICALLY VERIFIED | PENDING | `IMPLEMENTED / QA PENDING` |
| Owner/admin | DONE | PARTIAL | PENDING | `IMPLEMENTED / QA PENDING` |
| Server Manager | DONE | PARTIAL | PENDING | `IMPLEMENTED / QA PENDING` |
| Rebuild | DONE | PARTIAL | PENDING | `IMPLEMENTED / QA PENDING` |
| Verification | DONE | LIVE VERIFIED | PENDING | `RUNTIME TESTED / QA PENDING` |
| Moderation | DONE | PARTIAL | PENDING | `IMPLEMENTED / QA PENDING` |
| Tickets | DONE | PARTIAL | PENDING | `IMPLEMENTED / QA PENDING` |
| Logging | DONE | PARTIAL | PENDING | `IMPLEMENTED / QA PENDING` |
| Voice statistics | DONE | PARTIAL | PENDING | `IMPLEMENTED / QA PENDING` |
| Voice rooms | DONE | PARTIAL | PENDING | `IMPLEMENTED / QA PENDING` |
| XP / Levels | DONE | PARTIAL | PENDING | `IMPLEMENTED / QA PENDING` |
| Economy / Daily | DONE | PARTIAL | PENDING | `IMPLEMENTED / QA PENDING` |
| Shop | DONE | TESTED | PENDING REGRESSION | `RUNTIME TESTED / QA PENDING` |
| Quests | DONE | NOT STARTED | PENDING | `IMPLEMENTED / QA PENDING` |
| Achievements | DONE | NOT STARTED | PENDING | `IMPLEMENTED / QA PENDING` |
| Profile Card | DONE | NOT STARTED | PENDING | `IMPLEMENTED / QA PENDING` |
| Profile customization | DONE | NOT STARTED | PENDING | `IMPLEMENTED / QA PENDING` |
| Mini-games | NOT STARTED | — | — | `PLANNED` |
| Discord Activities | NOT STARTED | — | — | `PLANNED` |
| Social / Friends / Romantic | NOT STARTED | — | — | `PLANNED` |
| PvP | — | — | — | `REMOVED` |
| Collecting | — | — | — | `REMOVED FOR NOW` |

---

# 11. XP / LEVELS

Status: `IMPLEMENTED / QA PENDING`

Sources:

```text
cogs/xp.py
databases/xp.py
```

Implemented:

- persistent XP per guild/user;
- eligible message XP;
- message cooldown;
- configurable message XP min/max;
- message count;
- counted voice XP;
- AFK exclusion;
- persistent level;
- automatic level calculation;
- `/level`;
- `/xp_ranking`;
- level-up DM;
- persistent voice-session recovery;
- message economy reward;
- generated profile card;
- profile customization integration.

Current defaults:

```text
xp_message_min = 15
xp_message_max = 25
xp_message_cooldown = 60 sec
xp_voice_per_minute = 5
level threshold = 100 * level²
message economy reward = 2 🪙
```

Voice XP must reuse VoiceStats persistence rather than creating a duplicate voice-time counter.

QA remains pending.

---

# 12. ECONOMY / DAILY

Status: `IMPLEMENTED / QA PENDING`

Sources:

```text
cogs/economy.py
databases/economy.py
```

Currencies:

- 🪙 normal currency;
- 💎 rare currency.

Commands:

```text
/balance
/daily
/pay
/rich
```

Implemented:

- per-guild/user balances;
- user initialization;
- message rewards;
- daily reward;
- transfers;
- rich ranking;
- configurable economy enable/disable;
- Admin Panel balance adjustment.

Rare currency exists in persistence but does not yet have a complete earning/spending loop.

Daily cooldown uses persistent timestamp state and a 24-hour interval.

---

# 13. SHOP

Status: `RUNTIME TESTED / QA PENDING`

Sources:

```text
cogs/shop.py
databases/shop.py
```

Public commands:

```text
/shop
/buy <item_id>
```

Admin operations:

- create;
- edit;
- enable/disable;
- delete;
- configure name/description/price/role.

Purchase model:

```text
item exists + enabled
      ↓
role valid / user does not already have it
      ↓
charge economy
      ↓
assign Discord role
      ↓
assignment failure → refund
      ↓
success → shop_purchase event
```

Runtime tests on 2026-08-31 covered display, CRUD/edit, disable/delete, nonexistent item, insufficient balance, duplicate purchase, missing role, assignment failure/refund and successful purchase.

Remaining QA: permissions, economy-disabled behavior, hierarchy, concurrent purchases, achievement event and restart persistence.

Shop UI redesign/pagination is postponed unless explicitly requested.

---

# 14. QUESTS

Status: `IMPLEMENTED / QA PENDING`

Sources:

```text
cogs/quests.py
databases/quests.py
```

Command:

```text
/quests
```

Current daily quests:

```text
messages_10      → 10 messages → 50 🪙
voice_30         → 30 counted voice minutes → 100 🪙
voice_sessions_3 → 3 counted voice joins → 75 🪙
```

Rules:

- per guild/user/date;
- UTC quest date;
- persistent records;
- progress capped at target;
- completion persistent;
- reward claim once;
- bots/webhooks excluded;
- AFK voice excluded;
- voice-session recovery uses persistent voice state;
- economy uses existing economy storage.

Known integration risk: quest completion and economy reward are separate persistence operations, creating a possible crash window. This must be tested/hardened before QA PASS.

---

# 15. ACHIEVEMENTS

Status: `IMPLEMENTED / QA PENDING`

Sources:

```text
cogs/achievements.py
databases/achievements.py
```

Command:

```text
/achievements
```

Current achievements:

```text
messages_1000 → 1000 messages
voice_10h     → 10 h counted voice
rich_10000    → 10 000 🪙 balance
shop_purchase → first successful shop purchase
active_7_days → activity on 7 UTC dates
```

Rules:

- persistent per guild/user;
- permanent unlocks;
- capped progress;
- activity-day deduplication;
- message progress reuses XP message count;
- voice progress reuses persistent voice statistics;
- balance progress reuses economy balance;
- shop progress consumes successful purchase event.

`voice_10h` intentionally uses actual persistent counted voice time rather than a derived XP configuration.

QA remains pending.

---

# 16. PROFILE CARD

Status: `IMPLEMENTED / QA PENDING`

Sources:

```text
cogs/xp.py
utils/profile_card.py
```

`/profile` now generates a PNG card rather than the old text Embed.

Current data includes:

- avatar;
- display name;
- level;
- XP progress;
- total XP;
- 🪙 coins;
- 💎 rare currency;
- message count;
- voice XP;
- achievement count;
- customized bio.

Renderer size:

```text
1000 × 460
```

Pillow is used.

Profile customization is a layer on top of this renderer.

QA remains pending, including long names and Unicode/Cyrillic rendering.

---

# 17. PROFILE CUSTOMIZATION

Status: `IMPLEMENTED / QA PENDING`

Sources:

```text
cogs/xp.py
databases/profile_customization.py
utils/profile_card.py
```

Command:

```text
/profile_customize
```

Current options:

- background color;
- accent color;
- short bio;
- reset.

Defaults:

```text
background = #181B23
accent = #FFD75A
bio limit = 70 characters
color format = #RRGGBB
```

Persistence is per `guild_id + user_id`.

Colors are validated/normalized. Bio is limited to 70 characters. Renderer uses safe fallbacks.

QA remains pending.

---

# 18. VOICE STATISTICS

Status: `IMPLEMENTED / QA PENDING`

Sources:

```text
cogs/logging/voice_stats.py
databases/voice_stats.py
```

Commands:

```text
/voice
/voice_ranking
```

Tracks:

- total voice seconds;
- per-channel seconds;
- active persistent sessions.

Rules:

- AFK excluded;
- bots excluded;
- restart recovery through persistent sessions;
- channel moves close/start sessions;
- `on_ready` reconciles active sessions.

This is the foundational source for voice XP, quests and achievements.

---

# 19. VOICE ROOMS / CREATE VOICE

Status: `IMPLEMENTED / QA PENDING`

Sources:

```text
cogs/user_cmd/create_voice.py
databases/voice_rooms.py
```

Provides user-created/private voice rooms, including room controls, rename, user limit, co-owner/access management, main-room selection and persistence/cleanup.

This system is separate from VoiceStats even though both consume Discord voice events.

---

# 20. VERIFICATION

Status: `RUNTIME TESTED / QA PENDING`

Source:

```text
cogs/verification.py
```

Current flow:

```text
new member → Not verified
verification panel → arithmetic challenge
correct answer → Not verified removed + Member added
```

Owner synchronization assigns Owner to the server owner.

Previously live-verified hierarchy:

```text
Owner > Administrator > Moderator > Helper > Member > Not verified > @everyone
```

Technical note: the role-create synchronization path contains a TEST-guild-specific condition. Audit before treating production as fully supported.

---

# 21. MODERATION

Status: `IMPLEMENTED / QA PENDING`

Sources:

```text
cogs/moderation.py
databases/moderation.py
```

Commands:

```text
/warn
/timeout
/kick
/ban
/unban
/history
```

Implemented:

- staff role checks;
- configurable action enable/disable;
- punishment persistence;
- timeout maximum;
- history;
- logging;
- modal actions;
- interaction timeout hardening;
- modal callbacks reuse loaded Moderation COG.

Known audit candidates:

- logging failure after punishment;
- staff/target role hierarchy;
- Discord permission failures.

Relevant fixes include:

```text
d2c0509599b11359c1bc056dcac88c08deb7b141
64c80fb3ab96fcb954ae7524d799a57feaa0247f
```

---

# 22. TICKETS

Status: `IMPLEMENTED / QA PENDING`

Sources:

```text
cogs/tickets.py
databases/tickets.py
```

Flow:

```text
panel → create → modal → private thread → support → close confirmation → transcript → archive/lock
```

Implemented:

- persistent tickets;
- one-open-ticket logic;
- private threads;
- support/moderation access;
- creation modal;
- close confirmation;
- transcript;
- transcript setting;
- ready-time recovery;
- interaction timeout fixes;
- parent privacy fix.

Relevant fixes:

```text
041dcb14bc4f2b9db0c01c0f1b687b03e6ce379c
1755d209f4bacf859a9da3396fef94e252140f6
```

---

# 23. LOGGING

Status: `IMPLEMENTED / QA PENDING`

Sources:

```text
logs.py
cogs/logging/base_logger.py
cogs/logging/chat_logs.py
cogs/logging/guild_logs.py
cogs/logging/moderation_logs.py
cogs/logging/setup_logs.py
cogs/logging/system_logs.py
cogs/logging/voice_stats.py
```

Current groups:

- chat;
- guild/member/server;
- moderation;
- setup;
- system;
- voice/statistics.

`reaction_logs.py` remains intentionally unloaded.

Local logs:

```text
logs/bot.log
logs/errors.log
```

Runtime mapping uses `.logging_channels.json` and supports old `server_logs` as fallback to `guild_logs`.

A rebuild/logging cache bug was fixed. Full rebuild on 2026-09-01 completed without the previously observed Unknown Channel / 404 logging errors.

---

# 24. SERVER MANAGER

Status: `IMPLEMENTED / QA PENDING`

Sources:

```text
cogs/server_manager.py
server_structure.py
```

Responsibilities:

- active guild targeting;
- managed category/channel permissions;
- new-channel synchronization;
- category-move synchronization;
- owner-only `/sync_server`;
- owner-only `/channel_create`.

Managed categories include:

```text
🔐 ВХОД
📢 ИНФОРМАЦИЯ
💬 ОБЩЕНИЕ
🎮 ИГРА
🎫 ПОДДЕРЖКА
🛡️ МОДЕРАЦИЯ
🔊 ГОЛОСОВЫЕ КАНАЛЫ
```

Relevant hierarchy fix:

```text
4dea2a9d80e05672af8c5fd77dad12a1732db0f0
```

---

# 25. REBUILD

Status: `IMPLEMENTED / QA PENDING`

Sources:

```text
cogs/rebuild_command.py
cogs/rebuild_test_server.py
```

Current test rebuild is owner-only and restricted to TEST environment/test guild, with explicit confirmation.

Rebuild recreates configured server structure and updates runtime mappings.

Hard requirements:

- never target MAIN from TEST rebuild;
- preserve runtime databases;
- restore role/channel references;
- restore logging mappings;
- remain compatible with verification/tickets/logging.

Interaction timeout hardening:

```text
a6257712676522a2e31d4bf20ea773a8f4d0ca5e
```

---

# 26. ADMIN PANEL

Status: `IMPLEMENTED / QA PENDING`

Source:

```text
cogs/admin_panel.py
databases/settings.py
```

Central server configuration UI covering general/progression, moderation, tickets, shop, logging and economy settings.

Important configurable values include:

```text
xp_message_min
xp_message_max
xp_message_cooldown
xp_voice_per_minute
economy_message_reward
economy_daily_reward
xp_enabled
economy_enabled
moderation_timeout_max
moderation_warn_enabled
moderation_timeout_enabled
moderation_kick_enabled
moderation_ban_enabled
moderation_owner_role
moderation_administrator_role
moderation_moderator_role
moderation_helper_role
tickets_enabled
tickets_create_channel
tickets_channel
tickets_support_role
tickets_transcript_enabled
```

Settings are persistent per guild and audited in `settings_audit`.

---

# 27. OWNER / OWNER DUMP

Status: `IMPLEMENTED / QA PENDING`

Sources:

```text
cogs/owner.py
cogs/owner_dump.py
```

Owner-level operational tools. They are not part of the progression loop.

Owner protection and sensitive-data exposure still require QA.

---

# 28. FUTURE MINI-GAMES / DISCORD ACTIVITIES

## Mini-games

Status: `PLANNED`

Games may run directly through Discord bot components or as Activities. They must reuse existing XP/economy/quest/achievement/ranking/profile infrastructure.

## Discord Activities

Status: `PLANNED`

Architecture:

```text
Activity game result
      ↓
trusted result integration
      ↓
InsaneBot progression
 ├─ XP
 ├─ Economy
 ├─ Quests
 ├─ Achievements
 ├─ Rankings
 └─ Profile
```

Before implementation, define identity verification, guild verification, anti-cheat, reward calculation, idempotency, persistence and retry/failure semantics.

---

# 29. INTEGRATION MAP

```text
Messages
 ├─ XP
 ├─ Economy
 ├─ Quests
 ├─ Achievements
 └─ Chat logging

Voice
 ├─ VoiceStats
 ├─ XP
 ├─ Quests
 ├─ Achievements
 ├─ Voice logging
 └─ Voice rooms

Shop purchase
 ├─ Economy
 ├─ Discord role
 └─ shop_purchase → Achievements

Profile
 ├─ XP
 ├─ Economy
 ├─ Voice
 ├─ Achievements
 └─ Profile customization

Rebuild
 ├─ Server Manager
 ├─ Logging
 ├─ Verification
 └─ Tickets
```

When changing one system, inspect connected systems before changing shared behavior.

---

# 30. DOCUMENTATION PASS — CURRENT STATE

The current development session added architecture/purpose docstrings and comments without intentionally changing runtime logic to the following files:

```text
config.py
main.py
cogs/xp.py
cogs/economy.py
cogs/quests.py
cogs/achievements.py
cogs/shop.py
cogs/moderation.py
cogs/verification.py
cogs/owner_dump.py
utils/profile_card.py
databases/settings.py
databases/profile_customization.py
databases/economy.py
databases/achievements.py
databases/quests.py
```

Important: documentation pass is **not yet complete for every repository file**. Remaining files require the same docs-only treatment before the documentation task can honestly be marked complete.

Files still requiring documentation pass at this state include, at minimum:

```text
cogs/admin_panel.py
cogs/rebuild_command.py
cogs/rebuild_test_server.py
cogs/server_manager.py
cogs/tickets.py
cogs/owner.py
cogs/user_cmd/create_voice.py
cogs/logging/base_logger.py
cogs/logging/chat_logs.py
cogs/logging/guild_logs.py
cogs/logging/moderation_logs.py
cogs/logging/setup_logs.py
cogs/logging/system_logs.py
cogs/logging/voice_stats.py
databases/moderation.py
databases/shop.py
databases/tickets.py
databases/voice_rooms.py
databases/voice_stats.py
databases/xp.py
server_structure.py
logs.py
dev_runner.py
```

`cogs/user_cmd/get_roles.py` and `cogs/logging/reaction_logs.py` are legacy/disabled and do not need active-system documentation unless they are intentionally reintroduced.

Documentation commits already made include:

```text
config.py
→ dd3db445085913df285f2552f4459220073ad6c4

cogs/xp.py
→ 615e46880e112af5c426eb947886fd0c86a90ef8

cogs/economy.py
→ 5e4480690a9aba6e18c4b170df145d24fe5522ab

cogs/quests.py
→ a41375e9f0a408e4d72be3d1758a61ecf8e62897

cogs/achievements.py
→ bbf03036fcf3291b176b35a5b2114d956bd8997f

cogs/shop.py
→ c2678b76b8eba27eca79667fcb59a19d19bb45a7

utils/profile_card.py
→ 75247478231719903e77286bcf0f03037f182dbb

databases/settings.py
→ f8927ec7c0d55cee091bd05ee8b8e47312a80779

databases/economy.py
→ 11cb6fceb17c72ba356283a5cda5effe3558dfe1

databases/profile_customization.py
→ c5fb9ad29a7df15c94f4496292e3de012b6b8ebf

databases/quests.py
→ 705c0ec2dbbedd4465753603bc1ea4b09259cc90
```

Recent documentation commits also exist for `main.py`, `cogs/moderation.py`, `cogs/verification.py` and `cogs/owner_dump.py`; their exact SHA should be taken from Git history if referenced later rather than guessed.

---

# 31. KNOWN TECHNICAL AUDIT ITEMS

## HIGH PRIORITY

### Quest reward atomicity

Quest completion and economy reward are separate persistence operations. Test the crash window and harden only if required.

### Moderation logging failure

Some punishment flows perform the punishment before logging. Determine whether logging failure can produce unacceptable user-facing behavior.

### Production verification condition

Audit the TEST-guild-specific `on_guild_role_create` condition before production support is considered complete.

### Profile card rendering

Test long names and Unicode/Cyrillic font fallback.

## MEDIUM / LOW

- `active_7_days` exact semantic definition.
- Timing of voice achievement unlocks.
- Legacy `get_roles.py`.
- Disabled `reaction_logs.py`.
- Guild-only command behavior.
- Permission/role hierarchy edge cases.
- Async interaction acknowledgement.
- Potential duplicate event handling.

Do not fix speculative issues without inspecting the actual source/behavior first.

---

# 32. IMPORTANT FIX HISTORY

```text
4dea2a9d80e05672af8c5fd77dad12a1732db0f0
Server/role hierarchy fix.

041dcb14bc4f2b9db0c01c0f1b687b03e6ce379c
Ticket parent-channel privacy fix.

1755d209f4bacf859a9da3396fef94e252140f6
Ticket interaction timeout hardening.

a6257712676522a2e31d4bf20ea773a8f4d0ca5e
Rebuild command interaction timeout hardening.

64c80fb3ab96fcb954ae7524d799a57feaa0247f
Moderation interaction timeout hardening.

d2c0509599b11359c1bc056dcac88c08deb7b141
Moderation modal reuses loaded Moderation COG.

3767d4b7406f61b73437250ecc577259cd589371
Verification persistent view registration hardened.

55ac0a9043eed6cffc5e8d8d2fa60bf5fa020f21
Voice achievement uses persistent actual voice time.

b90d279960ba0a83822afd00fdf2e2aa0c39db07
Profile customization database added.

231fdab6110a6818028f4a2095d322be8de06884
Profile card customization support.

06af69d097c5a9e45638e7f3a3897528d94f5057
Profile customization command/integration.

f4321d9aa022b7085c19b510cf965d073d4ed544
TEST/MAIN config and server-map isolation.

f19eedcf4f3bbc1476aabc9f17f6f355602e5590
Logging map compatibility.
```

---

# 33. QA STATE

```text
Detailed QA started: NO
Current QA system: NONE
Current phase: PRE-QA / DOCUMENTATION + INTEGRATION PREPARATION
```

Already runtime verified:

- Verification basic flow and role hierarchy.
- Shop scenarios listed in Section 13.
- Full rebuild/logging recovery on 2026-09-01 without the previous Unknown Channel / 404 logging errors.
- Latest known Check workflow for the logging-map baseline completed successfully.

None of these facts should be interpreted as full QA for the whole system.

---

# 34. LOCKED DEVELOPMENT ORDER

## Step 1 — Finish documentation pass

Document the remaining active files with docs/comments only. Do not change runtime logic.

## Step 2 — Integration audit

Check, in order:

```text
XP ↔ Levels
XP ↔ Economy
XP ↔ Quests
XP ↔ Achievements
Economy ↔ Daily
Economy ↔ Shop
Economy ↔ Quests
Economy ↔ Achievements
Shop ↔ Achievements
VoiceStats ↔ XP
VoiceStats ↔ Quests
VoiceStats ↔ Achievements
Achievements ↔ Profile Card
Profile Customization ↔ Profile Card
COGs ↔ command sync
Rebuild ↔ mappings
Rebuild ↔ logging
Rebuild ↔ verification
Rebuild ↔ tickets
Restart ↔ persistent state
```

Check for missing imports, stale references, wrong event names, duplicate state, persistence gaps and guild/config isolation.

## Step 3 — Detailed QA

Recommended order:

1. Tickets
2. Moderation
3. Verification
4. XP / Levels
5. Economy / Daily
6. Shop
7. Quests
8. Achievements
9. Profile Card
10. Profile customization
11. Voice statistics / rankings
12. Voice rooms
13. Admin Panel
14. Server Manager
15. Rebuild
16. Logging
17. Runner
18. Full regression

Update this file immediately after each QA system.

## Step 4 — Technical cleanup

After functional QA:

- dead code;
- stale imports/references;
- duplicate logic;
- async correctness;
- interaction acknowledgement;
- permissions/hierarchy;
- channel/thread correctness;
- TEST/MAIN isolation;
- database consistency;
- event ordering;
- race conditions;
- exception handling;
- COG architecture;
- runner behavior.

## Step 5 — Product expansion

Only after the current core is integrated and QA-passed:

```text
Mini-games
   ↓
Discord Activities
   ↓
XP / Economy / Quests / Achievements / Rankings / Profile integration
```

---

# 35. NEW-CHAT CONTINUATION RULE

When continuing in a new chat:

1. Read this entire file.
2. Inspect current GitHub `main`.
3. Verify the actual source against this state.
4. Identify the exact system being changed.
5. Inspect connected systems from the integration map.
6. Make the smallest necessary change.
7. Check callers/imports/events/references.
8. Run appropriate validation.
9. Update this file with the result.
10. Commit directly to `main`.

Never assume this document is newer than source code.

For manual code fixes, provide complete replacement functions/fragments and never abbreviated code.

For QA records use:

```text
Date
System
Scenario
Expected
Actual
Result
Regression notes
```

---

# 36. FINAL CHECKPOINT

Current core is implemented at the product level:

```text
✓ Infrastructure
✓ Server management
✓ Verification
✓ Moderation
✓ Tickets
✓ Logging
✓ Voice
✓ XP / Levels
✓ Economy / Daily
✓ Shop
✓ Quests
✓ Achievements
✓ Profile Card
✓ Profile Customization
```

These checkmarks mean implemented/established, not automatically QA-passed.

The immediate goal is:

> **Finish docs-only pass → integration-clean core → system-by-system QA → regression → technical cleanup → mini-games / Discord Activities.**

PvP remains removed. Collecting remains removed for now. The community/progression direction remains binding until explicitly changed by the user.
