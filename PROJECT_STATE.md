# InsaneBot-discord — Project State

Repository: https://github.com/Kerdor/InsaneBot-discord
Branch: `main`
Last known repository commit: `77e0bd8090e3bba5ae2e003f437d9781521861d9` (`Load shop and admin panel cogs`)
State date: 2026-08-31

> **Purpose of this file:** this is the persistent hand-off/context document for future chats. A new chat must read this file first and then inspect the actual current repository before making changes. This document records product decisions, architecture, implementation history, current test state, known issues, and the immediate next steps. Do not silently undo decisions marked as agreed.

---

## 1. How to work on this project

The user wants the assistant to act as a **technical editor/developer**:

- Inspect the actual current GitHub `main` before editing. Do not rely on old snippets if the repository can be checked.
- Continue directly from the current state; do not repeatedly ask questions that have already been settled here.
- If an error is caused by the user's local changes, the user explicitly allows changing those parts when necessary.
- Preserve the existing architecture, names, function order and formatting unless a change is necessary.
- Make the smallest necessary change.
- Do not add unnecessary libraries, abstractions, checks or unrelated refactors.
- Never use `...` as a placeholder for omitted code.
- When reporting a changed function, provide the full ready-to-replace function, not a partial fragment.
- Check callers/references after changing or removing methods, variables, settings or modules.
- Validate/test changes whenever practical.
- Completed changes should be committed directly to `main` unless the user explicitly asks otherwise.
- When a local/runtime problem is reported, investigate the actual current repository rather than guessing.
- The user prefers a concise explanation of what is wrong, followed by the concrete change and commit.

### Code-editing style requested by the user

1. Prefer `БЫЛО → СТАЛО` when explaining a focused change.
2. Keep original indentation and formatting.
3. Python indentation is 4 spaces.
4. Do not rewrite a huge file when only a few functions need changing.
5. Keep existing logic unless the requested feature/fix requires changing it.
6. If several issues exist, list them and mark critical ones.

---

## 2. Product concept

InsaneBot is a Discord moderation/social/community bot with optional progression and game-like systems.

### Critical product decision: NOT an RPG system

The bot is **not** intended to become a traditional RPG.

There will be no invented RPG mechanics such as:

- talismans of luck;
- energy drinks;
- consumable combat items;
- loot-box style mechanics;
- an RPG equipment/inventory system;
- RPG stats merely for the sake of having RPG stats.

If a future system needs an item/collectible mechanic, it must be explicitly designed and agreed first.

The intended progression is primarily community/social: activity, XP, levels, economy, profiles, achievements, relationships, mini-games, rankings, etc.

---

## 3. Planned systems / product roadmap

The project is implemented incrementally. Do not attempt to build everything in one giant refactor.

Planned systems currently include:

1. Levels and XP — **implemented**
2. Economy — **implemented, expanding**
3. Shop — **partially implemented**
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

Do not interpret this list as a requirement to implement all RPG-like ideas. The no-RPG decision remains binding.

---

## 4. Repository/runtime configuration

Current local test run showed:

```text
[CONFIG] ENVIRONMENT=test
[CONFIG] MAIN_GUILD_ID=1217530337664434246
[CONFIG] TEST_GUILD_ID=519209364280573954
[CONFIG] TEST_GUILDS=[519209364280573954]
```

The bot was running locally as:

```text
Insane#6907
Bot ID: 1329863697358782504
```

The test guild is:

```text
Insane TEST
ID: 519209364280573954
```

The configured main guild ID was not found during the reported local test. This is expected for the current TEST environment and is not itself a crash.

---

## 5. Current COG loading state

The local test was started with the following configured COG list:

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
cogs.admin_panel
```

A subsequent repository fix added the missing shop cog to the configured list:

```text
cogs.shop
cogs.admin_panel
```

Commit:

`77e0bd8090e3bba5ae2e003f437d9781521861d9` — `Load shop and admin panel cogs`

This was done because the user's local startup log showed `/shop` and `/buy` were missing from the loaded application commands even though shop code had been added.

### IMPORTANT: first action after pulling

The user should run:

```bash
git pull
```

and restart the bot. The next test must verify that `cogs.shop` actually loads and that the shop commands appear in the synchronized TEST guild commands.

---

## 6. Application-command synchronization

The bot has explicit TEST guild synchronization/overwrite logic.

The user's reported startup showed:

```text
[SYNC] Начинаем явную синхронизацию TEST: guild_id=519209364280573954
[SYNC] Команд в памяти перед overwrite: 30
```

At that moment the registered commands included:

```text
admin_panel
balance
ban
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

The shop commands were absent because `cogs.shop` was not in the loaded COG configuration at that time.

After commit `77e0bd8`, the next startup should be used to verify the corrected command set. Do not claim shop commands are registered until the actual runtime log confirms it.

---

## 7. Major systems already implemented

### 7.1 Tickets

Private-thread ticket system exists with:

- ticket creation;
- transcripts;
- recovery;
- persistent ticket-related state.

Current known warning from the local run:

```text
[cogs.tickets] Канал create_ticket не настроен для guild=519209364280573954
```

This is a configuration warning, not a bot startup crash. It means the TEST guild does not currently have the `create_ticket` channel configured, so ticket creation/panel behavior needs to be configured/tested later.

Do not treat this warning as a failure of the entire bot.

---

### 7.2 Moderation

Moderation system exists with:

- persistent moderation database;
- slash commands;
- persistent moderation panel;
- moderation logging.

Known commands from the test run include:

```text
ban
kick
timeout
unban
warn
```

---

### 7.3 Logging

Logging is implemented as separate logical COGs:

- `cogs.logging.chat_logs`
- `cogs.logging.guild_logs`
- `cogs.logging.moderation_logs`
- `cogs.logging.setup_logs`
- `cogs.logging.voice_stats`
- `cogs.logging.system_logs`

Logical log groups:

- 💬 messages
- 👤 members/server
- 🛡️ moderation
- 📁 server/setup
- 🔊 voice
- 🤖 system

Reaction logging implementation exists but is disabled by default because it is noisy.

The admin panel can configure logging destinations per log type.

The user previously considered putting chat logs into a forum with log threads; do not change the existing logging architecture solely for that idea unless explicitly requested again. The current system already separates log types and is being expanded incrementally.

---

## 8. XP / levels

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

Current settings/behavior recorded in the project:

- message XP cooldown: **60 seconds**;
- message XP: **15–25 XP** per eligible message;
- voice XP: **5 XP per completed voice minute**;
- AFK channels excluded.

Level thresholds currently use cumulative `100 * level²`:

- level 1 starts at 0 XP;
- level 2 at 100 XP;
- level 3 at 400 XP;
- level 4 at 900 XP;
- etc.

The XP implementation also calculates level changes and can notify the user by DM when they level up.

### Message economy reward

A successful XP-eligible message also gives the normal economy reward.

Current default:

```text
1 XP-eligible message = XP + 2 🪙
```

The economy message reward uses the same eligibility/cooldown concept as message XP, so spam does not generate unlimited coins.

This is an intentional design decision.

---

## 9. Economy

The economy is persistent and stored in SQLite.

There are two currencies:

### Normal currency

Regular server coins, currently represented as 🪙.

Sources include:

- XP-eligible messages;
- daily reward;
- future shop/social/activity systems.

### Rare currency

There is also a rare special currency.

Important decision:

- it has **no real-money purchase**;
- it is intentionally difficult to obtain;
- intended sources include every 5th level, achievements, daily quests and other special activities once those systems exist.

Do not add real-money monetization to the rare currency without an explicit new decision.

### Current economy commands

Implemented:

- `/balance`
- `/daily`
- `/pay`
- `/rich`

Behavior:

- `/balance` shows normal and rare currency;
- `/daily` awards the configured daily amount and enforces a cooldown;
- `/pay` transfers normal coins between users;
- bots cannot receive transfers;
- users cannot pay themselves;
- `/rich` shows a top-10 balance ranking.

Economy can be disabled by the persistent server setting `economy_enabled`.

---

## 10. Profile

Basic `/profile` has been implemented.

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

The profile uses the same persistent XP/economy data, so there should not be a separate duplicate profile database for these values.

Future work:

- visual profile cards;
- customization;
- achievements;
- social information;
- friends/relationships;
- additional statistics.

---

## 11. Shop — CURRENT DEVELOPMENT AREA

The shop is the most recent feature being implemented.

### Shop database

A new `databases/shop.py` was added.

It contains a persistent `shop_items` table with fields conceptually equivalent to:

- `id`
- `guild_id`
- `name`
- `description`
- `price`
- `role_id`
- `enabled`

Implemented database operations include:

- initialize shop table;
- get enabled items;
- get a specific enabled item;
- create an item;
- purchase an item and deduct normal currency.

The purchase logic checks balance before deduction.

### Shop COG

A `cogs.shop` module was added with the public shop/purchase functionality.

The intended public commands are:

- `/shop`
- `/buy <item id>`

When a shop item has an associated Discord role, successful purchase should grant that role.

### Shop administration

Shop administration was also added to the admin-panel direction, with the intended controls:

- create item;
- edit item;
- enable/disable item;
- delete item;
- view item state;
- configure item name/description/price/role.

However, **the current local runtime has not yet verified this end-to-end**.

The immediate goal is not to invent an RPG inventory. The shop is intended to sell community/server benefits such as roles or future explicitly approved cosmetic/social features.

### Critical next verification

After pulling the latest `main`:

1. start the bot;
2. verify `cogs.shop` loads without import errors;
3. verify `/shop` and `/buy` are registered in TEST;
4. open `/admin_panel`;
5. verify the shop management section exists and opens;
6. create a cheap test role item;
7. run `/shop`;
8. buy it with a test account;
9. verify coins are deducted once;
10. verify the role is granted;
11. repeat purchase and verify the intended duplicate-purchase behavior;
12. test disabled/deleted items;
13. test insufficient balance;
14. test permissions.

Only after these tests should the shop be considered stable.

---

## 12. Admin panel

The admin panel is intended to become the central configuration/management UI so the user can control the bot without manually editing code/database values.

Current command:

```text
/admin_panel
```

It is restricted to the owner/administrator according to the current implementation.

Existing/targeted sections include:

- ⚙️ Settings — XP/economy settings;
- 📋 Logging — logging destination configuration;
- 🛒 Shop — shop management;
- future moderation/ticket/general controls.

Persistent settings live in:

```text
databases/settings.db
```

Changes are recorded in a settings audit history (`settings_audit`).

Important product principle:

> The admin panel should gradually become the central place to configure the bot. Do not hardcode values that are intended to be server-configurable.

Do not create settings for systems that do not exist yet.

---

## 13. Existing configuration philosophy

The bot uses a persistent settings database for server-level configuration.

Already discussed/implemented settings include XP and economy controls such as:

- XP enabled/disabled;
- message XP range;
- message XP cooldown;
- voice XP per minute;
- economy enabled/disabled;
- message economy reward;
- daily economy reward;
- logging destinations.

Exact current defaults should always be read from the actual repository/settings code before changing them.

Do not assume an old default is still current if the repository has changed.

---

## 14. Local startup test — IMPORTANT CURRENT STATE

The user ran the bot locally on 2026-08-31 around 02:56 and supplied the complete startup log.

The bot successfully:

- loaded all listed COGs without startup exceptions;
- connected to Discord;
- became ready as `Insane#6907`;
- found the TEST guild;
- performed explicit TEST command synchronization;
- registered 30 commands at that point;
- activated Discord system logging;
- recovered active voice sessions.

Representative successful startup lines:

```text
[STARTUP] Все расширения успешно загружены
Bot connected to Discord
Bot Insane#6907 is ready
Guilds: 1
[STARTUP] Discord system logging активирован
```

The critical issue discovered from that run was that `cogs.shop` was not in the configured COG list, so shop commands could not load.

That was fixed in commit:

`77e0bd8` — `Load shop and admin panel cogs`

### Do not forget

The supplied log is from **before** that configuration fix. A future chat must not claim the fix is runtime-verified until the user runs the updated code.

---

## 15. Known current warnings/issues

### ISSUE A — Shop runtime verification pending

**Status:** configuration fix committed; runtime verification pending.

Fix already committed:

`77e0bd8` — add `cogs.shop` to loaded COG configuration.

Next action: `git pull`, restart, inspect COG and command lists.

### ISSUE B — Ticket channel not configured in TEST

Current warning:

```text
Канал create_ticket не настроен для guild=519209364280573954
```

**Status:** configuration issue, not startup failure.

Needs to be configured/tested later.

### ISSUE C — Main guild not present in TEST environment

Current output:

```text
[MAIN] НЕ НАЙДЕН (ID: 1217530337664434246)
[TEST] Insane TEST (ID: 519209364280573954)
```

**Status:** expected/acceptable for TEST environment unless the user later wants the main guild connected in this environment.

---

## 16. Testing strategy agreed with the user

The user explicitly asked when the bot should be launched and tested.

Decision:

**Do not wait until the entire project is finished.**

Test in stages:

1. implement a coherent feature block;
2. validate code and obvious integration problems;
3. run the bot locally on the TEST guild;
4. manually test actual Discord interactions;
5. fix real runtime/API/permission/state issues;
6. continue development;
7. later perform a full integrated test and stabilization pass;
8. only then consider the current release production-ready.

This is important because waiting until the end would make integration failures harder to isolate.

The current project has now reached the point where local integrated testing is appropriate, especially for shop/admin/XP/economy/profile interactions.

---

## 17. Suggested immediate development sequence

Continue from the actual `main`, not from assumptions.

### Step 1 — FIRST

Verify the latest shop COG fix in the user's local environment.

Expected after `git pull` + restart:

```text
[COG] Загружаем: cogs.shop
[COG] OK: cogs.shop
```

and shop commands should appear in the application-command list/synchronization output.

### Step 2

Test shop end-to-end on TEST guild.

### Step 3

Fix any real shop/runtime issues found.

### Step 4

Finish the admin panel around existing systems, especially:

- shop;
- moderation;
- tickets;
- XP/economy settings;
- logging destinations.

Do not add fake settings for future systems.

### Step 5

Perform a broader integrated test:

- `/profile`
- `/level`
- `/xp_ranking`
- `/balance`
- `/daily`
- `/pay`
- `/rich`
- `/shop`
- `/buy`
- `/admin_panel`
- moderation commands;
- ticket creation;
- logging.

### Step 6

After the foundation is stable, continue with social/profile systems:

- profile cards/customization;
- friends;
- social interactions;
- romantic relationships.

Then move into achievements/quests/mini-games/PvP/collections/cosmetics according to future design decisions.

---

## 18. Historical implementation milestones

The recent implementation sequence was approximately:

1. XP/economy foundations were added.
2. Message rewards were connected to XP eligibility/cooldown.
3. `/profile` was added using XP + economy data.
4. Economy commands `/balance`, `/daily`, `/pay`, `/rich` were expanded.
5. Shop database was added.
6. Public shop commands were added.
7. Shop administration was integrated toward the admin panel.
8. Runtime test revealed `cogs.shop` was missing from the configured COG list.
9. Commit `77e0bd8` added `cogs.shop` to the COG loading list.
10. Current state: **pull/restart/test that fix, then continue from actual results.**

Do not repeat these implementation steps unless inspection shows they are missing or broken in the actual repository.

---

## 19. Important user expectations about commits

The user expects completed repository changes to actually be committed, not merely described.

A previous situation occurred where a change was described but the GitHub update did not actually succeed. The user explicitly questioned why it was not committed and stated that local/user changes can be modified when necessary.

Therefore:

- after implementing a change, verify the GitHub write succeeded;
- report the resulting commit;
- do not say “готово/закоммичено” unless the repository operation actually succeeded;
- if a write fails, say so clearly and retry correctly when possible.

---

## 20. Repository/source-of-truth rule

The actual GitHub repository is the source of truth for code.

This file is the source of truth for project decisions and hand-off context, but it can become stale. Therefore a new chat should:

1. read `PROJECT_STATE.md`;
2. inspect the current `main` and relevant files;
3. compare the current implementation against this state;
4. continue from the actual code.

Never blindly paste an old function over a newer repository version.

---

## 21. Do not accidentally reintroduce removed concepts

Never reintroduce:

- talismans of luck;
- energy drinks as an RPG resource;
- RPG equipment;
- arbitrary RPG consumables;
- a generic RPG inventory just because a shop exists.

The shop currently exists as a **server/community economy feature**, with Discord roles as one concrete purchasable benefit.

A future collectible/cosmetic system may exist, but it must be designed separately and explicitly.

---

## 22. Definition of “done” for the current foundation

The current foundation should not be called production-ready yet.

Before that claim, verify:

- clean startup;
- all intended COGs load;
- all intended slash commands synchronize;
- XP works after restart;
- voice XP works and recovers correctly;
- economy persists;
- daily cooldown persists correctly;
- transfers cannot create/lose money incorrectly;
- shop purchases are atomic enough for the current SQLite design;
- shop role grants work;
- admin permissions work;
- settings persist;
- logging destinations work;
- tickets work after configuration;
- moderation commands work;
- no stale references/imports remain;
- no duplicate command registration occurs;
- test guild behavior is stable.

Only after that should a broader production/release pass be performed.

---

## 23. Current one-line handoff

**CURRENT POSITION:** The bot successfully starts in TEST and the XP/economy/profile/admin foundations are present; shop database/public/admin functionality has been added, but the first local test revealed `cogs.shop` was missing from the configured COG list, which was fixed in `77e0bd8`. The immediate next action is `git pull`, restart, verify `cogs.shop` and `/shop`/`/buy`, then perform the first real integrated shop/admin test and fix whatever runtime issues appear. Continue committing directly to `main`. No RPG mechanics. The user allows modifying their changes when necessary.
