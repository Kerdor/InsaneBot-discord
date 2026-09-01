# InsaneBot-discord — PROJECT STATE / MASTER ROADMAP

Repository: https://github.com/Kerdor/InsaneBot-discord
Branch: `main`
State date: 2026-09-01

> Persistent hand-off document. This is the main project hand-off and roadmap. Always inspect actual GitHub `main` before editing. Do not silently undo agreed decisions.

---

## 1. Working rules

- Act as a technical editor/developer.
- Inspect current repository before changes.
- Preserve architecture, names, order and formatting unless a change is necessary.
- Make the smallest necessary change.
- No unnecessary libraries or refactors.
- Never use `...` as an omitted-code placeholder.
- If a function changes for local replacement, provide the complete function.
- Check callers/references after code changes.
- Validate/test when practical.
- After every code/config fix, update this `PROJECT_STATE.md` with the fix, current state and relevant verification result before considering the task complete.
- Do not create branches; completed changes go directly to `main`.
- For runtime problems, inspect actual code and supplied logs before guessing.
- Prefer `БЫЛО → СТАЛО` for focused changes.
- Python indentation: 4 spaces.
- Do not destructively reset/restore runtime databases.

---

## 2. Product vision and binding decisions

InsaneBot is a Discord moderation/social/community bot with progression and game-like community systems.

### NOT A TRADITIONAL RPG — BINDING

Do **not** introduce:
- talismans;
- consumable combat items;
- loot boxes;
- RPG equipment/inventory;
- meaningless RPG statistics;
- a combat/equipment system merely for the sake of making the bot look like an RPG.

Progression is primarily community/social:
- activity;
- XP;
- levels;
- economy;
- profiles;
- achievements;
- quests;
- rankings;
- social interactions;
- friends/relationships;
- mini-games.

The shop is primarily for server/community benefits such as Discord roles, not RPG inventory.

### Explicitly removed / not currently planned

- **PvP — removed from roadmap.**
- **Collecting — removed from roadmap for now.**

These must not be reintroduced unless explicitly reconsidered by the user.

---

## 3. Master development roadmap

The project is divided into stages. `DONE` means implemented, not necessarily fully QA-approved. `QA PENDING` means the implementation exists but belongs to the later detailed QA phase.

### Stage A — Core infrastructure

1. Configuration and TEST/MAIN separation — `DONE`
2. SQLite persistence / database layer — `DONE / EXPANDING`
3. COG architecture and startup loading — `DONE`
4. Owner/admin infrastructure — `DONE`
5. Server manager / rebuild / synchronization — `DONE / QA PENDING`
6. Role hierarchy and permissions — `DONE / QA PENDING`
7. Development runner — `DONE / QA PENDING`
8. Persistent project state / hand-off documentation — `DONE`

### Stage B — Server, moderation and support systems

1. Verification — `IMPLEMENTED / LIVE VERIFIED`
2. Moderation — `IMPLEMENTED / QA PENDING`
3. Tickets — `IMPLEMENTED / QA PENDING`
4. Chat/member/server logging — `IMPLEMENTED / QA PENDING`
5. Voice statistics/logging — `IMPLEMENTED / QA PENDING`
6. System/setup logging — `IMPLEMENTED / QA PENDING`
7. Server rebuild and cache recovery — `IMPLEMENTED / QA PENDING`

### Stage C — Community progression

1. XP from chat — `IMPLEMENTED / QA PENDING`
2. XP from voice — `IMPLEMENTED / QA PENDING`
3. Levels — `IMPLEMENTED / QA PENDING`
4. Level-up notification — `IMPLEMENTED / QA PENDING`
5. XP ranking — `IMPLEMENTED / QA PENDING`
6. Voice-time statistics/ranking — `IMPLEMENTED / QA PENDING`
7. Economy — `IMPLEMENTED / QA PENDING`
8. Daily rewards — `IMPLEMENTED / QA PENDING`
9. Economy ranking — `IMPLEMENTED / QA PENDING`

### Stage D — Shop and server rewards

1. Public shop — `IMPLEMENTED / RUNTIME TESTED`
2. Item persistence — `IMPLEMENTED`
3. Item CRUD/configuration — `IMPLEMENTED / RUNTIME TESTED`
4. Discord-role purchases — `IMPLEMENTED / RUNTIME TESTED`
5. Balance validation — `IMPLEMENTED / RUNTIME TESTED`
6. Duplicate-role protection — `IMPLEMENTED / RUNTIME TESTED`
7. Failure refund — `IMPLEMENTED / RUNTIME TESTED`
8. Shop → achievements event integration — `IMPLEMENTED`
9. Visual shop UI redesign — `POSTPONED`

Future shop UI, only when explicitly requested:
- visual presentation improvements;
- 5 or 10 items per page;
- pagination;
- bottom navigation;
- `◀ 1/2 ▶` style controls.

Do not implement this redesign yet.

### Stage E — Quests

Current status: **MVP IMPLEMENTED / DETAILED QA PENDING**.

1. Persistent daily quest storage — `DONE`
2. `/quests` — `DONE`
3. Message quest — `DONE`
4. Voice-time quest — `DONE`
5. Voice-session quest — `DONE`
6. Automatic completion — `DONE`
7. One-time reward per completion — `DONE`
8. UTC daily reset model — `DONE`
9. Bot/webhook exclusion — `DONE`
10. AFK voice exclusion — `DONE`
11. Voice-session recovery after restart where persistent session data exists — `DONE`
12. Economy reward integration — `DONE`
13. Detailed runtime QA — `NOT STARTED BY DESIGN`

Current daily quests:
- `messages_10`: 10 messages → 50 🪙
- `voice_30`: 30 counted voice minutes → 100 🪙
- `voice_sessions_3`: 3 counted voice joins → 75 🪙

Progress is stored per guild/user/quest/date. Quest date is UTC. Completion is persisted and rewards are granted once.

### Stage F — Achievements

Current status: **MVP IMPLEMENTED / DETAILED QA PENDING**.

1. Persistent achievement storage — `DONE`
2. `/achievements` — `DONE`
3. Message achievement — `DONE`
4. Voice achievement — `DONE`
5. Economy/balance achievement — `DONE`
6. Shop-purchase achievement — `DONE`
7. Activity-days achievement — `DONE`
8. Permanent unlocks — `DONE`
9. Activity-day deduplication — `DONE`
10. Reuse existing XP/economy statistics instead of duplicating counters — `DONE`
11. Shop event integration — `DONE`
12. Detailed runtime QA — `NOT STARTED BY DESIGN`

Current achievements:
- `messages_1000`: 1000 messages
- `voice_10h`: 10 hours of counted voice activity
- `rich_10000`: 10 000 🪙 balance
- `shop_purchase`: first successful shop purchase
- `active_7_days`: activity on 7 different UTC dates

### Stage G — Profiles and profile cards

Current status: **GENERATED PNG CARD IMPLEMENTED / CUSTOMIZATION IMPLEMENTED / QA PENDING**.

1. Replace old `/profile` Embed with generated PNG card — `DONE`
2. Display Discord avatar — `DONE`
3. Display name — `DONE`
4. Display level — `DONE`
5. Display XP progress — `DONE`
6. Display total XP — `DONE`
7. Display coins — `DONE`
8. Display rare currency — `DONE`
9. Display message count — `DONE`
10. Display voice XP — `DONE`
11. Display achievement count — `DONE`
12. Persistent profile customization storage — `DONE`
13. `/profile_customize` — `DONE`
14. Background color customization — `DONE`
15. Accent color customization — `DONE`
16. Short bio — `DONE`
17. Reset customization — `DONE`
18. Preserve unspecified existing customization values — `DONE`
19. Apply customization to PNG renderer — `DONE`
20. Detailed runtime QA — `NOT STARTED BY DESIGN`

Customization defaults:
- background: `#181B23`
- accent: `#FFD75A`
- bio limit: 70 characters
- colors: `#RRGGBB`

Renderer: `utils/profile_card.py`.
Storage: `databases/profile_customization.py` / `databases/profile_customization.db`.
Pillow is required for PNG rendering and is present in `requirements.txt`.

### Stage H — Integration / feature-completion audit

This stage happens **before detailed QA**.

Check that all currently selected systems work together without changing their intended logic:

1. XP ↔ levels
2. XP/economy ↔ quests
3. XP/economy ↔ achievements
4. Shop ↔ economy
5. Shop ↔ achievements
6. Achievements ↔ profile card
7. Profile customization ↔ profile card
8. Voice tracking ↔ XP
9. Voice tracking ↔ quests
10. Voice tracking ↔ rankings/statistics
11. Daily rewards ↔ economy/achievements where applicable
12. Commands ↔ COG loading/sync
13. Rebuild ↔ persistent systems
14. Logging ↔ moderation/tickets/server events
15. Restart/recovery ↔ persistent state

The purpose is to catch missing imports, stale references, wrong event names, unloaded COGs, duplicate storage, and integration gaps before QA.

---

## 4. Current agreed implementation order

**This is the immediate work order. Do not start full QA before completing it.**

1. Quests — finish/inspect implementation
2. Achievements — finish/inspect implementation
3. Generated PNG Profile Card — finish/inspect integration
4. Profile customization — finish/inspect integration
5. Integration audit of all newly added functionality
6. Only after that: begin detailed QA, one system at a time

The current project is therefore in the **functionality-build stage**, not the final QA stage.

---

## 5. Current TEST environment

```text
ENVIRONMENT=test
MAIN_GUILD_ID=1217530337664434246
TEST_GUILD_ID=519209364280573954
TEST_GUILDS=[519209364280573954]
```

TEST guild: `Insane TEST` (`519209364280573954`).
Bot: `Insane#6907`.

MAIN guild is not connected during TEST runs; this is expected.

`config.py` separates TEST/production, loads `.server_map.json` and `.logging_channels.json`, validates/creates required directories, and includes the quests and achievements COGs.

---

## 6. Current COGs

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

`main.py` loads configured COGs and also includes `cogs.admin_panel` through the current loader arrangement.

Previously verified startup loaded the configured COGs successfully and reached Discord normally. A previous startup had 33 application commands in memory and Discord returned 33 registered TEST commands. After the new quests/achievements/profile-customization work, command sync still requires explicit runtime verification during QA.

Expected new commands:
```text
/quests
/achievements
/profile_customize
```

---

## 7. XP / Levels

Persistent SQLite XP system.

Implemented:
- chat XP;
- anti-spam cooldown;
- voice XP;
- AFK exclusion;
- persistent levels;
- `/level`;
- `/xp_ranking`;
- active voice-session recovery;
- level-up DM notification.

Defaults:
- message XP cooldown: 60 seconds;
- message XP: 15–25 XP;
- voice XP: 5 XP per completed voice minute;
- level threshold: `100 * level²`;
- eligible message also awards 2 🪙.

Status: `IMPLEMENTED / FULL QA PENDING`.

---

## 8. Economy

Persistent SQLite economy.

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

Admin economy flow is implemented and was runtime verified:
`/admin_panel → 💰 Экономика → UserSelect → amount`.

Verified there:
- user selection;
- give/remove coins;
- zero rejection;
- balance changes.

Negative-balance policy remains undecided. Do not silently change it.

Status: `IMPLEMENTED / FULL QA PENDING`.

---

## 9. Shop

Persistent `shop_items` storage contains:
- id;
- guild_id;
- name;
- description;
- price;
- role_id;
- enabled state.

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
- configure name;
- configure description;
- configure price;
- configure role.

Implemented:
- purchase validation;
- duplicate-role protection;
- balance checks;
- role assignment;
- refund on assignment failure;
- successful purchase event for achievements.

Runtime tests completed 2026-08-31:
- display;
- CRUD/edit;
- disable/delete;
- nonexistent item;
- insufficient balance;
- duplicate purchase;
- missing role;
- assignment failure/refund;
- successful role purchase.

Status: `FUNCTIONALLY TESTED / REGRESSION QA STILL REQUIRED`.

Shop UI redesign remains postponed.

---

## 10. Profile / Profile Card / Customization

`/profile` now generates a PNG profile card instead of the old Embed.

Renderer:
```text
utils/profile_card.py
```

The card currently contains:
- display name;
- Discord avatar;
- level;
- XP progress;
- total XP;
- coins;
- rare currency;
- message count;
- voice XP;
- unlocked achievement count.

Pillow was added to `requirements.txt` because PNG generation is required.

### Customization

Storage:
```text
databases/profile_customization.py
databases/profile_customization.db
```

Command:
```text
/profile_customize
```

Supported:
- background `#RRGGBB`;
- accent `#RRGGBB`;
- bio up to 70 characters;
- `reset=true`.

Storage is per guild/user. Existing values are preserved when only one setting changes.

The renderer validates/falls back to safe RGB values. The command validates hex colors before saving.

Status: `IMPLEMENTED / RUNTIME QA PENDING`.

---

## 11. Quests

Storage:
```text
databases/quests.py
databases/quests.db
```

COG:
```text
cogs/quests.py
```

Command:
```text
/quests
```

Current daily quests:
- `messages_10`: 10 messages → 50 🪙
- `voice_30`: 30 counted voice minutes → 100 🪙
- `voice_sessions_3`: 3 counted voice joins → 75 🪙

Rules:
- progress is per guild/user/quest/date;
- date is UTC;
- completion is persistent;
- reward is granted once;
- bot/webhook messages are excluded;
- AFK voice is excluded;
- persistent voice-session information is used for restart recovery when available;
- existing economy storage is reused for rewards;
- no additional library was required.

Status: `MVP IMPLEMENTED / DETAILED QA PENDING`.

Important: if implementation details are changed, inspect actual code first. Do not assume the state document is more current than GitHub source.

---

## 12. Achievements

Storage:
```text
databases/achievements.py
databases/achievements.db
```

COG:
```text
cogs/achievements.py
```

Command:
```text
/achievements
```

Current achievements:
- `messages_1000`: 1000 messages;
- `voice_10h`: 10 hours of counted voice activity;
- `rich_10000`: 10 000 🪙 balance;
- `shop_purchase`: first successful shop purchase;
- `active_7_days`: activity on 7 different UTC dates.

Rules:
- persistent per guild/user;
- unlocks are permanent;
- daily quest resets do not reset achievements;
- activity dates are deduplicated;
- message/voice/balance progress reuses existing XP/economy persistence;
- successful shop purchase dispatches the achievement event.

Status: `MVP IMPLEMENTED / DETAILED QA PENDING`.

---

## 13. Admin Panel

Command:
```text
/admin_panel
```

Restricted to admin/owner users.

Current areas:
- settings;
- logging;
- shop;
- economy balance management.

Persistent settings/audit history use:
```text
databases/settings.db
```

Status: `IMPLEMENTED / FULL QA PENDING`.

---

## 14. Moderation

Persistent moderation DB and commands:
```text
/ban
/kick
/timeout
/unban
/warn
```

Interaction timeout hardening commit:
`64c80fb3ab96fcb954ae7524d799a57feaa0247f`

Fixed:
- moderation commands defer before long Discord/API/DB/logging work;
- `ModerationTargetModal.callback()` defers before member lookup and moderation work;
- post-defer responses use followups.

Status: `CODE FIXED / RUNTIME QA PENDING`.

QA must include:
- `/warn`;
- `/timeout`;
- `/kick`;
- `/ban`;
- `/unban`;
- `/history`;
- moderation-panel modals;
- repeated use;
- logs/history correctness.

---

## 15. Tickets

Private Discord-thread ticket system.

Implemented:
- ticket creation;
- private threads;
- transcripts;
- recovery;
- persistent state;
- close flow.

Previously verified:
- creation works;
- ticket is a private Discord thread under `🎫・тикеты`;
- author/moderation access works;
- ordinary users cannot access an individual ticket;
- closing works and the ticket is not immediately deleted.

### Parent-channel privacy fix

Commit:
`041dcb14bc4f2b9db0c01c0f1b687b03e6ce379c`

`server_manager.apply_channel_overwrites()` now detects managed `🎫・тикеты` and applies `build_private_ticket_overwrites()` instead of normal support-category permissions.

After pull/rebuild or `/sync_server`, verify:
- ordinary users cannot see `🎫・тикеты`;
- `🎫・создать-тикет` remains public;
- ticket creation still works.

### Interaction timeout fixes

Tickets:
`1755d209f4bacf859a9da3396fef94e252140f6`

Rebuild command:
`a6257712676522a2e31d4bf20ea773a8f4d0ca5e`

Both defer before long DB/transcript/rebuild work and use followups where required.

Status: `IMPLEMENTED / QA PENDING`.

Do not redesign ticket logs into a forum/thread logging architecture unless explicitly requested.

---

## 16. Verification

Role hierarchy:
```text
Owner > Administrator > Moderator > Helper > Member > Not verified > @everyone
```

LIVE VERIFIED after `/rebuild`:
- ordinary user gets `Not verified`;
- owner gets `Owner` without `Not verified`;
- verification changes `Not verified → Member`.

Status: `LIVE VERIFIED / FINAL REGRESSION QA PENDING`.

---

## 17. Server Manager / Rebuild

Responsibilities:
- roles;
- channels;
- categories;
- permissions;
- server map;
- logging destinations;
- synchronization;
- rebuild.

Role hierarchy fix:
`4dea2a9d80e05672af8c5fd77dad12a1732db0f0`

Logging cache/rebuild fix:
`a0a515d24b81f3340bfb231e81513a5602068f8f`

A full rebuild on 2026-09-01 completed without `Unknown Channel` / 404 logging errors.

Status: `IMPLEMENTED / QA PENDING`.

---

## 18. Logging

COGs:
```text
cogs.logging.chat_logs
cogs.logging.guild_logs
cogs.logging.moderation_logs
cogs.logging.setup_logs
cogs.logging.voice_stats
cogs.logging.system_logs
```

Logging groups:
- messages/chat;
- members/server;
- moderation;
- setup;
- voice;
- system.

Reaction logging is disabled by default because it is noisy.

### Rebuild/logging cache fix

Commit:
`a0a515d24b81f3340bfb231e81513a5602068f8f`

Fixed stale cached logging destinations:
- validate cached destinations against current guild cache;
- invalidate deleted text channels;
- invalidate cached threads with missing parents;
- apply equivalent validation to fetched destinations.

Verification on 2026-09-01:
- full `/rebuild` completed without `Unknown Channel` / 404 logging errors.

Status: `IMPLEMENTED / FULL QA PENDING`.

---

## 19. Runner

`dev_runner.py` polls every 5 seconds.

Previously verified:
```text
pull → detect changes → stop child → restart child
```

Bot entrypoint:
```text
main.py
```

Development runner:
```text
dev_runner.py
```

Runner self-update is **not implemented**.

Status: `IMPLEMENTED / QA PENDING`.

---

## 20. Database inventory / persistence caution

Observed runtime databases:
```text
databases/Insane.sqlite3
databases/economy.db
databases/moderation.db
databases/settings.db
databases/tickets.db
databases/xp.db
databases/quests.db
databases/achievements.db
databases/profile_customization.db
```

Never destructively reset or restore these during normal debugging.

When changing database code:
- preserve existing data;
- inspect schema/current code first;
- avoid duplicate sources of truth;
- consider restart/persistence behavior;
- update this state document.

---

## 21. Integration audit before QA

Before starting detailed QA, inspect the actual codebase for these integration points:

### XP / economy
- message XP and coin reward happen exactly as intended;
- voice XP and voice statistics use the same counted-minute rules;
- AFK is consistently excluded.

### Quests
- message progress is connected to eligible messages;
- voice progress is finalized correctly;
- voice sessions are counted once per join;
- restart recovery does not double-count;
- daily UTC boundary works;
- rewards are granted exactly once.

### Achievements
- event listeners are loaded;
- event names match dispatchers;
- shop purchase unlock works only after successful purchase;
- balance/message/voice progress reads the correct existing persistence;
- activity-day counting is deduplicated;
- permanent unlocks remain permanent.

### Profile
- `/profile` uses current XP/economy data;
- achievement count comes from achievement persistence;
- avatar retrieval failure does not crash rendering;
- customization is correctly scoped per guild/user;
- reset restores defaults;
- partial updates preserve unspecified settings;
- generated PNG is actually attached/sent.

### Commands / COGs
- new COGs load at startup;
- slash commands synchronize;
- no stale imports/references remain;
- no duplicate command registration;
- no missing event listener due to loader order.

---

## 22. Detailed QA strategy — AFTER functionality build

**User decision: finish all selected functionality first, then test one system at a time in detail.**

Do not interrupt the functionality-build stage with the full QA campaign.

For each system test at minimum:
1. normal scenario;
2. invalid/bad input;
3. permissions and role restrictions;
4. edge cases;
5. repeated execution/double-clicks;
6. persistence/restart;
7. interaction acknowledgement/timeouts;
8. Discord permission failures;
9. API/DB failures where practical;
10. logs;
11. rebuild/sync interactions;
12. race/concurrency-sensitive paths.

### Agreed QA order

1. Tickets and recent timeout/privacy fixes
2. Moderation
3. Verification
4. XP / levels
5. Economy / daily / pay / rich
6. Shop
7. Quests
8. Achievements
9. Profile / profile card / customization
10. Rankings / voice statistics
11. Admin Panel
12. Rebuild / Server Manager
13. Logging groups
14. Runner
15. Full regression

### Final technical audit after QA

Inspect the entire project for:
- dead code;
- stale references;
- unused functions/imports;
- broken callers;
- async correctness;
- interaction acknowledgement;
- Discord API usage;
- permissions;
- role hierarchy;
- channels/categories/threads;
- config separation;
- database consistency;
- persistence/restart behavior;
- runner behavior;
- COG loading architecture;
- exception handling;
- race conditions;
- duplicate event handling;
- accidental destructive operations;
- logging failures;
- command synchronization;
- unnecessary dependencies;
- documentation accuracy.

---

## 23. Future roadmap after current functionality stage

These features are accepted future directions but are **not part of the current implementation order**.

### Mini-games

Planned direction:
- mini-games inside Discord;
- Discord Activities where appropriate;
- integration with XP;
- integration with economy;
- integration with quests;
- integration with achievements;
- integration with rankings.

Do not build this before the current functionality stage and QA unless explicitly reordered.

### Social interactions

Planned:
- social interaction system;
- user-to-user interactions;
- integration with community progression where appropriate.

### Friends

Planned:
- friend requests;
- friend list;
- friendship state;
- future social integrations.

### Romantic relationships

Planned:
- relationship mechanics;
- mutual relationship state;
- future social/profile integrations.

### Future profile/shop expansion

Possible later work:
- richer profile-card visual design;
- more customization options;
- redesigned shop UI/pagination.

These are intentionally later than the current functionality and QA cycle.

---

## 24. Explicit non-goals / do not reintroduce

Unless the user explicitly changes the product decision, do **not** add:
- PvP;
- collecting systems;
- talismans;
- combat consumables;
- loot boxes;
- RPG equipment/inventory;
- meaningless RPG stats;
- traditional RPG progression unrelated to community activity.

Do not turn the project into a traditional RPG.

---

## 25. Current status snapshot — 2026-09-01

### Implemented
- TEST/MAIN configuration separation;
- COG architecture;
- server management/rebuild;
- verification;
- tickets;
- moderation;
- logging groups;
- runner;
- XP/levels;
- economy;
- daily rewards;
- rankings;
- shop;
- quests MVP;
- achievements MVP;
- generated PNG profile card;
- persistent profile customization;
- `/profile_customize`;
- shop purchase → achievement event integration.

### Runtime verified / partially verified
- shop functionality: substantial runtime test completed;
- verification: live verified;
- admin economy flow: runtime verified;
- rebuild/logging cache fix: verified by full rebuild;
- runner pull/detect/restart cycle: previously verified.

### Code-fixed but runtime QA pending
- moderation interaction timeout hardening;
- tickets interaction timeout hardening;
- ticket parent privacy fix;
- quests;
- achievements;
- profile card;
- profile customization;
- newly integrated feature paths.

### Current phase

**FUNCTIONALITY-BUILD STAGE.**

Immediate goal:
> Finish and integration-audit all currently selected functionality.

Only after that:
> Start detailed QA, one system at a time, using the agreed QA order.

Only after QA:
> Perform the final technical audit and then move to the future roadmap.

---

## 26. Important historical fixes

- `4dea2a9d80e05672af8c5fd77dad12a1732db0f0` — role hierarchy fix.
- `041dcb14bc4f2b9db0c01c0f1b687b03e6ce379c` — ticket parent privacy fix.
- `1755d209f4bacf859a9da3396fef94e252140f6` — ticket interaction timeout hardening.
- `a6257712676522a2e31d4bf20ea773a8f4d0ca5e` — `/rebuild_test_server` interaction timeout hardening.
- `64c80fb3ab96fcb954ae7524d799a57feaa0247f` — moderation interaction timeout hardening.
- `a0a515d24b81f3340bfb231e81513a5602068f8f` — stale logging destination/cache invalidation.

Recent feature work also added:
- quests persistence/COG;
- achievements persistence/COG;
- PNG profile-card rendering;
- Pillow dependency;
- persistent profile customization;
- profile customization command and renderer integration;
- shop purchase achievement event integration.

---

## 27. Handoff rule for the next chat

When continuing this project from a new chat:

1. Read this file first.
2. Treat the roadmap and binding product decisions above as the current agreed plan.
3. Inspect actual GitHub `main` source before making assumptions about implementation status.
4. Continue from the **Current agreed implementation order**, not from an invented alternative roadmap.
5. Do not start detailed QA until the functionality-build stage and integration audit are complete.
6. After every fix, update this file with the new state and verification.
7. Preserve the user's technical editing rules and existing architecture.
