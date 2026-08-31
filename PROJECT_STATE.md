# InsaneBot-discord — Project State

Repository: https://github.com/Kerdor/InsaneBot-discord
Branch: `main`
State date: 2026-09-01

> Persistent hand-off document for future chats. Always inspect the actual current GitHub `main` before editing. Do not silently undo agreed decisions.

---

## 1. WORKING RULES

The user wants the assistant to act as a technical editor/developer.

- Inspect actual current GitHub `main` before making changes.
- Preserve architecture, names, function order and formatting unless a change is necessary.
- Make the smallest necessary change.
- Do not add unnecessary libraries, abstractions or unrelated refactors.
- Never use `...` as an omitted-code placeholder.
- If a function is changed for local replacement, provide the complete function.
- Check callers/references after changing or removing code.
- Validate/test changes whenever practical.
- Normally commit completed changes directly to `main`.
- For runtime problems, inspect the current repository and supplied logs before guessing.
- Prefer `БЫЛО → СТАЛО` for focused code changes.
- Python indentation: 4 spaces.
- If multiple issues exist, list them with severity.

---

## 2. PRODUCT DECISION

InsaneBot is a Discord moderation/social/community bot with progression and game-like community systems.

### NOT A TRADITIONAL RPG

This is binding. Do not introduce RPG mechanics such as talismans, consumable combat items, loot boxes, RPG equipment/inventory or meaningless RPG stats. The intended progression is community/social: activity, XP, levels, economy, profiles, achievements, relationships, mini-games, rankings and future social systems.

The shop is primarily for server/community benefits such as Discord roles, not an RPG inventory.

---

## 3. ROADMAP

1. Levels/XP — implemented
2. Economy — implemented/expanding
3. Shop — implemented and runtime-tested; remaining edge/admin tests are non-blocking cleanup
4. Profiles — basic `/profile` implemented
5. Daily rewards — implemented
6. Quests — planned
7. PvP — planned
8. Mini-games — planned
9. Rankings — XP/economy/voice implemented
10. Achievements — planned
11. Collecting — planned
12. Profile customization — planned
13. Social interactions — planned
14. Voice-time rankings — implemented
15. Friends — planned
16. Romantic relationships — planned
17. Tickets — implemented, TEST configuration still needs testing
18. Moderation — implemented
19. Logging — implemented/expanding

Do not interpret the roadmap as permission to add unrelated RPG mechanics.

---

## 4. CURRENT TEST RUNTIME

```text
ENVIRONMENT=test
MAIN_GUILD_ID=1217530337664434246
TEST_GUILD_ID=519209364280573954
TEST_GUILDS=[519209364280573954]
```

TEST guild: `Insane TEST` (`519209364280573954`).
Bot during latest run: `Insane#6907` (`1329863697358782504`).

The configured MAIN guild is not connected during TEST runs; this is expected.

`config.py` uses TEST_GUILD_ID for TEST_GUILDS, loads `.server_map.json` and `.logging_channels.json`, validates/creates database/assets/log directories, and includes `cogs.shop` and `cogs.admin_panel`.

---

## 5. CURRENT COGS

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

`cogs.shop` was previously missing and caused `/shop` and `/buy` not to load. Fixed in `77e0bd8`.

---

## 6. COMMAND SYNC — VERIFIED

Latest supplied startup log showed:

- all configured COGs loaded successfully;
- **33 application commands in memory**;
- Discord returned **33 registered TEST commands** after overwrite;
- `/shop`, `/buy`, `/shop_admin` and `/admin_panel` are present;
- Discord connection and startup succeeded.

The 33 registered commands were:

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

The previous missing-shop-COG problem is verified fixed.

---

## 7. XP / LEVELS

Persistent SQLite XP system.

Implemented:
- chat XP with per-user anti-spam cooldown;
- voice XP and AFK exclusion;
- persistent levels;
- `/level`;
- `/xp_ranking`;
- active voice session recovery after restart;
- DM notification on level-up.

Recorded defaults:
- message XP cooldown: 60 seconds;
- message XP: 15–25 XP;
- voice XP: 5 XP per completed voice minute;
- cumulative level threshold: `100 * level²`.

An XP-eligible message also awards normal economy currency; recorded default is **2 🪙 per eligible message**, using the same anti-spam eligibility concept.

---

## 8. ECONOMY

Persistent SQLite economy.

Normal currency: 🪙.
Rare currency: 💎.

Binding rare-currency decisions:
- no real-money purchase;
- intentionally difficult to obtain;
- future sources may include every 5th level, achievements, daily quests and other special activities.

Commands:
```text
/balance
/daily
/pay
/rich
```

`/pay` transfers normal coins; bots cannot receive transfers and users cannot pay themselves. Economy can be disabled through persistent server settings.

### Admin economy — VERIFIED

`/admin_panel → 💰 Экономика → UserSelect → amount`.

The UserSelect flow was runtime-tested successfully:
- selecting a user works;
- giving coins works;
- removing coins works;
- zero amount is rejected;
- balance changes are applied correctly.

Potential negative balances when removing more than available remain an explicit undecided design question. Do not silently change this behavior during unrelated work.

Relevant history:
- `989a7f6` — add economy balance management;
- `b5ff3f1` — temporary mention input;
- `c9e0b11` — replace with Discord UserSelect;
- `118e653` — fix UserSelect member handling.

---

## 9. SHOP — TESTED

`databases/shop.py` stores persistent shop items with id, guild_id, name, description, price, role_id and enabled state.

Public commands:
```text
/shop
/buy <item_id>
```

Admin controls include create/edit/enable/disable/delete and configuration of name, description, price and role.

### Purchase safety fix

`ad99f0a` — `Fix shop role purchase validation`.

The current purchase flow:
1. resolves an enabled item;
2. validates configured Discord role;
3. rejects duplicate role ownership;
4. checks coins;
5. purchases/deducts;
6. attempts role assignment;
7. refunds on `disnake.Forbidden` or `disnake.HTTPException`.

### Runtime shop tests completed 2026-08-31

The TEST shop was opened and CRUD behavior was exercised.

Observed/verified:
- shop items display correctly;
- item editing changes name/description/price/role display as expected;
- disabling item #3 removes it from public `/shop`;
- deleting item #3 removes it from public `/shop`;
- buying a nonexistent/deleted item returns `❌ Товар не найден или больше недоступен.`;
- insufficient balance returns the expected error;
- duplicate purchase is rejected with `❌ У тебя уже есть эта роль. Повторная покупка невозможна.`;
- missing role returns `❌ Роль товара не найдена на этом сервере. Покупка отменена.`;
- role assignment failure returns the warning and money is refunded;
- normal role purchase was verified: balance decreased by the price and the Discord role was actually granted after checking the server;
- shop admin CRUD behavior used during testing works.

Therefore the previously critical shop purchase bug is fixed and the main end-to-end flow is verified.

The old PROJECT_STATE listed duplicate purchase and other negative tests as future work; **that is stale and must not be repeated as if untested**.

Remaining shop cleanup only if needed:
- broader admin permission/UI coverage;
- explicitly decide negative-balance policy for admin economy (not shop-specific);
- any new regression tests requested by the user.

---

## 10. PROFILE

Basic `/profile` is implemented and shows display name/avatar, level, XP progress, normal/rare currency, message count, voice XP and total XP. It can show another member.

Future: visual profile cards, customization, achievements and social information.

---

## 11. ADMIN PANEL

`/admin_panel` is the central management UI and is admin/owner restricted.

Current areas include:
- settings;
- logging;
- shop;
- economy balance management;
- future controls.

Persistent server settings are in `databases/settings.db`; settings changes are audited in `settings_audit`.

Do not create settings for systems that do not exist yet.

---

## 12. LOGGING

Logging COGs:
```text
cogs.logging.chat_logs
cogs.logging.guild_logs
cogs.logging.moderation_logs
cogs.logging.setup_logs
cogs.logging.voice_stats
cogs.logging.system_logs
```

Groups: messages, members/server, moderation, setup, voice, system.

Reaction logging is disabled by default because it is noisy.

`.logging_channels.json` persists logging destinations/forum/thread IDs. Do not redesign logging into a forum/thread architecture unless the user explicitly requests it.

---

## 13. MODERATION

Implemented persistent moderation DB, slash commands, persistent moderation panel and moderation logging.

Commands:
```text
/ban
/kick
/timeout
/unban
/warn
```

---

## 14. TICKETS

Private-thread ticket system exists with ticket creation, transcripts, recovery and persistent ticket state.

Current TEST warning:
```text
Канал create_ticket не настроен для guild=519209364280573954
```

This is configuration, not a startup crash.

**Next ticket task:** configure/map the TEST `create_ticket` channel and then perform an end-to-end test of ticket creation, thread behavior, closing/transcript and recovery.

---

## 15. SERVER MAP / PERSISTENT CONFIG

`.server_map.json` is used in TEST for server-specific role/channel IDs.

Required role names:
```text
Owner
Administrator
Moderator
Helper
Member
Not verified
```

Required channel names include:
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

Incomplete mappings may fall back to values in `BotConfig`.

---

## 16. DEV RUNNER — VERIFIED 2026-08-31 / 2026-09-01

`dev_runner.py` is the local development auto-update runner.

**Current polling interval: 5 seconds.**

Important: the previous PROJECT_STATE incorrectly said 10 seconds and said the full cycle was untested. That is now stale.

### Actual end-to-end test

While `dev_runner.py` was already running, a harmless commit was made:

`6dbd454` — `test: verify dev runner auto update`

The runner detected it:
```text
[GIT] Updating 53bf473..6dbd454
Fast-forward
 DEV_RUNNER_TEST.txt | 1 +
[RUNNER] Обнаружены изменения: 53bf473... -> 6dbd454...
[RUNNER] Останавливаем старый процесс бота...
[RUNNER] Запуск бота...
```

The restarted bot then successfully:
- loaded all COGs;
- connected to Discord;
- became ready;
- synchronized 33 TEST commands;
- continued polling and printing `[GIT] Already up to date.`.

This proves the live **pull → changed HEAD detection → stop child → start child → continue polling** cycle.

The test file was then removed from GitHub in a follow-up commit:
`3b872d6` — `chore: remove dev runner test file`.

The runner automatically pulled that deletion and restarted the bot as expected.

Do not repeat the runner test unless a regression occurs.

Do not run a separate `main.py` alongside the runner.

One limitation remains by design: if `dev_runner.py` itself is modified through GitHub, the currently running runner process cannot automatically replace its own Python process merely by restarting the child bot. Treat runner self-update as a separate feature only if explicitly requested.

---

## 17. LOCAL GIT / DATABASE STATE

Runtime-generated local DB changes must not be discarded blindly.

Previously observed local files:
```text
modified: databases/Insane.sqlite3
untracked: databases/economy.db
databases/moderation.db
databases/settings.db
databases/tickets.db
databases/xp.db
```

The user has local development databases. Do not use `git restore`, reset or cleanup commands that could destroy them without explicit instruction.

A previous GitHub Desktop discrepancy showed many commits to pull while command-line Git said `main` was up to date. Command-line Git was treated as authoritative for the local repository check.

---

## 18. CURRENT STATUS / NEXT STEPS

### DONE / VERIFIED
- Admin Economy UserSelect and balance operations.
- Shop loading and command synchronization.
- Shop CRUD scenarios exercised.
- Shop role purchase and role assignment.
- Shop duplicate purchase/insufficient funds/disabled/deleted/missing-role/role-assignment failure behavior tested.
- Shop refunds on role assignment failure tested.
- `dev_runner.py` 5-second polling configured.
- Full live runner auto-pull/restart cycle tested.
- Runner test file removed.

### NEXT — HIGH PRIORITY
1. **Tickets:** configure `create_ticket` in TEST and test the full ticket lifecycle.
2. **Admin panel:** only address remaining issues discovered during real testing; do not refactor unnecessarily.
3. **Economy:** decide whether negative balances are allowed when an admin removes more than the user owns.

### FUTURE
- profile cards/customization;
- quests;
- achievements;
- mini-games;
- friends/relationships;
- other planned social systems.

If a test fails, inspect the actual current code and fix the smallest necessary part. Do not add speculative workarounds.

---

## 19. IMPORTANT HAND-OFF FACTS

- Branch: `main`.
- TEST guild: `519209364280573954` (`Insane TEST`).
- Bot: `Insane#6907`.
- Current runner interval: **5 seconds**.
- Runner auto-update cycle: **verified**.
- Shop normal purchase: **verified**.
- Shop duplicate purchase rejection: **verified**.
- Shop error/refund cases listed above: **verified during current testing**.
- Admin Economy UserSelect: **verified**.
- `/shop`, `/buy`, `/shop_admin`, `/admin_panel`: synchronized and available in TEST.
- Tickets exist in code but TEST `create_ticket` channel mapping is not configured.
- Do not repeat already completed shop/runner tests unless regression occurs.
- Do not discard local runtime databases.
- Do not turn the project into a traditional RPG.
