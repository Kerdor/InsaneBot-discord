# InsaneBot-discord — PROJECT STATE / MASTER ROADMAP

Repository: https://github.com/Kerdor/InsaneBot-discord  
Branch: `main`  
State date: 2026-09-02  
Current source branch: `main`

> This file is the authoritative hand-off document. GitHub `main` source is the final authority when source and this document disagree.

---

# 1. BINDING DEVELOPMENT RULES

- Inspect current `main` and this file before serious changes.
- Preserve architecture and existing behavior unless a change is required.
- Make the smallest correct change.
- Do not add dependencies without a real requirement.
- Never use `...` as omitted code in replacement code.
- Changed functions must be provided completely when manual replacement is required.
- Never delete/reset runtime databases.
- Normal changes go directly to `main`.
- After every project action/change, update this file with the current checkpoint.
- `IMPLEMENTED` does not mean `QA PASSED`.
- CI success is not runtime QA.

User development priority (binding):

1. Continue implementing all agreed/planned systems first.
2. Do NOT start the full system-by-system QA phase until implementation of the planned systems is complete.
3. After all planned implementation is complete, perform QA sequentially, one system at a time, updating this file after every QA action/result.

---

# 2. PRODUCT CONCEPT

InsaneBot is a Discord **community/progression bot**, not a traditional RPG.

Core loop:

```text
Discord activity
 ├─ messages
 ├─ voice
 ├─ daily
 ├─ quests
 ├─ shop
 └─ mini-games / future Activities
        ↓
 XP / Economy
        ↓
 Levels / Rankings / Quests / Achievements / Profile
```

Do not add without explicit approval:

- talismans;
- combat items;
- loot boxes;
- RPG equipment/inventory;
- meaningless RPG stats;
- combat systems without community purpose;
- PvP;
- collecting.

Future product directions:

- mini-games;
- Discord Activities;
- social interactions;
- Friends;
- Romantic relationships;
- richer profile cosmetics.

---

# 3. STATUS DEFINITIONS

- `PLANNED` — agreed, not implemented.
- `IN PROGRESS` — currently being implemented.
- `IMPLEMENTED` — source implementation exists.
- `INTEGRATION CHECK` — implementation exists and cross-system checks are required.
- `RUNTIME TESTED` — manually tested for listed scenarios.
- `QA PASSED` — detailed QA/regression completed.
- `QA PENDING` — implementation exists but detailed QA is incomplete.
- `POSTPONED` — deliberately postponed.
- `REMOVED` — removed from roadmap.
- `BLOCKED` — blocked by dependency/decision.

---

# 4. CURRENT ARCHITECTURE

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
│   ├── minigames.py
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

`README.md` is absent.
`get_roles.py` is legacy/dead and unloaded.
`reaction_logs.py` is intentionally disabled/unloaded.

Technology:

- Python from `.python-version`.
- `disnake>=2.12.1,<3`.
- `Pillow>=11,<13`.
- built-in `sqlite3`.

---

# 5. TEST / MAIN

Current development configuration:

```text
ENVIRONMENT=test
MAIN_GUILD_ID=1217530337664434246
TEST_GUILD_ID=519209364280573954
TEST_GUILDS=[519209364280573954]
```

TEST guild: `Insane TEST` / `519209364280573954`.

Production must never silently consume TEST server mappings.

Relevant fixes:

```text
f4321d9aa022b7085c19b510cf965d073d4ed544 → TEST/MAIN isolation
f19eedcf4f3bbc1476aabc9f17f6f355602e5590 → logging map compatibility
```

---

# 6. STARTUP / COGS

`main.py` loads `BotConfig.COGS`, explicitly ensures `cogs.admin_panel`, synchronizes TEST commands and runs the Discord lifecycle.

Active COG order now includes:

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
cogs.admin_panel
```

Expected progression commands now include `/minigame` in addition to:

```text
/level /xp_ranking /balance /daily /pay /rich
/shop /buy /profile /profile_customize /quests /achievements
/voice /voice_ranking
```

---

# 7. DATABASES

Persistent databases are real user/server state. Never reset them.

```text
xp.py                  → xp.db
economy.py             → economy.db
shop.py                → economy.db
settings.py            → settings.db
moderation.py          → moderation.db
tickets.py             → tickets.db
quests.py              → quests.db
achievements.py        → achievements.db
profile_customization.py → profile_customization.db
voice_stats.py         → Insane.sqlite3
voice_rooms.py         → configured persistence
```

`databases/xp.py` now also has `add_xp(guild_id, user_id, amount)`. It adds generic XP without modifying message/voice counters and preserves existing rows.

---

# 8. MASTER SYSTEM STATUS

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
| Mini-games | DONE | NOT TESTED | NOT STARTED | `IMPLEMENTED / QA BLOCKED UNTIL IMPLEMENTATION PHASE ENDS` |
| Discord Activities | NOT STARTED | — | — | `PLANNED` |
| Social / Friends / Romantic | NOT STARTED | — | — | `PLANNED` |
| PvP | — | — | — | `REMOVED` |
| Collecting | — | — | — | `REMOVED FOR NOW` |

---

# 9. XP / LEVELS

Implemented in `cogs/xp.py` + `databases/xp.py`:

- persistent guild/user XP;
- message XP/cooldown;
- message counter;
- counted voice XP;
- AFK exclusion;
- levels and automatic level calculation;
- `/level`, `/xp_ranking`;
- level-up DM;
- persistent voice-session recovery;
- message economy reward;
- profile card and customization integration.

Defaults:

```text
xp_message_min=15
xp_message_max=25
xp_message_cooldown=60
xp_voice_per_minute=5
level threshold=100 * level²
message economy reward=2
```

QA pending.

---

# 10. ECONOMY / DAILY

Implemented in `cogs/economy.py` + `databases/economy.py`:

```text
/balance /daily /pay /rich
```

Supports 🪙 and 💎 persistence, message rewards, daily reward, transfers, ranking, settings and Admin Panel adjustment.

Rare currency has persistence but no complete earning/spending loop yet.
QA pending.

---

# 11. SHOP

Implemented/tested in `cogs/shop.py` + `databases/shop.py`.

```text
/shop /buy
```

Purchase flow validates item/role/duplicate, charges economy, assigns role, refunds on assignment failure and emits `shop_purchase` for achievements.

Runtime scenarios were tested on 2026-08-31. Regression QA remains pending.

---

# 12. QUESTS

Implemented in `cogs/quests.py` + `databases/quests.py`.

Daily quests:

```text
messages_10      → 10 messages → 50 🪙
voice_30         → 30 counted voice minutes → 100 🪙
voice_sessions_3 → 3 counted voice joins → 75 🪙
```

Persistent per guild/user/date, UTC date, capped progress, one reward claim, bot/webhook exclusion, AFK exclusion and voice recovery.

Known integration risk: completion and economy reward are separate persistence operations, creating a crash window.

---

# 13. ACHIEVEMENTS

Implemented in `cogs/achievements.py` + `databases/achievements.py`.

```text
messages_1000
voice_10h
rich_10000
shop_purchase
active_7_days
```

Progress reuses XP, VoiceStats and Economy sources. Shop purchase consumes the successful purchase event.

QA pending.

---

# 14. PROFILE

`/profile` generates a 1000×460 PNG using Pillow.

Current card data:

- avatar;
- display name;
- level/XP;
- total XP;
- coins/rare currency;
- message count;
- voice XP;
- achievement count;
- customized bio.

`/profile_customize` supports background color, accent color, short bio and reset. Persistence is guild/user scoped; colors are normalized; bio limit is 70 chars.

QA pending, especially long names and Unicode/Cyrillic fallback.

---

# 15. VOICE

VoiceStats in `cogs/logging/voice_stats.py` + `databases/voice_stats.py` tracks persistent total/channel seconds and active sessions.

Rules: AFK excluded, bots excluded, restart recovery, channel move handling and `on_ready` reconciliation.

Voice rooms in `cogs/user_cmd/create_voice.py` + `databases/voice_rooms.py` provide private/user-created rooms, controls, access/co-owner management, persistence and cleanup.

Both systems consume voice events and must remain separate.

QA pending.

---

# 16. VERIFICATION / MODERATION / TICKETS

Verification: arithmetic panel, role transition and owner synchronization. TEST role-create condition remains an audit candidate.

Moderation: `/warn`, `/timeout`, `/kick`, `/ban`, `/unban`, `/history`; persistent actions, settings, hierarchy checks, history, logging and hardened interaction callbacks.

Tickets: panel → modal → private thread → support → close confirmation → transcript → archive/lock. Persistent state and ready-time recovery are implemented.

QA pending for both.

Relevant historical fixes:

```text
4dea2a9d80e05672af8c5fd77dad12a1732db0f0 → role hierarchy
041dcb14bc4f2b9db0c01c0f1b687b03e6ce379c → ticket parent privacy
1755d209f4bacf859a9da3396fef94e252140f6 → ticket interaction timeout
64c80fb3ab96fcb954ae7524d799a57feaa0247f → moderation timeout
 d2c0509599b11359c1bc056dcac88c08deb7b141 → moderation modal COG reuse
3767d4b7406f61b73437250ecc577259cd589371 → verification persistent view
```

---

# 17. LOGGING / SERVER MANAGER / REBUILD

Logging groups:

```text
chat / guild / moderation / setup / system / voice
```

Runtime mapping uses `.logging_channels.json`, with `server_logs` compatibility. Full rebuild on 2026-09-01 completed without previous Unknown Channel / 404 logging errors.

Server Manager handles active guild targeting, managed permissions, synchronization, `/sync_server` and `/channel_create`.

Rebuild is owner-only, TEST-restricted, confirmed, mapping-aware and must preserve databases.

QA pending.

---

# 18. ADMIN / OWNER

Admin Panel centralizes persistent server settings and audits changes.

Owner/Owner Dump provide owner-level operational tools and are not part of the progression loop.

Sensitive-data exposure and owner protection remain QA candidates.

---

# 19. MINI-GAMES — CURRENT IMPLEMENTATION

Status: `IMPLEMENTED / QA NOT STARTED`

Files:

```text
cogs/minigames.py
databases/xp.py
config.py
```

Command:

```text
/minigame
```

Available skill-based games:

```text
Математика
Реакция
Память
```

Rules:

- one active game per guild/user;
- 30-second cooldown after completion/failure;
- only the initiating user can operate the buttons;
- expired games grant no reward;
- XP-disabled servers cannot start games;
- rewards reuse existing progression/economy storage;
- no gambling/betting mechanic;
- successful game gives `+15 XP` and, when economy is enabled, `+25 🪙`;
- XP level calculation reuses the existing XP COG rather than creating a second level system;
- memory sequence is hidden after three seconds;
- wrong answers end the game without reward.

`databases.xp.add_xp()` intentionally changes only total XP and does not inflate message/voice counters.

No runtime test has been performed yet. Do not mark this system QA passed until the later global QA phase.

---

# 20. FUTURE DISCORD ACTIVITIES

Status: `PLANNED`

Architecture target:

```text
Activity result
   ↓
trusted result integration
   ↓
XP / Economy / Quests / Achievements / Rankings / Profile
```

Before implementation define identity verification, guild verification, anti-cheat, reward calculation, idempotency, persistence and retry/failure semantics.

Do not fake external Activity results or mark an Activity integration complete without a real verified boundary.

---

# 21. FUTURE SOCIAL SYSTEMS

Status: `PLANNED`

Potential directions:

- social interactions;
- Friends;
- Romantic relationships.

They must fit the community/progression concept and must not introduce traditional RPG systems.

---

# 22. KNOWN TECHNICAL AUDIT ITEMS

High priority:

- quest completion/reward atomicity;
- moderation punishment vs logging failure;
- TEST-specific verification role-create condition;
- profile card long names and Unicode/Cyrillic fallback.

Medium/low:

- exact `active_7_days` semantics;
- voice achievement timing;
- legacy `get_roles.py`;
- disabled `reaction_logs.py`;
- guild-only command behavior;
- permissions/role hierarchy edge cases;
- interaction acknowledgement;
- duplicate event handling;
- mini-game reward integration and concurrency behavior.

Do not fix speculative issues without inspecting source/behavior first.

---

# 23. QA STATE

```text
Detailed QA started: NO
Current QA system: NONE
Current phase: IMPLEMENTATION FIRST
```

Already runtime verified:

- Verification basic flow and role hierarchy.
- Shop scenarios from 2026-08-31.
- Full rebuild/logging recovery on 2026-09-01 without previous Unknown Channel / 404 errors.
- Latest known Check workflow for logging-map baseline.

These do not equal full QA.

---

# 24. CURRENT DEVELOPMENT ORDER — USER OVERRIDE

The old roadmap said documentation → integration audit → QA → expansion. The user has explicitly changed the immediate priority.

Current order is:

```text
1. Implement remaining planned systems.
2. Integrate each new system with existing core where appropriate.
3. Keep PROJECT_STATE.md updated after every action.
4. Only when all planned implementation is complete:
   → Integration cleanup
   → Detailed QA, one system at a time
   → Full regression
   → Technical cleanup
```

Current implementation checkpoint:

```text
Core community/progression systems       → IMPLEMENTED
Mini-games                                → IMPLEMENTED (new in this checkpoint)
Discord Activities                         → PLANNED
Social / Friends / Romantic                → PLANNED
Full QA                                    → NOT STARTED
```

Next implementation target: continue with the next planned system, not QA.

---

# 25. IMPORTANT FIX HISTORY

```text
b90d279960ba0a83822afd00fdf2e2aa0c39db07 → profile customization DB
231fdab6110a6818028f4a2095d322be8de06884 → profile card customization
06af69d097c5a9e45638e7f3a3897528d94f5057 → profile customization command
55ac0a9043eed6cffc5e8d8d2fa60bf5fa020f21 → persistent actual voice time
f4321d9aa022b7085c19b510cf965d073d4ed544 → TEST/MAIN isolation
f19eedcf4f3bbc1476aabc9f17f6f355602e5590 → logging map compatibility
```

Recent current checkpoint commits:

```text
c80450ef6ecdb9fd8ec89ebf68cadbed4a50c1f0 → initial mini-games cog
92d518e7d6396cdab13d3bee7a10bd537b392a99 → generic XP persistence
566cae53fcfc640347e89311a02ae99d23f403ac → load mini-games COG
18a084f82a87128b2c23d6c76cf9aafbf69ab760 → mini-game interaction/memory hardening
```

---

# 26. NEW-CHAT CONTINUATION

On every new chat:

1. Read this file.
2. Inspect current GitHub `main`.
3. Identify the current implementation target.
4. Inspect connected systems.
5. Make the smallest necessary change.
6. Validate source/imports/references as far as available.
7. Update this file immediately after the action.
8. Continue from the new checkpoint.

Never claim runtime success without runtime evidence.
Never reset databases.
Never use abbreviated replacement code.
