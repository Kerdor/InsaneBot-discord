# InsaneBot-discord — Project State

Repository: https://github.com/Kerdor/InsaneBot-discord
Branch: `main`
State date: 2026-09-01

> Persistent hand-off document. Always inspect actual GitHub `main` before editing. Do not silently undo agreed decisions.

## 1. Working rules

- Act as a technical editor/developer.
- Inspect current repository before changes.
- Preserve architecture, names, order and formatting unless change is necessary.
- Make the smallest necessary change.
- No unnecessary libraries/refactors.
- Never use `...` as omitted-code placeholder.
- If a function changes for local replacement, provide the complete function.
- Check callers/references after code changes.
- Validate/test when practical.
- **After every code/config fix, update `PROJECT_STATE.md` with the fix, current state and relevant verification result before considering the task complete.**
- **Do not create branches; make completed changes directly on `main`.**
- For runtime problems, inspect actual code and supplied logs before guessing.
- Prefer `БЫЛО → СТАЛО` for focused changes.
- Python indentation: 4 spaces.

## 2. Product decision

InsaneBot is a Discord moderation/social/community bot with progression and game-like community systems.

### NOT A TRADITIONAL RPG — BINDING

Do not introduce talismans, consumable combat items, loot boxes, RPG equipment/inventory or meaningless RPG stats. Progression is primarily community/social: activity, XP, levels, economy, profiles, achievements, relationships, mini-games and rankings.

Shop is primarily for server/community benefits such as Discord roles, not RPG inventory.

## 3. Roadmap

1. Levels/XP — implemented
2. Economy — implemented/expanding
3. Shop — implemented and runtime-tested; UI redesign postponed
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
17. Tickets — implemented; TEST configuration/testing next
18. Moderation — implemented
19. Logging — implemented/expanding

## 4. TEST runtime

```text
ENVIRONMENT=test
MAIN_GUILD_ID=1217530337664434246
TEST_GUILD_ID=519209364280573954
TEST_GUILDS=[519209364280573954]
```

TEST guild: `Insane TEST` (`519209364280573954`).
Bot: `Insane#6907` (`1329864697358782504`).

MAIN guild is not connected during TEST runs; expected.

`config.py` separates TEST/production, loads `.server_map.json` and `.logging_channels.json`, validates/creates required directories, and includes `cogs.shop` and `cogs.admin_panel`.

## 5. Current COGs

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

All loaded successfully in the latest verified run.

## 6. Command sync — VERIFIED

Latest verified startup:

- all configured COGs loaded;
- 33 application commands in memory;
- Discord returned 33 registered TEST commands;
- `/shop`, `/buy`, `/shop_admin`, `/admin_panel` are available;
- Discord connection/startup succeeded.

The previous missing `cogs.shop` problem was fixed in `77e0bd8`.

## 7. XP / Levels

Persistent SQLite XP system.

Implemented: chat XP with anti-spam cooldown, voice XP with AFK exclusion, persistent levels, `/level`, `/xp_ranking`, active voice session recovery and level-up DM notification.

Recorded defaults:

- message XP cooldown: 60 seconds;
- message XP: 15–25 XP;
- voice XP: 5 XP per completed voice minute;
- level threshold: `100 * level²`;
- eligible message also awards 2 🪙.

## 8. Economy

Persistent SQLite economy.

Normal currency: 🪙. Rare currency: 💎.

Commands:

```text
/balance
/daily
/pay
/rich
```

Rare currency has no real-money purchase and is intended to be difficult to obtain.

### Admin Economy — VERIFIED

`/admin_panel → 💰 Экономика → UserSelect → amount` works.

Verified:
- select user;
- give coins;
- remove coins;
- reject zero;
- apply balance changes.

Negative-balance policy is still undecided. Do not silently change it.

## 9. Shop — FUNCTIONALLY TESTED

Persistent `shop_items` storage contains id, guild_id, name, description, price, role_id and enabled state.

Public commands:

```text
/shop
/buy <item_id>
```

Admin operations: create, edit, enable/disable, delete, configure name/description/price/role.

### Purchase safety

`ad99f0a` — `Fix shop role purchase validation`.

Current flow validates enabled item and role, rejects duplicate role ownership, checks coins, purchases/deducts, assigns role, and refunds on `disnake.Forbidden` or `disnake.HTTPException`.

### Runtime tests completed 2026-08-31

Verified:

- shop display;
- CRUD/edit;
- disabling item removes it from public shop;
- deleting item removes it from public shop;
- nonexistent/deleted item error;
- insufficient balance error;
- duplicate purchase rejection;
- missing role error;
- role assignment failure with refund;
- successful role purchase and actual Discord role assignment.

The previous PROJECT_STATE test list is stale; these tests must not be repeated unless a relevant regression/code change occurs.

### FUTURE SHOP UI/UX — AGREED, POSTPONED

The current shop presentation is considered too dry. The user wants a later visual redesign without changing the purchase mechanism.

Current style:

```text
🛒 Магазин

#1 · test — 1 🪙 → @Неизвестная роль — test
#2 · test — 2 🪙 → @test — test

Используйте /buy <ID> для покупки
```

Agreed future design:

- make the shop embed/text more visually appealing and less dry;
- paginate shop items;
- allow/display a choice of **5 or 10 items per page**;
- add bottom navigation buttons;
- left/right arrow buttons with page number in the center, visually like:

```text
◀  1/2  ▶
```

Navigation behavior:

- first page: left disabled;
- last page: right disabled;
- middle pages: both enabled;
- page number updates when navigating;
- `/buy <ID>` remains the purchase mechanism.

**Do not implement this redesign until the user explicitly asks to start it.** It is a planned UI/UX improvement, not a bug.

## 10. Profile

Basic `/profile` is implemented using existing XP/economy persistence. It shows identity, level/XP progress, normal/rare currency, message count, voice XP and total XP.

Future: profile cards, customization, achievements and social information.

## 11. Admin panel

`/admin_panel` is admin/owner restricted and is becoming the central management UI.

Current areas: settings, logging, shop and economy balance management; future controls may be added incrementally.

Persistent server settings: `databases/settings.db` with settings audit history.

## 12. Logging

COGs:

```text
cogs.logging.chat_logs
cogs.logging.guild_logs
cogs.logging.moderation_logs
cogs.logging.setup_logs
cogs.logging.voice_stats
cogs.logging.system_logs
```

Groups: messages, members/server, moderation, setup, voice, system.

Reaction logging is disabled by default because it is noisy. Do not redesign logging into a forum/thread architecture unless explicitly requested.

### 2026-09-01 rebuild/logging fixes

Initial `/rebuild` runs produced repeated `ClientException: Parent channel not found` errors in `GuildLogs.get_log_channel()` because cached log `Thread` objects could survive after their parent channel was deleted.

The first stale-thread fix was committed on `main` before the 02:02 runtime test. That test confirmed the `Parent channel not found` exception no longer occurs.

The 2026-09-01 02:02 runtime test then exposed a second cache problem: after the configured log forum/thread was deleted during rebuild, a stale cached logging destination was still returned and `.send()` produced `404 Not Found: Unknown Channel`.

Fixed in commit `a0a515d24b81f3340bfb231e81513a5602068f8f`:

- cached logging destinations are now checked against the current guild cache before reuse;
- deleted cached text channels are invalidated;
- cached threads are invalidated when their parent is missing from the guild cache;
- fetched thread destinations receive the same parent-existence validation;
- existing logging architecture and normal behavior are preserved.

**Verification status:** the stale-thread and stale-channel logging fixes are now **LIVE VERIFIED**. A full `/rebuild` on 2026-09-01 completed successfully with **no `Unknown Channel` / 404 logging errors**.

## 13. Moderation

Implemented persistent moderation DB, slash commands, moderation panel and moderation logging.

```text
/ban
/kick
/timeout
/unban
/warn
```

## 14. Tickets — NEXT CONCRETE TASK

Private-thread ticket system exists with creation, transcripts, recovery and persistent state.

Current TEST warning:

```text
Канал create_ticket не настроен для guild=519209364280573954
```

This is configuration, not a startup crash.

Next: configure/map the TEST `create_ticket` channel, then test ticket creation, private thread behavior, closing/transcript and recovery.

## 15. Server map / persistent config

`.server_map.json` provides TEST server-specific role/channel IDs.

Required roles and hierarchy:

```text
Owner
Administrator
Moderator
Helper
Member
Not verified
```

Discord hierarchy after rebuild must be, from highest to lowest:

```text
Owner
Administrator
Moderator
Helper
Member
Not verified
@everyone
```

### Role hierarchy fix — 2026-09-01

The previous rebuild relied on role creation order alone. Runtime testing showed that the resulting Discord hierarchy did not match the required order: `Not verified` appeared above `Member`, while `Owner` appeared at the bottom.

Fixed in commit `4dea2a9d80e05672af8c5fd77dad12a1732db0f0`:

- `_create_roles()` still creates the same six roles with the same permissions, colors, hoist and mentionable settings;
- after creation, the actual created `Role` objects are collected from the guild cache;
- `guild.edit_role_positions()` explicitly sets:
  - `Not verified` = 1;
  - `Member` = 2;
  - `Helper` = 3;
  - `Moderator` = 4;
  - `Administrator` = 5;
  - `Owner` = 6;
- a rebuild log line records the intended final hierarchy.

**Verification status:** **LIVE VERIFIED 2026-09-01.** The complete `/rebuild` completed without errors and the Discord role hierarchy was confirmed as Owner → Administrator → Moderator → Helper → Member → Not verified → @everyone.

Required channels include:

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

`.logging_channels.json` stores logging destinations/forum/thread IDs.

## 16. Dev runner — VERIFIED

`dev_runner.py` is the local development auto-update runner.

Current polling interval: **5 seconds**.

### Full live test

While runner was already running, commit `6dbd454` (`test: verify dev runner auto update`) was made.

Runner output confirmed:

```text
[GIT] Updating 53bf473..6dbd454
[RUNNER] Обнаружены изменения: 53bf473... -> 6dbd454
[RUNNER] Останавливаем старый процесс бота...
[RUNNER] Запуск бота...
```

Restarted bot loaded all COGs, connected to Discord, became ready and synchronized 33 TEST commands. Runner continued with `[GIT] Already up to date.`.

Temporary `DEV_RUNNER_TEST.txt` was removed in commit `3b872d6`, and that deletion was also automatically pulled/restarted.

Therefore the complete **pull → detect changed HEAD → stop child → start child → continue polling** cycle is verified.

Do not repeat the runner test unless runner code changes or regression occurs.

Do not run a separate `main.py` alongside the runner.

Runner self-update is not implemented: changing `dev_runner.py` itself through GitHub does not replace the currently running runner process. Treat that as a separate feature only if explicitly requested.

## 17. Local Git / databases

Do not blindly discard local runtime DB changes.

Previously observed local files:

```text
modified: databases/Insane.sqlite3
untracked: databases/economy.db
databases/moderation.db
databases/settings.db
databases/tickets.db
databases/xp.db
```

Do not use destructive restore/reset/cleanup commands against these without explicit instruction.

## 18. Current status / next steps

### DONE / VERIFIED

- Admin Economy UserSelect and balance operations.
- Shop loading and command synchronization.
- Shop CRUD and purchase/error/refund behavior.
- Successful shop role assignment.
- Dev runner 5-second polling.
- Full live auto-pull/restart cycle.
- Runner test file removal.
- Discord ticket/private-thread behavior fix verified: ticket channels no longer create unwanted Discord threads.
- Logging `Parent channel not found` stale-thread crash fixed and verified gone.
- Rebuild logging stale cached-channel 404 fix **live verified** on 2026-09-01.
- Rebuild role hierarchy **live verified** on 2026-09-01.

### DONE / CODE-FIXED, RUNTIME VERIFICATION PENDING

- None for the rebuild/logging/role-hierarchy items tested in the latest run.

### NEXT

1. **Tickets:** configure/map the TEST `create_ticket` channel and test the full lifecycle: creation → private thread → closing/transcript → recovery.
2. **Admin panel:** fix only issues discovered during real testing.
3. **Economy:** explicitly decide whether negative balances are allowed.

### FUTURE

- Shop visual redesign with 5/10 items per page and `◀ page/total ▶` navigation.
- Profile cards/customization.
- Quests.
- Achievements.
- Mini-games.
- Friends/relationships.
- Other planned social systems.

## 19. IMPORTANT HAND-OFF FACTS

- Branch: `main` only; **do not create branches**.
- TEST guild: `519209364280573954` (`Insane TEST`).
- Bot: `Insane#6907`.
- Runner interval: **5 seconds**.
- Runner auto-update: **verified**.
- Shop function/error/CRUD tests: **verified**.
- Admin Economy UserSelect: **verified**.
- `/shop`, `/buy`, `/shop_admin`, `/admin_panel`: synchronized and available in TEST.
- Shop UI redesign is **planned, not current work**.
- Tickets exist in code; Discord ticket-thread behavior has been corrected and needs lifecycle testing.
- Logging stale-thread crash and stale cached-channel 404 are verified fixed.
- Rebuild role hierarchy is verified in live Discord.
- **After every fix, update `PROJECT_STATE.md` before considering the work complete.**
- Do not repeat completed shop/runner tests without a relevant code change.
- Do not discard local runtime databases.
- Do not turn the project into a traditional RPG.
