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
17. Tickets — implemented; TEST lifecycle testing in progress
18. Moderation — implemented; interaction acknowledgement hardening added
19. Logging — implemented/expanding

## 4. TEST runtime

```text
ENVIRONMENT=test
MAIN_GUILD_ID=1217530337664434246
TEST_GUILD_ID=519209364280573954
TEST_GUILDS=[519209364280573954]
```

TEST guild: `Insane TEST` (`519209364280573954`).
Bot: `Insane#6907`.

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

## 7. XP / Levels

Persistent SQLite XP system.

Implemented: chat XP with anti-spam cooldown, voice XP with AFK exclusion, persistent levels, `/level`, `/xp_ranking`, active voice session recovery and level-up DM notification.

Defaults:
- message XP cooldown: 60 seconds;
- message XP: 15–25 XP;
- voice XP: 5 XP per completed voice minute;
- level threshold: `100 * level²`;
- eligible message also awards 2 🪙.

## 8. Economy

Persistent SQLite economy. Normal currency: 🪙. Rare currency: 💎.

Commands:
```text
/balance
/daily
/pay
/rich
```

### Admin Economy — VERIFIED

`/admin_panel → 💰 Экономика → UserSelect → amount` works. Verified user selection, give/remove coins, zero rejection and balance changes.

Negative-balance policy remains undecided; do not silently change it.

## 9. Shop — FUNCTIONALLY TESTED

Persistent `shop_items` storage contains id, guild_id, name, description, price, role_id and enabled state.

Public commands:
```text
/shop
/buy <item_id>
```

Admin operations: create, edit, enable/disable, delete and configure name/description/price/role.

Purchase validation, duplicate-role protection, balance checks, role assignment and refund-on-failure are implemented.

Runtime tests completed 2026-08-31: display, CRUD/edit, disable/delete, nonexistent item, insufficient balance, duplicate purchase, missing role, assignment failure/refund and successful role purchase were verified.

### Future shop UI/UX — POSTPONED

Later redesign: more visual presentation, pagination, 5 or 10 items per page, bottom navigation and `◀ 1/2 ▶`. Do not implement until explicitly requested.

## 10. Profile

Basic `/profile` is implemented using existing XP/economy persistence. Future: profile cards, customization, achievements and social information.

## 11. Admin panel

`/admin_panel` is admin/owner restricted. Current areas: settings, logging, shop and economy balance management. Persistent server settings use `databases/settings.db` with audit history.

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

### Rebuild/logging fixes — 2026-09-01

Stale cached logging threads/channels caused `Parent channel not found` and later `404 Unknown Channel` errors during `/rebuild`.

Fixed in `a0a515d24b81f3340bfb231e81513a5602068f8f`: cached destinations are validated against current guild cache, deleted text channels are invalidated, cached threads with missing parents are invalidated, and fetched destinations receive the same validation.

**Verification:** full `/rebuild` on 2026-09-01 completed without `Unknown Channel` / 404 logging errors.

## 13. Moderation

Implemented persistent moderation DB, slash commands, moderation panel and moderation logging:
```text
/ban
/kick
/timeout
/unban
/warn
```

### Discord interaction timeout hardening — CODE-FIXED, runtime verification pending

Inspection of `cogs/moderation.py` found the same intermittent interaction-timeout risk previously seen in tickets/rebuild: slash commands could perform Discord API, database or logging work before acknowledging the interaction. The modal callback could also fetch a member, perform moderation actions and send logs before acknowledgement.

Fixed in commit `64c80fb3ab96fcb954ae7524d799a57feaa0247f` directly on `main`:

- `/warn` now defers before moderation logging/database work.
- `/timeout` now defers before the Discord timeout and database write.
- `/kick` now defers before the Discord kick/logging work.
- `/ban` now defers before the Discord ban/logging work.
- `/unban` now defers before user fetch/unban/logging work.
- `/history` now defers before the database read.
- `ModerationTargetModal.callback()` now defers before member lookup and all moderation work.
- All successful responses after a defer use `inter.followup.send()`.
- Validation/configuration errors that occur before long work still use the initial interaction response.

No new libraries, no branch, and no moderation logic/architecture changes were introduced.

**Verification status:** CODE-FIXED, runtime verification pending. After the runner pulls `64c80fb...`, test `/warn`, `/timeout`, `/kick`, `/ban`, `/unban`, `/history` and each moderation-panel modal multiple times. Confirm that every interaction acknowledges immediately and never requires a second click. Also verify moderation logs and punishment history remain correct.

## 14. Tickets

Private-thread ticket system exists with creation, transcripts, recovery and persistent state.

### Ticket runtime tests already passed

- Ticket creation works.
- Ticket is created as a Discord private thread under `🎫・тикеты`.
- Ticket privacy was checked successfully: author/moderation access works and ordinary users cannot access the individual ticket.
- Closing a ticket works and the ticket is not immediately deleted.

### Ticket channel permissions bug — FIXED, runtime verification pending

**Problem found during live testing:** ordinary users could see the parent channel `🎫・тикеты`, even though individual ticket threads were private.

Root cause:
- `rebuild_test_server.py` correctly created `🎫・тикеты` with `build_private_ticket_overwrites()`;
- however `server_manager.py` automatically called `apply_channel_overwrites()` for every new channel;
- `apply_channel_overwrites()` always applied normal category permissions;
- the support category grants the `Member` role `view_channel=True`;
- therefore the automatic channel-permission handler overwrote the intended private permissions of `🎫・тикеты`.

Fixed in commit `041dcb14bc4f2b9db0c01c0f1b687b03e6ce379c`: `apply_channel_overwrites()` now detects the managed `🎫・тикеты` channel by `CHANNEL_NAMES["tickets"]` and applies `build_private_ticket_overwrites()` instead of the normal category overwrites.

This preserves the existing ticket architecture and also fixes future automatic permission application, `/sync_server`, and channel creation/update paths that use `apply_channel_overwrites()`.

**Verification status:** CODE-FIXED, runtime verification pending. The TEST server must be rebuilt or `/sync_server` run after the bot pulls commit `041dcb14...`; then verify that ordinary users cannot see `🎫・тикеты` while `🎫・создать-тикет` remains public and ticket creation still works.

### Discord interaction timeout fix — CODE-FIXED, runtime verification pending

Live testing showed intermittent `Приложение не отвечает` on ticket creation, ticket closing and `/rebuild`, sometimes succeeding immediately on a second attempt, with no corresponding application error in the bot console.

Discord interactions must be acknowledged promptly; otherwise Discord can display a failed interaction even when the bot later continues processing.

Fixed on `main`:

- `cogs/tickets.py` commit `1755d209f4bacf859a9da3396fef94e252140f6`: ticket modal now defers immediately before database checks; ticket close button/command and close confirmation also acknowledge immediately before database/transcript work and use followups afterward.
- `cogs/rebuild_command.py` commit `a6257712677652a2e31d4bf20ea773a8f4d0ca5e`: `/rebuild_test_server` now defers immediately and sends the confirmation through a followup.

No libraries or overall ticket/rebuild architecture were changed.

**Verification status:** CODE-FIXED, runtime verification pending. After the runner pulls both commits, test `/rebuild`, create a ticket, open the close dialog and confirm close several times. The expected result is that the interaction is acknowledged every time without requiring a second click.

## 15. Verification / role synchronization

Verification system assigns `Not verified` to new members, removes it and assigns `Member` after successful verification, and synchronizes existing members on startup. The guild owner receives `Owner` instead of `Not verified`.

### Rebuild role assignment bug — CODE-FIXED, runtime verification pending — 2026-09-01

**Problem:** after `/rebuild`, all old custom roles are deleted and recreated with new IDs. The rebuild correctly recreated the role hierarchy, but it did not immediately reassign the new roles to existing members. The existing synchronization only ran on bot startup (`on_ready`) or member join, so a rebuild during an already-running bot left users without `Not verified` / `Owner` until a restart.

**Expected behavior:** yes — after a TEST rebuild, existing ordinary users should receive the newly created `Not verified` role, while the guild owner should receive the newly created `Owner` role and have `Not verified` removed. A previously verified ordinary user should keep their `Member` role only if that role is still present; because rebuild replaces the roles, the current sync behavior treats users without the new `Member` role as not verified.

Fixed directly on `main` in commit `cd04d2c63db22214b16e1fcd4c8dda74ba589f10` (`cogs/verification.py`):

- added an `on_guild_role_create` listener that detects creation of the rebuilt `Owner` role and immediately runs existing-member role synchronization;
- `_sync_existing_members()` now falls back to resolving the freshly created roles by their configured names when the runtime IDs still point to deleted pre-rebuild roles;
- existing verification logic and role hierarchy were not otherwise changed;
- no new libraries and no branches were used.

**Verification status:** CODE-FIXED, runtime verification pending. Pull/restart, run `/rebuild`, then check an ordinary member has `Not verified` and the guild owner has `Owner` (without `Not verified`). Also verify the verification panel still changes `Not verified → Member` normally.

## 16. Server map / persistent config

`.server_map.json` provides TEST server-specific role/channel IDs. `.logging_channels.json` stores logging destinations/forum/thread IDs.

Required roles and hierarchy:
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

The previous rebuild relied on role creation order and produced the wrong hierarchy. Fixed in `4dea2a9d80e05672af8c5fd77dad12a1732db0f0` by explicitly calling `guild.edit_role_positions()` after role creation:

- Not verified = 1
- Member = 2
- Helper = 3
- Moderator = 4
- Administrator = 5
- Owner = 6

**Verification:** LIVE VERIFIED 2026-09-01. Full rebuild completed without errors and Discord showed Owner → Administrator → Moderator → Helper → Member → Not verified → @everyone.

Required channels include `create_voice`, `verification`, `create_ticket`, `tickets`, `game_panel`, `moderation_panel`, logging destinations and the normal community/game channels.

## 17. Dev runner — VERIFIED

`dev_runner.py` polls every 5 seconds.

Full live pull → detect changed HEAD → stop child → start child → continue polling cycle was verified. Do not repeat unless runner code changes or a regression occurs.

Do not run a separate `main.py` alongside the runner.

Runner self-update is not implemented; treat it as a separate future feature only if explicitly requested.

## 18. Local Git / databases

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

## 19. Current status / next steps

### DONE / VERIFIED

- Admin Economy UserSelect and balance operations.
- Shop loading, command synchronization, CRUD and purchase/error/refund behavior.
- Successful shop role assignment.
- Dev runner 5-second polling and full auto-pull/restart cycle.
- Runner test file removal.
- Discord ticket/private-thread behavior: individual ticket privacy and lifecycle creation/closing verified.
- Logging stale-thread crash and stale cached-channel 404 fix.
- Rebuild role hierarchy.

### CODE-FIXED, RUNTIME VERIFICATION PENDING

- `🎫・тикеты` parent-channel privacy fix from commit `041dcb14bc4f2b9db0c01c0f1b687b03e6ce379c`.
- Intermittent Discord interaction timeout fix from commits `1755d209f4bacf859a9da3396fef94e252140f6` and `a6257712677652a2e31d4bf20ea773a8f4d0ca5e`.
- Moderation interaction acknowledgement hardening from commit `64c80fb3ab96fcb954ae7524d799a57feaa0247f`.
- Rebuild existing-member role synchronization from commit `cd04d2c63db22214b16e1fcd4c8dda74ba589f10`.

### NEXT

1. Pull/restart the bot with the latest `main`.
2. Run `/rebuild` and verify role synchronization: ordinary member → `Not verified`; guild owner → `Owner` and not `Not verified`.
3. Verify the verification panel still converts `Not verified → Member`.
4. Verify the moderation interaction acknowledgement fix: test `/warn`, `/timeout`, `/kick`, `/ban`, `/unban`, `/history` and all moderation panel modals multiple times.
5. Confirm moderation logs and punishment history remain correct.
6. Finish runtime verification of the ticket parent-channel privacy fix and ticket/rebuild interaction acknowledgement fix if not already verified after the latest pull.
7. Continue ticket lifecycle tests: transcript/recovery.
8. Then move to the next planned functionality and test it incrementally.
9. Admin panel: fix only issues discovered during real testing.
10. Economy: explicitly decide whether negative balances are allowed.

### FUTURE

- Shop visual redesign with 5/10 items per page and `◀ page/total ▶` navigation.
- Profile cards/customization.
- Quests.
- Achievements.
- Mini-games.
- Friends/relationships.
- Other planned social systems.

## 20. IMPORTANT HAND-OFF FACTS

- Branch: `main` only; **do not create branches**.
- TEST guild: `519209364280573954` (`Insane TEST`).
- Bot: `Insane#6907`.
- Runner interval: **5 seconds**.
- Runner auto-update: verified.
- Shop function/error/CRUD tests: verified.
- Admin Economy UserSelect: verified.
- `/shop`, `/buy`, `/shop_admin`, `/admin_panel`: synchronized and available in TEST.
- Shop UI redesign is planned, not current work.
- Tickets use private Discord Threads under the `🎫・тикеты` parent channel.
- Individual ticket privacy and creation/closing have been tested successfully.
- Parent `🎫・тикеты` privacy fix is committed but needs live verification after update/rebuild.
- Ticket/rebuild interaction acknowledgement fix is committed but needs live verification.
- Logging stale-thread and stale-channel fixes are verified.
- Rebuild role hierarchy is verified.
- Rebuild role synchronization fix is committed but needs live verification.
- **After every fix, update `PROJECT_STATE.md` before considering the work complete.**
- Do not repeat completed shop/runner tests without a relevant code change.
- Do not discard local runtime databases.
- Do not turn the project into a traditional RPG.
