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

## 3. Current roadmap

1. Levels/XP — implemented
2. Economy — implemented/expanding
3. Shop — implemented and runtime-tested; UI redesign postponed
4. Profiles — generated profile-card image implemented; customization comes next
5. Daily rewards — implemented
6. Quests — MVP implemented; detailed QA later
7. PvP — **removed from current roadmap**
8. Mini-games — future; Discord Activities are an accepted direction
9. Rankings — XP/economy/voice implemented
10. Achievements — MVP implemented; detailed QA later
11. Collecting — **removed from current roadmap for now**
12. Profile customization — planned on top of generated profile-card architecture
13. Social interactions — planned
14. Voice-time rankings — implemented
15. Friends — planned
16. Romantic relationships — planned
17. Tickets — implemented; final regression QA remains
18. Moderation — implemented; interaction acknowledgement hardening added; runtime QA remains
19. Logging — implemented/expanding

### Agreed development order before full QA

Finish all currently selected functionality first:
1. Quests
2. Achievements
3. Generated profile card for `/profile`
4. Profile customization on top of the card architecture
5. Only then begin detailed QA, strictly one system at a time.

Mini-games are a later feature and may include Discord Activities integrated with XP, economy, quests, achievements and rankings.

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

`config.py` separates TEST/production, loads `.server_map.json` and `.logging_channels.json`, validates/creates required directories, and loads the quests and achievements COGs.

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
cogs.quests
cogs.achievements
cogs.admin_panel
```

Before the latest feature commits, all configured COGs loaded successfully and startup reached Discord normally. Runtime verification of the newly added COGs remains part of the later QA phase.

## 6. Command sync

Latest previously verified startup had 33 application commands in memory and Discord returned 33 registered TEST commands. `/shop`, `/buy`, `/shop_admin`, `/admin_panel` were available.

After adding quests and achievements, command sync must be runtime-verified again. Expected new commands: `/quests` and `/achievements`.

## 7. XP / Levels

Persistent SQLite XP system.

Implemented: chat XP with anti-spam cooldown, voice XP with AFK exclusion, persistent levels, `/level`, `/xp_ranking`, active voice session recovery and level-up DM notification.

Defaults:
- message XP cooldown: 60 seconds;
- message XP: 15–25 XP;
- voice XP: 5 XP per completed voice minute;
- level threshold: `100 * level²`;
- eligible message also awards 2 🪙.

Full QA remains pending.

## 8. Economy

Persistent SQLite economy. Normal currency: 🪙. Rare currency: 💎.

Commands:
```text
/balance
/daily
/pay
/rich
```

Admin Economy was runtime verified: `/admin_panel → 💰 Экономика → UserSelect → amount`, including user selection, give/remove coins, zero rejection and balance changes.

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

## 10. Profile / Profile Card

`/profile` now uses the existing XP/economy persistence and generates a PNG profile card instead of returning the old Embed.

New renderer: `utils/profile_card.py`.

The card currently includes display name, level, XP progress, total XP, coins, rare currency, message count, voice XP and unlocked achievement count, plus the user's Discord avatar.

Pillow was added to `requirements.txt` because actual PNG rendering is required for the profile-card feature.

**Runtime QA remains pending.** Profile customization is intentionally not implemented yet; it should be built on top of this card architecture.

## 11. Quests

New persistent database: `databases/quests.py`, SQLite file `databases/quests.db`.

New COG: `cogs/quests.py`.

Public command:
```text
/quests
```

Current daily quests:
- `messages_10`: send 10 messages → 50 🪙
- `voice_30`: spend 30 counted voice minutes → 100 🪙
- `voice_sessions_3`: enter a counted voice channel 3 times → 75 🪙

Progress is stored per guild/user/quest/date. The date is UTC, so a new UTC day creates fresh progress without destructive cleanup.

Completion is automatically marked once the target is reached and the reward is granted once. Bot/webhook messages and AFK voice channels are excluded. Existing persistent voice-session information is used for recovery after restart when available.

No new library was needed for quests. Existing economy storage is reused for rewards.

**Detailed runtime QA is intentionally postponed until all currently selected functionality is implemented.**

## 12. Achievements — MVP IMPLEMENTED

New persistent database: `databases/achievements.py`, SQLite file `databases/achievements.db`.

New COG: `cogs/achievements.py`.

Public command:
```text
/achievements
```

Current achievements:
- `messages_1000`: 1000 messages
- `voice_10h`: 10 hours of counted voice activity
- `rich_10000`: 10 000 🪙 balance
- `shop_purchase`: first successful shop purchase
- `active_7_days`: activity on 7 different UTC dates

Progress is persistent per guild/user. Achievement unlocks are permanent and are not reset with daily quests.

Activity days are stored separately so repeated activity on one date does not inflate the count.

Shop integration: a successful purchase dispatches `shop_purchase`, allowing the achievements COG to increment the purchase achievement without changing the shop's purchase logic.

The achievements COG also derives message, voice and balance progress from the existing XP/economy persistence, avoiding duplicate statistic storage.

**Detailed runtime QA is intentionally postponed until the current functionality-build stage is complete.**

## 13. Admin panel

`/admin_panel` is admin/owner restricted. Current areas: settings, logging, shop and economy balance management. Persistent server settings use `databases/settings.db` with audit history.

Full QA remains pending.

## 14. Logging

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

## 15. Moderation

Implemented persistent moderation DB, slash commands, moderation panel and moderation logging:
```text
/ban
/kick
/timeout
/unban
/warn
```

### Interaction timeout hardening — CODE-FIXED, runtime QA pending

Fixed in commit `64c80fb3ab96fcb954ae7524d799a57feaa0247f`:
- moderation slash commands defer before long Discord/API/DB/logging work;
- `ModerationTargetModal.callback()` defers before member lookup and moderation work;
- successful post-defer responses use followups.

Runtime QA remains: `/warn`, `/timeout`, `/kick`, `/ban`, `/unban`, `/history` and moderation-panel modals multiple times, plus logs/history correctness.

## 16. Tickets

Private-thread ticket system exists with creation, transcripts, recovery and persistent state.

Previously verified:
- ticket creation works;
- ticket is a Discord private thread under `🎫・тикеты`;
- author/moderation access works;
- ordinary users cannot access an individual ticket;
- closing works and the ticket is not immediately deleted.

### Parent channel privacy bug — CODE-FIXED, runtime QA pending

Commit `041dcb14bc4f2b9db0c01c0f1b687b03e6ce379c` changed `server_manager.apply_channel_overwrites()` so managed `🎫・тикеты` uses `build_private_ticket_overwrites()` instead of normal support-category permissions.

After pulling/rebuilding or `/sync_server`, verify ordinary users cannot see `🎫・тикеты` while `🎫・создать-тикет` remains public and ticket creation still works.

### Interaction timeout fix — CODE-FIXED, runtime QA pending

- `cogs/tickets.py`: commit `1755d209f4bacf859a9da3396fef94e252140f6` — ticket modal, close button/command and close confirmation defer before DB/transcript work.
- `cogs/rebuild_command.py`: commit `a6257712676522a2e31d4bf20ea773a8f4d0ca5e` — `/rebuild_test_server` defers immediately and uses followup.

## 17. Verification — LIVE VERIFIED

Current role hierarchy:
```text
Owner > Administrator > Moderator > Helper > Member > Not verified > @everyone
```

Live verification already completed after `/rebuild`:
- ordinary user gets `Not verified`;
- owner gets `Owner` without `Not verified`;
- verification changes `Not verified → Member`.

## 18. Server Manager / Rebuild

Role hierarchy fix commit: `4dea2a9d80e05672af8c5fd77dad12a1732db0f0`.

Rebuild/logging cache fix commit: `a0a515d24b81f3340bfb231e81513a5602068f8f`.

Full rebuild previously completed successfully without Unknown Channel/404 logging errors.

## 19. Runner

`dev_runner.py` polls every 5 seconds.

Previously verified full pull → detect → stop child → restart child cycle.

The repository currently has `main.py` as the bot entrypoint and `dev_runner.py` as the development runner. Runner self-update is not implemented.

## 20. Local DB caution

Do not destructively reset/restore runtime DBs.

Observed runtime DBs include:
```text
databases/Insane.sqlite3
databases/economy.db
databases/moderation.db
databases/settings.db
databases/tickets.db
databases/xp.db
databases/quests.db
databases/achievements.db
```

## 21. QA strategy after functionality build

User decision: **finish all currently selected functionality first, then test one system at a time in detail.**

For each system test at minimum:
- normal scenario;
- invalid/bad input;
- permissions and role restrictions;
- edge cases;
- repeated execution/double-clicks;
- persistence/restart;
- interaction acknowledgement/timeouts;
- Discord permission failures;
- API/DB failures where practical;
- logs;
- rebuild/sync interactions;
- race/concurrency-sensitive paths.

Suggested QA order after the functionality stage:
1. Tickets and recent timeout/privacy fixes
2. Moderation
3. Verification
4. XP/levels
5. Economy/daily/pay/rich
6. Shop
7. Quests
8. Achievements
9. Profile/profile card
10. Rankings/voice stats
11. Admin panel
12. Rebuild/server manager
13. Logging groups
14. Runner
15. Full regression

After system-by-system QA, perform a final technical audit covering dead code, stale references, async correctness, interaction acknowledgement, permissions, role hierarchy, channels/threads, config, DB, runner, COG architecture, exceptions and race conditions.

## 22. Future roadmap after current functionality stage

- Profile customization
- Mini-games
- Discord Activities integrated with XP/economy/quests/achievements/rankings
- Social interactions
- Friends
- Romantic relationships

PvP and Collecting are not part of the current roadmap unless explicitly reconsidered later.

## 23. Current development status

The project is in the **functionality-build stage**, not the final QA stage.

Recently added directly to `main`:
- quests MVP;
- achievements MVP;
- generated PNG profile card;
- Pillow dependency for profile rendering;
- shop purchase event integration for achievements;
- corresponding COG/config/state updates.

Next development task: finish any remaining agreed functionality, especially profile customization on top of the generated card architecture. **Do not begin the detailed one-system-at-a-time QA phase until the current functionality stage is complete.**
