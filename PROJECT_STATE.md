# InsaneBot-discord — Project State

Repository: https://github.com/Kerdor/InsaneBot-discord
Branch: `main`
Current HEAD: `89e232ac81b5075fd3a86ebddd5ecf609b2edded`
Current HEAD message: `Add local development auto-pull runner`
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

The configured MAIN guild ID was not found during the TEST run. This was not a crash and is expected for the current TEST environment.

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

### Current verified state

The user subsequently ran the bot and supplied a complete startup log at approximately 03:03 on 2026-08-31.

All configured COGs loaded successfully, including `cogs.shop` and `cogs.admin_panel`.

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
2026-08-31 03:03:03,023 - cogs.tickets - WARNING - Канал create_ticket не настроен для guild=519209364280573954
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

## 12. ADMIN ECONOMY MANAGEMENT — CURRENT DEVELOPMENT

Administrator balance management was added to `/admin_panel`.

### Current intended UI

The economy section now uses a real Discord `UserSelect` instead of a text field for the user.

Flow:

```text
/admin_panel
→ 💰 Экономика
→ [ Выберите пользователя ▼ ]
→ select a server member
```

After selection, the view displays:

```text
Выбран пользователь: @user
Текущий баланс: N 🪙

Теперь нажмите 💰 Изменить баланс и укажите сумму.
```

Then the modal contains only:

```text
Сумма (+ выдать / - снять)
```

Positive value gives coins.
Negative value removes coins.
Zero is rejected.

The selected user ID is kept by the view, so no manual ID or `@mention` parsing is required.

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

### Runtime status

The old text-input UI was shown by the user before the UserSelect change.

The latest UserSelect implementation has **not yet been runtime-tested after the final pull/restart**.

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

### Bug found during runtime testing

The user created a test role item, initially lacked enough money, then reduced the price and bought the item twice.

Observed old behavior:

- the purchase was accepted twice;
- no Discord role appeared;
- money could therefore be spent without the expected role reward;
- duplicate role purchases were possible.

This exposed a critical flaw in the old purchase flow: money was deducted before the role assignment was safely validated, and there was no duplicate-role protection.

### Shop fix

`ad99f0a3cc880ec7ce781b7e4353ea712c0eb091` — `Fix shop role purchase validation`

The current fix in `cogs/shop.py`:

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

The user-facing error explicitly tells the user when role assignment failed and that money was returned.

### Important status

The fix is committed, but **the post-fix role-assignment flow has not yet been verified by a fresh local test**.

Therefore the shop remains **in end-to-end testing**, not fully stable.

### Required shop tests

After pulling the current `main`:

1. verify the test item contains the correct Discord role ID;
2. verify the bot's highest role is above the shop role;
3. use admin economy management to give the test user enough coins;
4. run `/shop`;
5. run `/buy <item_id>`;
6. verify exactly one deduction;
7. verify the role appears on the user;
8. repeat `/buy <item_id>` and verify duplicate purchase is rejected;
9. test a missing/deleted role and verify no money is lost;
10. test insufficient balance;
11. test disabled item;
12. test deleted/nonexistent item;
13. test role hierarchy/permission failure and verify automatic refund.

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

## 18. LOCAL STARTUP TEST — VERIFIED 2026-08-31 03:03

The user ran the bot locally with Python 3.12 using `main.py`.

The complete supplied startup log showed:

```text
[CONFIG] ENVIRONMENT=test
[CONFIG] MAIN_GUILD_ID=1217530337664434246
[CONFIG] TEST_GUILD_ID=519209364280573954
[CONFIG] TEST_GUILDS=[519209364280573954]
```

All configured COGs loaded successfully, including:

```text
cogs.shop
cogs.admin_panel
```

The bot connected successfully:

```text
Bot connected to Discord
Bot Insane#6907 is ready
Guilds: 1
```

TEST synchronization succeeded:

```text
[SYNC] Команд в памяти перед overwrite: 33
[SYNC] Discord вернул зарегистрированных команд: 33
```

System logging was activated:

```text
[STARTUP] Discord system logging активирован
```

XP and voice active sessions were recovered successfully.

Only startup warning:

```text
Канал create_ticket не настроен для guild=519209364280573954
```

No startup exception was reported.

### What this proves

- configuration loads;
- bot connects;
- all configured COGs load;
- shop COG loads;
- admin panel COG loads;
- `/shop`, `/buy`, `/shop_admin` synchronize to TEST;
- bot reaches ready state;
- active voice sessions recover.

### What this does not prove

It does not prove every command works end-to-end.

Specifically, after the later commits the following still require fresh runtime verification:

- shop role assignment after `ad99f0a`;
- duplicate shop purchase rejection;
- admin economy UserSelect after `c9e0b114`;
- `dev_runner.py` after `89e232ac`.

---

## 19. RECENT COMMIT HISTORY — EXACT HAND-OFF

Recent development sequence:

### `77e0bd8...`

**Load shop and admin panel cogs**

Added `cogs.shop` to the configured COG list after discovering that shop commands were not loading.

### `989a7f654ae475612c99f0e8f2c22d8607de229d`

**Add economy balance management to admin panel**

Added administrator balance management.

### `b5ff3f19a8bfbe0b341c3f61d511e0684ea1fd73`

**Allow economy admin balance changes using @mention**

Temporarily changed the economy user input to mention-style text.

### `ad99f0a3cc880ec7ce781b7e4353ea712c0eb091`

**Fix shop role purchase validation**

Added role existence checks, duplicate-role checks and refunds when role assignment fails.

### `c9e0b11492bf4a60f4b5e7c107dcdc3a54cecc6a`

**Replace economy admin input with Discord user selector**

Replaced manual user/mention input with Discord `UserSelect`, shows current balance, and leaves only the amount in the modal.

### `89e232ac81b5075fd3a86ebddd5ecf609b2edded`

**Add local development auto-pull runner**

Added `dev_runner.py`.

This is the current HEAD before the PROJECT_STATE refresh commit.

---

## 20. `dev_runner.py` — LOCAL AUTO-UPDATE / RESTART

File:

```text
dev_runner.py
```

Purpose:

- start `main.py`;
- periodically execute `git pull`;
- detect whether HEAD changed;
- if a new commit was pulled, stop the current bot process and start it again;
- allow Ctrl+C to stop both runner and child bot.

Current polling interval:

```text
POLL_INTERVAL = 10
```

Current flow:

```text
start dev_runner.py
        ↓
start main.py
        ↓
wait 10 seconds
        ↓
git pull
        ↓
HEAD changed?
   ┌────┴────┐
  no        yes
   ↓          ↓
wait       stop bot
              ↓
           start bot
```

If `git pull` fails, the runner prints the output and keeps the existing bot process running.

If the child bot exits by itself, the runner currently reports the exit code and returns rather than automatically restarting it.

The runner uses `sys.executable`, so it launches `main.py` with the same Python interpreter used to launch the runner.

### Important status

The file is committed but **has not yet been runtime-tested by the user**.

The intended local launcher is:

```bash
C:\Users\nik_s\AppData\Local\Programs\Python\Python312\python.exe dev_runner.py
```

Do not run a separate `main.py` at the same time, because the runner starts it itself.

---

## 21. CURRENT KNOWN ISSUES / TODO

### CRITICAL — Shop role assignment must be retested

The old behavior was broken and was fixed in `ad99f0a`.

Need runtime proof that:

- correct role ID is configured;
- role is below the bot's highest role;
- `/buy` deducts once;
- role is assigned;
- duplicate purchase is rejected;
- role assignment failure refunds money.

### CRITICAL — Economy UserSelect must be retested

The new `c9e0b114` implementation needs to be pulled and tested in Discord.

Expected flow:

```text
/admin_panel
→ 💰 Экономика
→ Выберите пользователя
→ выбрать себя
→ увидеть текущий баланс
→ 💰 Изменить баланс
→ ввести amount
```

### HIGH — Verify `dev_runner.py`

Run it locally and verify:

1. it starts `main.py`;
2. it checks Git every 10 seconds;
3. a new commit is pulled;
4. old bot process stops cleanly;
5. new bot starts;
6. no duplicate bot process is created;
7. Ctrl+C stops runner and child bot.

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

## 22. RECOMMENDED NEXT SESSION START

Unless the user requests a different task, continue in this order.

### Step 1 — Sync local repository

```bash
git pull
```

The current code HEAD before this state-file refresh was:

```text
89e232ac81b5075fd3a86ebddd5ecf609b2edded
```

After this PROJECT_STATE update, the repository HEAD will additionally contain the state-file refresh commit. The exact new HEAD must be checked rather than guessed.

### Step 2 — Test the new local runner

Run:

```bash
C:\Users\nik_s\AppData\Local\Programs\Python\Python312\python.exe dev_runner.py
```

Confirm startup is clean.

### Step 3 — Test admin economy

In TEST Discord:

```text
/admin_panel
→ 💰 Экономика
→ Выберите пользователя
→ выбрать себя
→ проверить текущий баланс
→ 💰 Изменить баланс
→ ввести 100
```

Then run `/balance` and confirm the result.

### Step 4 — Test shop

Use the newly issued coins:

```text
/shop
/buy <item_id>
```

Confirm role assignment and one-time balance deduction.

Then repeat `/buy <item_id>` and confirm duplicate purchase is blocked.

### Step 5 — Continue development from actual results

If a test fails, inspect the actual current code and fix the smallest necessary part. Do not blindly add workarounds.

---

## 23. IMPORTANT FACTS TO NOT FORGET

- Current branch: `main`.
- Before this state-file update, current HEAD was `89e232ac`.
- Current local environment: TEST.
- TEST guild: `519209364280573954` (`Insane TEST`).
- Bot: `Insane#6907`.
- `cogs.shop` is in `BotConfig.COGS` and was verified loading.
- `/shop`, `/buy`, `/shop_admin` were verified synchronized in TEST in the supplied 03:03 startup.
- Shop is under end-to-end testing, not declared fully stable.
- A real shop bug was found: purchases could occur without role assignment and duplicate purchases were possible. This was fixed in `ad99f0a`, but the fix still needs runtime verification.
- Admin economy management exists.
- The admin economy UI now uses a Discord UserSelect instead of an ID/mention text field.
- `dev_runner.py` exists and polls Git every 10 seconds, but it still needs local runtime verification.
- TEST currently warns that `create_ticket` is not configured.
- The bot is not an RPG project.
- Do not undo the existing architecture or add unrelated libraries/refactors.
- Always inspect current GitHub code before making the next change.
