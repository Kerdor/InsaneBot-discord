# InsaneBot-discord — Project State

Repository: https://github.com/Kerdor/InsaneBot-discord
Branch: `main`
Current code HEAD before this state refresh: `54b1bd4`
Current code HEAD message: `fix: restore admin panel and UserSelect fix`
State date: 2026-08-31

> **Purpose:** persistent hand-off/context document for future chats. A new chat must read this file first and then inspect the actual current repository before making changes. This document records product decisions, architecture, implemented systems, exact recent changes, runtime verification, known issues, and the next development steps. Do not silently undo decisions marked as agreed.

---

## 1. HOW TO WORK ON THIS PROJECT

The user wants the assistant to act as a **technical editor/developer**.

Mandatory rules:

- Inspect the actual current GitHub `main` before editing.
- Do not rely on old snippets when the repository can be checked.
- Continue directly from the current state; do not repeatedly ask for information already documented here.
- If a problem is caused by the user's local changes, the user allows changing the affected parts when necessary.
- Preserve existing architecture, names, function order and formatting unless a change is necessary.
- Make the smallest necessary change.
- Do not add unnecessary libraries, abstractions, checks or unrelated refactors.
- **Never use `...` as a placeholder for omitted code.**
- If a function is changed and the user needs to edit locally, provide the full ready-to-replace function.
- Check callers/references after changing or removing methods, variables, settings or modules.
- Validate/test changes whenever practical.
- Completed changes should normally be committed directly to `main` unless the user explicitly asks otherwise.
- When a runtime problem is reported, investigate the actual current repository and supplied runtime log before guessing.
- The user prefers a concise explanation of the problem followed by the concrete change and commit.

### Code-editing style

1. Prefer `БЫЛО → СТАЛО` for focused changes.
2. Keep original indentation and formatting.
3. Python indentation is 4 spaces.
4. Do not rewrite a huge file when only a few functions need changing.
5. Keep existing logic unless the requested feature/fix requires changing it.
6. If several issues exist, list them and mark them critical/high/medium.

---

## 2. PRODUCT CONCEPT

InsaneBot is a Discord moderation/social/community bot with progression and game-like community systems.

### CRITICAL DECISION: NOT A TRADITIONAL RPG

The project must **not** become a traditional RPG.

Do not invent mechanics such as:

- talismans of luck;
- energy drinks;
- consumable combat items;
- loot-box mechanics;
- RPG equipment/inventory systems;
- RPG stats merely for the sake of having RPG stats.

If a future system needs an item/collectible mechanic, it must be explicitly designed and agreed first.

The intended progression is primarily community/social:

- activity;
- XP;
- levels;
- economy;
- profiles;
- achievements;
- relationships;
- mini-games;
- rankings;
- future social systems.

The shop is currently intended mainly for server/community benefits such as Discord roles, not as an RPG inventory.

---

## 3. PRODUCT ROADMAP

Current roadmap/status:

1. Levels and XP — **implemented**
2. Economy — **implemented, expanding**
3. Shop — **implemented in code, currently undergoing end-to-end testing**
4. Profiles — **basic `/profile` implemented; profile cards/customization later**
5. Daily rewards — **implemented**
6. Quests — **planned**
7. PvP — **planned**
8. Mini-games — **planned**
9. Rankings — **XP and economy rankings implemented; more later**
10. Achievements — **planned**
11. Collecting — **planned**
12. Profile customization — **planned**
13. Social interactions — **planned**
14. Voice-time rankings — **implemented**
15. Friends — **planned**
16. Romantic relationships — **planned**
17. Tickets — **implemented**
18. Moderation — **implemented**
19. Logging — **implemented/expanding**

Do not interpret the roadmap as permission to add unrelated RPG mechanics. The no-RPG decision is binding.

---

## 4. CURRENT REPOSITORY / RUNTIME CONFIGURATION

Current local TEST configuration reported by the user:

```text
[CONFIG] ENVIRONMENT=test
[CONFIG] MAIN_GUILD_ID=1217530337664434246
[CONFIG] TEST_GUILD_ID=519209364280573954
[CONFIG] TEST_GUILDS=[519209364280573954]
```

Bot during the reported local run:

```text
Name: Insane#6907
Bot ID: 1329863697358782504
```

Connected guild during the run:

```text
Insane TEST
ID: 519209364280573954
```

The configured MAIN guild ID was not found during the TEST run. This is expected for the current TEST environment.

The current `config.py` confirms:

- `ENVIRONMENT` accepts `test` or `production`;
- TEST mode requires `TEST_GUILD_ID` and uses `[TEST_GUILD_ID]` as `TEST_GUILDS`;
- production mode requires `MAIN_GUILD_ID`;
- `.server_map.json` is loaded for TEST role/channel mapping;
- `.logging_channels.json` is loaded for logging destinations;
- database/assets/log directories are validated/created;
- `cogs.shop` and `cogs.admin_panel` are in `BotConfig.COGS`.

---

## 5. CURRENT COG LIST

The actual current `config.py` COG list is:

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
cogs.admin_panel
```

`cogs.shop` was previously missing and caused shop commands not to load. That problem was fixed in `77e0bd8`.

---

## 6. APPLICATION COMMAND SYNCHRONIZATION

The bot explicitly synchronizes/overwrites commands for the TEST guild.

### Previous broken state

Before `cogs.shop` was loaded, the runtime had 30 commands and `/shop` + `/buy` were absent.

### Verified state

A supplied startup log showed all configured COGs loading, including `cogs.shop` and `cogs.admin_panel`.

The runtime had **33 application commands in memory** and Discord returned **33 registered TEST commands** after overwrite.

Commands verified in that run:

```text
admin_panel
balance
ban
buy
channel_create
chatlog
daily
dump_server
history
kick
level
load
logsetup
modlog
pay
profile
rebuild_test_server
reload
restart
rich
serverlog
shop
shop_admin
sync_server
systemlog
ticket_close
timeout
unban
unload
voice
voice_ranking
warn
xp_ranking
```

Representative lines:

```text
[STARTUP] Все расширения успешно загружены
[SYNC] Команд в памяти перед overwrite: 33
[SYNC] Discord вернул зарегистрированных команд: 33
[STARTUP] Discord system logging активирован
```

Therefore the old missing-shop-COG problem is **verified fixed**.

---

## 7. TICKETS

Private-thread ticket system exists with:

- ticket creation;
- transcripts;
- recovery;
- persistent ticket-related state.

Known TEST warning:

```text
Канал create_ticket не настроен для guild=519209364280573954
```

This is a configuration warning, not a startup crash.

The TEST guild currently does not have the `create_ticket` channel configured. Ticket creation/panel behavior still needs a separate configuration/test pass.

---

## 8. MODERATION

Moderation is implemented with:

- persistent moderation database;
- slash commands;
- persistent moderation panel;
- moderation logging.

Known commands:

```text
/ban
/kick
/timeout
/unban
/warn
```

---

## 9. LOGGING

Logging is split into:

```text
cogs.logging.chat_logs
cogs.logging.guild_logs
cogs.logging.moderation_logs
cogs.logging.setup_logs
cogs.logging.voice_stats
cogs.logging.system_logs
```

Logical groups:

- 💬 messages;
- 👤 members/server;
- 🛡️ moderation;
- 📁 server/setup;
- 🔊 voice;
- 🤖 system.

Reaction logging exists but is disabled by default because it is noisy.

The admin panel can configure logging destinations.

The user previously considered turning chat logs into a forum with log threads. **Do not change the current logging architecture solely because of that old idea** unless explicitly requested again.

`config.py` supports persisted logging channel/forum mappings via `.logging_channels.json`.

---

## 10. XP / LEVELS

XP is persistent and stored in SQLite.

Implemented:

- chat message XP;
- per-user anti-spam message cooldown;
- random XP per eligible message;
- voice XP;
- AFK voice exclusion;
- persistent levels;
- `/level`;
- `/xp_ranking`;
- recovery of active voice XP sessions after restart using persisted voice sessions.

Recorded behavior/defaults:

- message XP cooldown: **60 seconds**;
- message XP: **15–25 XP** per eligible message;
- voice XP: **5 XP per completed voice minute**;
- AFK channels excluded.

Level thresholds use cumulative `100 * level²`:

- level 1: 0 XP;
- level 2: 100 XP;
- level 3: 400 XP;
- level 4: 900 XP;
- etc.

The XP system calculates level changes and can notify the user by DM on level-up.

### Message economy reward

An XP-eligible message also gives normal economy currency.

Recorded default:

```text
1 XP-eligible message = XP + 2 🪙
```

The economy message reward follows the same eligibility/cooldown concept as message XP so spam does not generate unlimited coins.

---

## 11. ECONOMY

Economy is persistent and stored in SQLite.

There are two currencies.

### Normal currency

Regular server coins, represented as 🪙.

Known sources:

- XP-eligible messages;
- daily reward;
- future shop/social/activity systems.

### Rare currency

Special rare currency, represented as 💎.

Binding decisions:

- no real-money purchase;
- intentionally difficult to obtain;
- intended future sources include every 5th level, achievements, daily quests and other special activities.

Do not add real-money monetization to the rare currency without an explicit new decision.

### Economy commands

Implemented:

```text
/balance
/daily
/pay
/rich
```

Behavior:

- `/balance` shows normal and rare currency;
- `/daily` awards the configured daily amount and enforces cooldown;
- `/pay` transfers normal coins;
- bots cannot receive transfers;
- users cannot pay themselves;
- `/rich` shows a top-10 balance ranking.

Economy can be disabled with the persistent `economy_enabled` server setting.

---

## 12. ADMIN ECONOMY MANAGEMENT — TESTED

Administrator balance management is part of `/admin_panel`.

### Current UI

The economy section uses a real Discord `UserSelect` instead of a text field for the user.

Flow:

```text
/admin_panel
→ 💰 Экономика
→ [ Выберите пользователя ▼ ]
→ select a server member
```

After selection, the view displays the selected user and current balance.

The modal contains:

```text
Сумма (+ выдать / - снять)
```

Positive value gives coins.
Negative value removes coins.
Zero is rejected.

The selected user ID is kept by the view, so no manual ID or `@mention` parsing is required.

### Runtime tests completed 2026-08-31

The UserSelect flow was tested after the final repair.

Verified:

- selecting a user works;
- giving coins works;
- removing coins works;
- zero amount is rejected;
- balance changes are applied correctly.

The user confirmed that money was successfully issued and removed through the admin economy panel.

### Important remaining economy question

The current admin balance logic may allow a negative balance if an administrator removes more coins than the user has. This has **not** yet been tested/decided as a required rule.

If economy design requires balances to be non-negative, add that as a separate explicit change rather than silently changing behavior during unrelated testing.

### Implementation history

`989a7f654ae475612c99f0e8f2c22d8607de229d` — `Add economy balance management to admin panel`

Added:

- `show_economy()`;
- `set_balance()`;
- `AdminEconomyView`;
- `EconomyBalanceModal`;
- `💰 Экономика` button;
- before/after balance logging.

`b5ff3f19a8bfbe0b341c3f61d511e0684ea1fd73` — `Allow economy admin balance changes using @mention`

Temporarily changed the user field to mention-style text input.

`c9e0b11492bf4a60f4b5e7c107dcdc3a54cecc6a` — `Replace economy admin input with Discord user selector`

Replaced the mention text field with `disnake.ui.user_select`, shows the selected member's current balance, and leaves only the amount in the modal.

`118e653` — `fix: handle disnake UserSelect member value`

Fixed the UserSelect handler so it correctly handles the selected Discord member object instead of assuming the select value is a raw integer ID.

---

## 13. SHOP — CURRENT DEVELOPMENT AREA

The shop is the main feature currently being stabilized.

### Shop database

`databases/shop.py` contains a persistent `shop_items` table with fields equivalent to:

- `id`;
- `guild_id`;
- `name`;
- `description`;
- `price`;
- `role_id`;
- `enabled`.

Database operations include:

- initialize shop table;
- get enabled items;
- get a specific enabled item;
- create item;
- purchase item and deduct normal currency;
- update item;
- enable/disable item;
- delete item;
- list all items for administration.

### Public shop

`cogs.shop` provides:

```text
/shop
/buy <item_id>
```

Role-item flow is intended to be:

1. resolve the enabled item;
2. validate the associated Discord role if configured;
3. reject the purchase if the user already has the role;
4. check available coins;
5. process the purchase;
6. grant the role;
7. confirm the purchase.

### Shop administration

`/shop_admin` and the admin panel provide management for shop items.

Intended controls include:

- create item;
- edit item;
- enable/disable item;
- delete item;
- view item state;
- configure name;
- configure description;
- configure price;
- configure role.

### Previous shop bug

The old purchase flow allowed purchases to be accepted without the expected role and allowed duplicate purchases.

The critical flaw was that money could be deducted before role assignment was safely validated, and there was no duplicate-role protection.

### Shop fix

`ad99f0a3cc880ec7ce781b7e4353ea712c0eb091` — `Fix shop role purchase validation`

The fix in `cogs/shop.py`:

- imports `add_balance` for refunds;
- imports `get_item`;
- verifies the item exists/is available;
- resolves the configured role from the current guild;
- rejects a missing role before purchase;
- rejects a user who already has the role;
- performs the purchase after those checks;
- attempts to assign the role;
- on `disnake.Forbidden`, refunds the item price;
- on `disnake.HTTPException`, logs the error and refunds the item price.

### Runtime tests completed 2026-08-31

The current TEST shop was opened with `/shop` and showed:

```text
#1 · Тестовая роль — 1 🪙
```

The user then executed `/buy 1`.

Observed:

- purchase was accepted;
- balance decreased from 499 to 498;
- bot reported successful purchase;
- the role initially appeared not to be present, but after checking the server role setup the user confirmed that **the role is actually being granted**;
- role hierarchy was correct: the shop role is below the bot role.

Therefore the normal role purchase path is now **verified working**.

### Current next shop test

The role is currently already owned by the test user.

Next test must be:

```text
/buy 1
```

again, without manually removing the role.

Expected:

- purchase rejected because the user already has the role;
- balance remains unchanged;
- no duplicate charge occurs.

After that, test:

1. insufficient balance;
2. disabled item;
3. deleted/nonexistent item;
4. missing/deleted Discord role and verify no money is lost;
5. role hierarchy/permission failure and verify automatic refund;
6. shop admin CRUD and permission behavior.

Shop remains **under end-to-end testing**, not declared fully stable.

---

## 14. PROFILE

Basic `/profile` is implemented.

It currently shows:

- user display name/avatar;
- ⭐ level;
- XP progress toward next level;
- 💰 normal balance;
- 💎 rare currency;
- 💬 message count;
- 🔊 voice XP;
- 📊 total XP.

`/profile [member]` can show another member's profile.

Profile values should use the existing XP/economy persistence rather than a duplicate profile database.

Future work:

- visual profile cards;
- customization;
- achievements;
- social information;
- friends/relationships;
- additional statistics.

---

## 15. ADMIN PANEL — CURRENT ARCHITECTURE

`/admin_panel` is intended to become the central configuration/management UI.

It is restricted by the current `_allowed()` admin/owner check.

Current sections include/are being expanded around:

- ⚙️ Settings — XP/economy/server settings;
- 📋 Logging — logging destination configuration;
- 🛒 Shop — shop management;
- 💰 Экономика — administrator balance management;
- future moderation/ticket/general controls.

Persistent server settings live in:

```text
databases/settings.db
```

Settings changes are recorded in settings audit history (`settings_audit`).

### Product principle

The admin panel should gradually become the central place to configure the bot without manually editing source code/database values.

Do not hardcode values that are intended to be server-configurable.

Do not create settings for systems that do not exist yet.

---

## 16. CONFIGURATION PHILOSOPHY

The bot uses persistent server-level settings rather than relying exclusively on constants.

Known configurable areas include:

- XP enabled/disabled;
- message XP range;
- message XP cooldown;
- voice XP per minute;
- economy enabled/disabled;
- message economy reward;
- daily economy reward;
- logging destinations.

Exact current defaults must always be read from the actual repository/settings code before changing them.

Do not assume an old default remains current if the repository changed.

---

## 17. SERVER MAP / PERSISTENT CONFIG FILES

Current `config.py` supports:

### `.server_map.json`

Used in TEST mode to dynamically load server-specific role/channel IDs.

Required role names:

```text
Owner
Administrator
Moderator
Helper
Member
Not verified
```

Required channel names:

```text
create_voice
verification
create_ticket
tickets
game_panel
moderation_panel
chat_logs
guild_logs
moderation_logs
system_logs
voice_logs
logs
```

If the required map is incomplete, hardcoded fallback values remain in `BotConfig`.

### `.logging_channels.json`

Used for persisted logging destinations and forum/thread IDs.

`config.py` can:

- load logging destinations;
- set all logging/forum mappings;
- set a single logging channel;
- retrieve a logging channel.

---

## 18. LOCAL STARTUP / RUNNER TESTING — VERIFIED 2026-08-31

The user launched:

```text
C:\Users\nik_s\AppData\Local\Programs\Python\Python312\python.exe dev_runner.py
```

The runner printed:

```text
[RUNNER] Автообновление включено. Проверка Git каждые 10 сек.
[RUNNER] Для остановки нажмите Ctrl+C.
[RUNNER] Запуск бота...
```

The first restart after commit `54b1bd4` exposed a regression caused by an earlier bad edit: `cogs.admin_panel` was missing its `setup()` function and the bot aborted startup.

This was immediately repaired in:

`54b1bd4` — `fix: restore admin panel and UserSelect fix`

After the repair the bot was able to run far enough for the user to successfully test Admin Economy and Shop in Discord.

Therefore:

- `dev_runner.py` exists;
- it launches the bot;
- the repaired bot starts successfully enough for Discord testing;
- auto-pull polling is configured for 10 seconds.

### Still not fully proven

The complete automatic update cycle itself has not yet been deliberately tested end-to-end with a new commit while the runner is already running.

Required dedicated runner test:

1. start `dev_runner.py`;
2. make/commit a harmless test change on GitHub;
3. wait for the 10-second poll;
4. verify `git pull` detects the new commit;
5. verify the child bot is stopped;
6. verify the child bot is started again exactly once;
7. verify no duplicate bot process exists;
8. verify Ctrl+C stops runner and child bot.

Do not run a separate `main.py` at the same time as the runner.

---

## 19. LOCAL GIT STATE OBSERVED 2026-08-31

The user ran:

```text
git status
git branch -vv
git log --oneline --decorate -5
git remote -v
```

The local branch reported:

```text
* main 54b1bd4 [origin/main] fix: restore admin panel and UserSelect fix
```

and:

```text
Your branch is up to date with 'origin/main'.
```

Recent local log:

```text
54b1bd4 (HEAD -> main, origin/main, origin/HEAD) fix: restore admin panel and UserSelect fix
118e653 fix: handle disnake UserSelect member value
0ec71e9 Update PROJECT_STATE with current development state
89e232a Add local development auto-pull runner
c9e0b11 Replace economy admin input with Discord user selector
```

Local working tree contained runtime-generated/local changes:

```text
modified:   databases/Insane.sqlite3
modified:   dev_runner.py

Untracked files:
    databases/economy.db
    databases/moderation.db
    databases/settings.db
    databases/tickets.db
    databases/xp.db
```

These are local runtime/database changes and **must not be discarded blindly**.

GitHub Desktop displayed a message saying there were 172 commits to pull, but command-line Git simultaneously reported `main` was up to date with `origin/main`. Therefore the user was explicitly told **not to press Pull Origin or discard local changes** until the discrepancy is understood. Treat the command-line Git state as the authoritative local check unless GitHub Desktop is separately investigated.

---

## 20. CURRENT KNOWN ISSUES / TODO

### CRITICAL — Finish shop end-to-end testing

Normal role purchase is now verified.

Next immediate test:

```text
/buy 1
```

while the user already owns the role.

Expected: purchase rejected and balance unchanged.

Then test insufficient balance, disabled item, nonexistent item, missing role, role hierarchy failure/refund, and shop admin CRUD.

### HIGH — Verify `dev_runner.py` automatic update cycle

Startup and normal Discord testing are working after the admin panel repair, but the automatic **pull → detect changed HEAD → restart child bot** cycle still needs a deliberate end-to-end test.

### MEDIUM — Decide/verify negative balances

The user asked whether the balance can go negative when an administrator removes more coins than available. Current behavior has not been changed. Decide whether balances should be clamped at zero or whether negative balances are intentionally allowed.

### MEDIUM — Configure/test TEST ticket channel

Current warning:

```text
Канал create_ticket не настроен для guild=519209364280573954
```

Configure the test server mapping/channel and test ticket creation/recovery.

### MEDIUM — Finish shop administration testing

Verify all CRUD operations and permission behavior.

### FUTURE — Expand admin panel

Move appropriate server configuration into the admin panel incrementally without creating unnecessary settings.

### FUTURE — Profile card/customization

Basic `/profile` exists. Visual customization is later.

### FUTURE — Planned social/game systems

Quests, PvP, mini-games, achievements, collecting, friends and relationships remain planned, but should be implemented incrementally after current systems are stable.

---

## 21. RECOMMENDED NEXT SESSION START

Unless the user requests a different task, continue in this order.

### Step 1 — Confirm local sync

```bash
git status
git branch -vv
git log --oneline --decorate -5
```

Do not discard runtime database changes.

### Step 2 — Continue shop testing

The immediate next action is:

```text
/buy 1
```

with the test role already owned.

### Step 3 — Finish shop negative/error cases

Test:

- insufficient balance;
- disabled item;
- nonexistent item;
- missing/deleted Discord role;
- role hierarchy/permission failure with refund;
- shop admin CRUD.

### Step 4 — Deliberately test `dev_runner.py` auto-restart

Use a harmless commit while the runner is already running and verify the complete automatic update cycle.

### Step 5 — Test tickets

Resolve the `create_ticket` TEST configuration warning and test ticket creation/recovery.

### Step 6 — Continue development from actual results

If a test fails, inspect the actual current code and fix the smallest necessary part. Do not blindly add workarounds.

---

## 22. IMPORTANT FACTS TO NOT FORGET

- Current branch: `main`.
- Before this state-file refresh, current code HEAD was `54b1bd4`.
- Current local environment: TEST.
- TEST guild: `519209364280573954` (`Insane TEST`).
- Bot: `Insane#6907`.
- `cogs.shop` is in `BotConfig.COGS` and was verified loading.
- `/shop`, `/buy`, `/shop_admin` were verified synchronized in TEST.
- Admin Economy UserSelect is now runtime-tested and works for selecting users, adding money, removing money, and rejecting zero.
- A shop test item `#1 · Тестовая роль` costs 1 🪙.
- Normal shop role purchase is runtime-tested and the role is confirmed to be granted.
- The immediate next shop test is duplicate purchase rejection while the role is already owned.
- Shop is still under end-to-end testing and is not declared fully stable.
- `dev_runner.py` polls Git every 10 seconds and launches the bot, but its full automatic pull/restart cycle still needs a deliberate test.
- The bot is not an RPG project.
- Do not undo the existing architecture or add unrelated libraries/refactors.
- Local runtime databases are present and must not be discarded blindly.
- Always inspect current GitHub code before making the next change.
