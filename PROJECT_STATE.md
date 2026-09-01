# InsaneBot-discord — PROJECT STATE / MASTER ROADMAP

Repository: https://github.com/Kerdor/InsaneBot-discord  
Branch: `main`  
State date: 2026-09-02  
Audited source baseline: `f19eedcf4f3bbc1476aabc9f17f6f355602e5590`

> **This file is the authoritative hand-off document for the project.** It describes the product concept, binding decisions, current architecture, implemented systems, known limitations, exact development order and QA state. A new development chat must be able to continue from this file without requiring the user to re-explain the project from zero.
>
> The source code on GitHub `main` is always the final authority for implementation details. If this document and the source disagree, inspect the source, resolve the discrepancy and update this file.

---

# 1. WORKING RULES — BINDING

These rules apply to all future development unless the user explicitly changes them.

- Act as a technical editor/developer.
- Inspect the current GitHub `main` before making code changes.
- Do not guess about the current implementation when the repository can be inspected.
- Preserve existing architecture, names, function order and formatting unless a change is actually necessary.
- Make the smallest necessary code change.
- Do not add libraries without a real requirement.
- Do not perform unrelated refactors.
- Never use `...` as an omitted-code placeholder in code supplied for replacement.
- If a function is changed for manual replacement, provide the complete function body.
- Check callers, imports and references after changing or removing code.
- Prefer `БЫЛО → СТАЛО` when describing focused code changes.
- Python indentation is 4 spaces.
- Do not destructively reset, delete or restore runtime databases.
- Do not create branches for normal project work; completed changes go directly to `main`.
- After every code/config fix, update this `PROJECT_STATE.md` with the current state and verification result.
- Runtime bugs must be investigated from actual source code and logs before proposing a fix.
- Keep the project state accurate: `IMPLEMENTED` does not mean `QA PASSED`.
- Do not mark a system as tested merely because its code exists or CI passes.
- When a system is fully QA-tested, record what was tested and the result here.

---

# 2. STATUS SYSTEM

Use these statuses consistently.

- `PLANNED` — agreed future functionality, not implemented.
- `IN PROGRESS` — currently being implemented.
- `IMPLEMENTED` — source implementation exists.
- `INTEGRATION CHECK` — implementation exists and cross-system verification is required.
- `RUNTIME TESTED` — manually tested against the running Discord bot for the listed scenarios.
- `QA PASSED` — detailed system QA is complete and regression checks passed.
- `QA PENDING` — implementation exists but detailed QA has not yet been completed.
- `POSTPONED` — deliberately postponed; do not implement unless explicitly requested.
- `REMOVED` — deliberately removed from the current roadmap.
- `BLOCKED` — cannot proceed until a stated dependency/decision is resolved.

A system can therefore legitimately be:

`IMPLEMENTED / QA PENDING`

or:

`IMPLEMENTED / RUNTIME TESTED / QA PENDING`.

The target for the current core systems is eventually:

`IMPLEMENTED → INTEGRATION CHECK → RUNTIME TESTED → QA PASSED`.

---

# 3. PRODUCT CONCEPT — DO NOT BREAK THIS

## 3.1 What InsaneBot is

InsaneBot is a **Discord community/progression bot**.

The core idea is to make normal activity on a Discord server meaningful without turning the bot into a traditional RPG.

The main progression loop is:

```text
Server activity
      │
      ├── chat
      ├── voice
      ├── daily activity
      ├── quests
      ├── purchases
      └── future mini-games / Activities
             │
             ▼
        XP / Coins / Rare Currency
             │
             ├── Levels
             ├── Rankings
             ├── Quests
             ├── Achievements
             ├── Shop
             └── Profile
```

The systems should reinforce one another instead of existing as unrelated commands.

## 3.2 NOT A TRADITIONAL RPG — HARD CONSTRAINT

Do **not** introduce RPG mechanics merely for the sake of making the bot look like an RPG.

Explicitly prohibited from the current concept:

- talismans;
- consumable combat items;
- loot boxes;
- RPG equipment/inventory;
- meaningless RPG statistics;
- combat systems without a strong community purpose;
- PvP as part of the current roadmap;
- collection mechanics as part of the current roadmap.

The shop is primarily for **Discord/community benefits**, such as roles, not RPG equipment.

## 3.3 Progression should come from community activity

Important progression sources:

- messages;
- voice activity;
- daily rewards;
- quests;
- achievements;
- shop activity;
- future mini-games;
- future Discord Activities;
- future social systems if they prove useful.

---

# 4. PRODUCT DECISIONS THAT ARE NOW LOCKED

## KEEP — mandatory product direction

- XP / levels
- Economy
- Daily rewards
- Shop
- Profile
- Generated profile card
- Profile customization
- Rankings
- Verification
- Moderation
- Tickets
- Voice systems
- Logging
- Admin Panel
- Server Manager
- Rebuild
- Development Runner
- Quests
- Achievements
- Mini-games in the future
- Discord Activities in the future

## REMOVED FROM CURRENT ROADMAP

### PvP — `REMOVED`

Do not add PvP unless the user explicitly reopens the decision.

Reason: it would add a large amount of balance/state/gameplay complexity and does not fit the current community-first direction.

### Collecting — `REMOVED FOR NOW`

Do not build a collection system merely because the bot has achievements/profile/shop systems.

Possible future collection concepts may exist, but they are not part of the active plan.

## FUTURE ONLY

These are ideas, not current implementation tasks:

- social interactions;
- friends;
- romantic relationships;
- richer profile cosmetics;
- additional mini-games;
- Discord Activities;
- Activity result integration with progression.

Do not start these before the current core QA is complete unless explicitly requested.

---

# 5. ARCHITECTURE VISION

The long-term architecture should remain a connected ecosystem:

```text
                         ┌─────────────────────┐
                         │      Discord        │
                         └──────────┬──────────┘
                                    │
              ┌─────────────────────┼─────────────────────┐
              │                     │                     │
              ▼                     ▼                     ▼
          Discord Bot          Mini-games          Discord Activity
              │                 (future)               (future)
              │                     │                     │
              └─────────────────────┼─────────────────────┘
                                    ▼
                           InsaneBot progression
                                    │
        ┌──────────────┬────────────┼────────────┬──────────────┐
        ▼              ▼            ▼            ▼              ▼
       XP          Economy       Quests    Achievements      Profile
        │              │            │            │              │
        ▼              ▼            └──────┬─────┘              ▼
     Levels         Shop                   │              Profile Card
        │              │                   │                    │
        └──────────────┴───────────────────┴────────────────────┘
                                    │
                                    ▼
                                Rankings
```

The important principle is that future systems should **use the existing progression infrastructure** instead of creating duplicate currencies, counters or unrelated databases.

Example future flow:

```text
Quiz Activity
   ↓
result: 8/10
   ↓
+50 XP
+100 🪙
   ↓
achievement progress +1
quest progress +1
ranking updated through existing XP/economy data
profile reflects the new totals
```

This is an architectural direction, not a current implementation requirement.

---

# 6. CURRENT REPOSITORY STRUCTURE

The current repository contains the following important application areas.

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

`README.md` is currently absent from `main`.

`cogs/user_cmd/get_roles.py` exists in the repository but is not in the configured COG list and appears to be legacy/dead code. It should not be treated as an active system unless explicitly reintroduced.

`cogs/logging/reaction_logs.py` exists but is intentionally not loaded in the current COG configuration.

---

# 7. TECHNOLOGY / DEPENDENCIES

Current runtime stack:

- Python version is controlled by `.python-version`.
- Discord library: `disnake >=2.12.1,<3`.
- Image generation for profile cards: `Pillow >=11,<13`.
- Persistence: SQLite through Python's built-in `sqlite3`.
- No additional external application framework is currently required.

Current `requirements.txt`:

```text
disnake>=2.12.1,<3
Pillow>=11,<13
```

Do not add dependencies without an actual requirement.

---

# 8. RUNTIME / DEPLOYMENT MODEL

## TEST environment

Current intended development environment:

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

The bot is currently developed/tested against the TEST guild.

The MAIN guild must not be touched accidentally during TEST development.

## Configuration isolation

`config.py`:

- reads `.env`;
- distinguishes `test` and `production`;
- chooses the active guild from `TEST_GUILD_ID` or `MAIN_GUILD_ID`;
- loads `.server_map.json` when valid for the active guild;
- loads `.logging_channels.json` by guild ID;
- validates required configuration;
- creates required runtime directories.

Important safety rule:

**Production must never silently consume a TEST server map.**

The config/server-map compatibility fix was implemented in commit:

```text
f4321d9aa022b7085c19b510cf965d073d4ed544
```

Logging-map compatibility for old `server_logs` vs current `guild_logs` naming was implemented in:

```text
f19eedcf4f3bbc1476aabc9f17f6f355602e5590
```

GitHub Actions run #214 for that commit completed successfully.

---

# 9. BOT STARTUP / COMMAND LOADING

Main entrypoint:

```text
main.py
```

Development runner:

```text
dev_runner.py
```

`main.py`:

- creates the `disnake` bot;
- enables members and message-content intents;
- loads configured COGs;
- explicitly includes `cogs.admin_panel` through the current loader arrangement;
- prints loaded COGs and application commands;
- performs explicit TEST guild command synchronization;
- starts the Discord client;
- provides owner-only `/load`, `/unload` and `/reload` commands.

The configured COG list is:

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

Current expected progression commands include:

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

Other infrastructure/moderation/admin/server/ticket commands exist in their respective COGs.

Command count/sync must be runtime-verified after major command changes. Historical startup verification reached Discord normally and reported the expected registered TEST commands; the latest additions still require the planned detailed QA.

---

# 10. DEVELOPMENT RUNNER

`dev_runner.py` is a local development auto-update runner.

Behavior:

- starts `main.py`;
- checks Git every 5 seconds;
- runs `git pull`;
- detects HEAD changes;
- stops the current bot process;
- starts the new version;
- keeps running until Ctrl+C or bot process termination.

Current poll interval:

```text
5 seconds
```

The runner does not implement a self-update mechanism for itself.

Status: `IMPLEMENTED / QA PENDING`.

---

# 11. DATABASE ARCHITECTURE

SQLite is used for persistent systems.

Current databases:

```text
databases/xp.py
    → databases/xp.db

databases/economy.py
    → databases/economy.db

databases/shop.py
    → databases/economy.db

databases/settings.py
    → databases/settings.db

databases/moderation.py
    → databases/moderation.db

databases/tickets.py
    → databases/tickets.db

databases/quests.py
    → databases/quests.db

databases/achievements.py
    → databases/achievements.db

databases/profile_customization.py
    → databases/profile_customization.db

databases/voice_stats.py
    → databases/Insane.sqlite3

databases/voice_rooms.py
    → its configured voice-room persistence database
```

Important:

- Runtime databases must be treated as persistent user/server state.
- Never reset databases simply to make a test pass.
- Never delete existing user progression as part of ordinary development.
- If schema changes are required later, use a safe migration strategy.

`databases/Insane.sqlite3` is currently tracked as an empty repository placeholder; runtime voice data is created in the actual runtime environment.

`.gitignore` ignores SQLite journal files but does not ignore all `.sqlite3` files, so this repository's database policy must remain deliberate.

---

# 12. SYSTEM STATUS MASTER TABLE

This is the quick status board. Detailed sections below are the authoritative descriptions.

| System | Implementation | Runtime tests | Detailed QA | Current status |
|---|---|---|---|---|
| Configuration / TEST-MAIN | DONE | PARTIAL | PENDING | `IMPLEMENTED / QA PENDING` |
| COG loading / startup | DONE | VERIFIED historically | PENDING after latest additions | `IMPLEMENTED / QA PENDING` |
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
| Economy | DONE | PARTIAL | PENDING | `IMPLEMENTED / QA PENDING` |
| Daily | DONE | PARTIAL | PENDING | `IMPLEMENTED / QA PENDING` |
| Shop | DONE | RUNTIME TESTED | PENDING regression QA | `RUNTIME TESTED / QA PENDING` |
| Quests | DONE | NOT STARTED | PENDING | `IMPLEMENTED / QA PENDING` |
| Achievements | DONE | NOT STARTED | PENDING | `IMPLEMENTED / QA PENDING` |
| Profile Card | DONE | NOT STARTED | PENDING | `IMPLEMENTED / QA PENDING` |
| Profile customization | DONE | NOT STARTED | PENDING | `IMPLEMENTED / QA PENDING` |
| Mini-games | NOT STARTED | — | — | `PLANNED` |
| Discord Activities | NOT STARTED | — | — | `PLANNED` |
| Social interactions | NOT STARTED | — | — | `PLANNED` |
| Friends | NOT STARTED | — | — | `PLANNED` |
| Romantic relationships | NOT STARTED | — | — | `PLANNED` |
| PvP | — | — | — | `REMOVED` |
| Collecting | — | — | — | `REMOVED FOR NOW` |

---

# 13. CORE PROGRESSION SYSTEM — XP / LEVELS

## Status

`IMPLEMENTED / QA PENDING`

## Source

```text
cogs/xp.py
databases/xp.py
```

## Implemented

- persistent XP per guild/user;
- XP from eligible chat messages;
- message XP cooldown;
- random message XP within configured min/max;
- message count tracking;
- XP from counted voice activity;
- AFK voice exclusion;
- persistent level;
- automatic level calculation;
- `/level`;
- `/xp_ranking`;
- level-up DM notification;
- active voice-session recovery using persistent voice session data;
- message activity also awards economy coins through existing economy storage.

## Current defaults

```text
xp_message_min = 15
xp_message_max = 25
xp_message_cooldown = 60 seconds
xp_voice_per_minute = 5
level threshold = 100 * level²
message reward = 2 🪙
```

## Important implementation detail

Voice XP uses completed counted voice minutes. The persistent voice session source is maintained by the VoiceStats system.

Do not create a second independent persistent voice-time counter for XP.

## QA checklist

- [ ] First eligible message gives XP.
- [ ] Message cooldown works.
- [ ] Bots/webhooks do not award XP.
- [ ] Min/max XP settings work.
- [ ] Message count increments correctly.
- [ ] Coins are awarded according to economy settings.
- [ ] Voice XP starts/stops correctly.
- [ ] AFK time is excluded.
- [ ] Moving between counted voice channels does not lose/duplicate time.
- [ ] Restart while in voice recovers correctly.
- [ ] Level transitions occur at the correct threshold.
- [ ] Level-up notification does not break the XP operation if DMs are disabled.
- [ ] `/level` handles users without a stored XP row.
- [ ] `/xp_ranking` ordering is correct.
- [ ] Settings changes through Admin Panel apply immediately.

---

# 14. ECONOMY / DAILY / CURRENCIES

## Status

`IMPLEMENTED / QA PENDING`

## Source

```text
cogs/economy.py
databases/economy.py
```

## Currencies

- 🪙 normal currency;
- 💎 rare currency.

The rare currency exists in the persistence model but does not currently have a full earning/spending loop.

## Commands

```text
/balance
/daily
/pay
/rich
```

## Implemented

- persistent per guild/user balance;
- user initialization;
- message rewards;
- daily reward;
- player-to-player transfer;
- balance ranking;
- economy enable/disable setting;
- admin balance adjustment through Admin Panel.

## Important decisions

Negative-balance policy is not a separately finalized product rule. Do not silently invent a new policy.

Daily cooldown currently uses a persistent timestamp and a 24-hour interval.

## QA checklist

- [ ] New user starts correctly.
- [ ] `/balance` is correct.
- [ ] `/daily` awards exactly once per cooldown.
- [ ] Daily cooldown survives restart.
- [ ] `/pay` rejects self-transfer.
- [ ] `/pay` rejects bots.
- [ ] `/pay` rejects non-positive amounts.
- [ ] `/pay` rejects insufficient balance.
- [ ] Successful transfer changes both users atomically.
- [ ] `/rich` ordering is correct.
- [ ] Admin give/remove works.
- [ ] Economy disable blocks relevant earning/spending flows.
- [ ] No unintended negative balance is introduced.

---

# 15. SHOP

## Status

`RUNTIME TESTED / QA PENDING`

## Source

```text
cogs/shop.py
databases/shop.py
```

Shop persistence is stored in `economy.db` alongside economy data.

## Public commands

```text
/shop
/buy <item_id>
```

## Admin functionality

- create item;
- edit item;
- enable/disable item;
- delete item;
- set name;
- set description;
- set price;
- set Discord role.

## Item model

```text
id
guild_id
name
description
price
role_id
enabled
```

## Purchase flow

```text
/buy
  ↓
item exists + enabled
  ↓
role exists if configured
  ↓
user does not already have role
  ↓
charge balance
  ↓
assign role
  ↓
if assignment fails → refund
  ↓
success → dispatch shop_purchase
```

Successful purchases dispatch:

```text
shop_purchase
```

Achievements consume this event.

## Runtime tests already completed

On 2026-08-31 the following were tested:

- shop display;
- item CRUD/edit;
- disable/delete;
- nonexistent item;
- insufficient balance;
- duplicate purchase;
- missing role;
- role assignment failure and refund;
- successful role purchase.

## QA still required

- [ ] Full regression after later progression changes.
- [ ] Permission behavior.
- [ ] Economy-disabled behavior.
- [ ] Role hierarchy edge cases.
- [ ] Concurrent purchase edge cases.
- [ ] Achievement event behavior.
- [ ] Restart persistence.

## Shop UI redesign

`POSTPONED`.

Do not implement the following unless explicitly requested:

- redesigned visual shop;
- 5/10 items per page;
- pagination;
- bottom navigation;
- `◀ 1/2 ▶` controls.

---

# 16. QUESTS — CORE SYSTEM

## Status

`IMPLEMENTED / QA PENDING`

Quests are now a **permanent part of the product concept**.

They are **community/activity quests**, not RPG quests.

## Source

```text
cogs/quests.py
databases/quests.py
```

## Command

```text
/quests
```

## Current daily quests

```text
messages_10
10 messages → 50 🪙

voice_30
30 counted voice minutes → 100 🪙

voice_sessions_3
3 counted voice joins → 75 🪙
```

## Current implementation rules

- progress is per guild/user/quest/date;
- quest date is UTC;
- daily records are persistent;
- progress is capped at target;
- completion is persistent for the current quest date;
- reward is claimed once;
- bot messages are excluded;
- webhook messages are excluded;
- AFK voice is excluded;
- voice sessions are recovered from persistent voice session data when available;
- economy reward uses the existing economy storage;
- no additional library is required.

## Important architectural direction

Quests should eventually support a broader set of activity conditions, for example:

- send 100 messages;
- spend 60 minutes in voice;
- earn 500 XP;
- be active on several days;
- use `/daily`;
- make a purchase;
- interact socially with other members;
- combine multiple conditions.

Rewards may include:

- 🪙 coins;
- 💎 rare currency;
- XP;
- achievement progress/unlocks;
- future profile cosmetics.

These are **future quest types**, not all currently implemented.

## QA checklist

- [ ] `/quests` renders all current daily quests.
- [ ] Message quest increments exactly once per eligible message.
- [ ] Bot/webhook messages do not count.
- [ ] Voice-minute quest counts only counted voice time.
- [ ] AFK time is excluded.
- [ ] Voice-session quest increments on valid entry.
- [ ] Moving between counted channels does not incorrectly create a new session unless intended by implementation.
- [ ] Leaving voice awards the correct completed-minute progress.
- [ ] Completion triggers once.
- [ ] Reward is granted once.
- [ ] Reward persists.
- [ ] UTC reset works.
- [ ] Restart/recovery works.
- [ ] Quest state is isolated by guild and user.
- [ ] Failure/crash windows around reward claiming are examined.

---

# 17. ACHIEVEMENTS — CORE SYSTEM

## Status

`IMPLEMENTED / QA PENDING`

Achievements are a permanent part of the progression architecture and should become one of the main long-term progression layers.

## Source

```text
cogs/achievements.py
databases/achievements.py
```

## Command

```text
/achievements
```

## Current achievements

```text
messages_1000
1000 messages

voice_10h
10 hours of counted voice activity

rich_10000
10 000 🪙 balance

shop_purchase
first successful shop purchase

active_7_days
activity on 7 different UTC dates
```

## Current implementation rules

- persistent per guild/user;
- unlocks are permanent;
- progress is capped at the achievement target;
- activity dates are deduplicated;
- message progress reuses XP message count;
- voice progress reuses persistent voice statistics;
- balance progress reuses economy balance;
- shop purchase progress uses the successful shop purchase event;
- daily quest reset does not reset achievements.

The `voice_10h` achievement deliberately uses persistent counted voice time rather than assuming that one particular XP-per-minute configuration is fixed.

## Future achievement philosophy

Achievements should reward meaningful community progression, for example:

- first steps — 10 messages;
- talkative member — 1000 messages;
- social life — 10 voice hours;
- wealthy member — 100 000 🪙;
- regular customer — 10 purchases;
- loyal member — active on 30 days;
- future game/activity achievements.

Exact future achievements must be designed before implementation.

## QA checklist

- [ ] `/achievements` displays locked/unlocked states correctly.
- [ ] Message achievement progresses correctly.
- [ ] Voice achievement uses actual counted voice time.
- [ ] Balance achievement reflects actual balance.
- [ ] Shop achievement triggers only on successful purchase.
- [ ] Activity-day achievement deduplicates same-day activity.
- [ ] Unlock is permanent.
- [ ] Progress never moves backwards.
- [ ] Achievements are isolated by guild/user.
- [ ] Restart preserves progress.
- [ ] Profile card displays achievement count correctly.

---

# 18. PROFILE CARD — CORE SYSTEM

## Status

`IMPLEMENTED / QA PENDING`

The profile card is the visual representation of the user's progression.

The old concept of `/profile` as a text Embed has been replaced by a generated PNG card.

## Source

```text
cogs/xp.py
utils/profile_card.py
```

## Command

```text
/profile
```

## Current card data

The card currently contains:

- Discord avatar;
- display name;
- level;
- current XP progress;
- required XP for next level;
- total XP;
- 🪙 coins;
- 💎 rare currency;
- message count;
- voice XP;
- unlocked achievement count;
- bio when customized.

## Renderer

```text
utils/profile_card.py
```

Current generated image size:

```text
1000 × 460
```

Pillow is used for rendering.

## Architectural order

The intended product order is:

```text
Profile data
   ↓
Generated Profile Card
   ↓
Profile Customization
```

The customization implementation already exists in the current source, but the conceptual dependency remains important: customization is a layer on top of the profile card, not a separate replacement for it.

## QA checklist

- [ ] `/profile` generates a valid PNG.
- [ ] Avatar loads correctly.
- [ ] Avatar fallback works if Discord avatar retrieval fails.
- [ ] Display name renders correctly.
- [ ] Level is correct.
- [ ] XP progress is correct.
- [ ] Total XP is correct.
- [ ] Coins are correct.
- [ ] Rare currency is correct.
- [ ] Message count is correct.
- [ ] Voice XP is correct.
- [ ] Achievement count is correct.
- [ ] User with no prior XP/economy data still gets a valid card.
- [ ] Long display names do not break the card.
- [ ] Unicode/Cyrillic text renders acceptably with the current font fallback.
- [ ] Image can be sent by Discord without corruption.
- [ ] Profile data remains guild-specific.

---

# 19. PROFILE CUSTOMIZATION

## Status

`IMPLEMENTED / QA PENDING`

## Source

```text
cogs/xp.py
databases/profile_customization.py
utils/profile_card.py
```

## Command

```text
/profile_customize
```

## Current supported customization

- background color;
- accent color;
- short bio;
- reset.

## Defaults

```text
background = #181B23
accent = #FFD75A
bio limit = 70 characters
color format = #RRGGBB
```

## Persistence

Stored per:

```text
guild_id + user_id
```

When only one setting changes, unspecified existing settings are preserved.

## Validation

- colors are normalized/validated as hexadecimal RGB values;
- bio is limited to 70 characters;
- renderer has safe color fallbacks.

## Future customization

Possible future layers:

- richer backgrounds;
- profile frames;
- visual themes;
- icons;
- titles;
- badges;
- selected displayed achievements.

These are future plans, not current implementation requirements.

## QA checklist

- [ ] Set background color.
- [ ] Set accent color.
- [ ] Set bio.
- [ ] Update only one field and verify other fields remain unchanged.
- [ ] Reject invalid colors.
- [ ] Reject bio longer than 70 characters.
- [ ] Reset returns to defaults.
- [ ] Persistence survives restart.
- [ ] Customization is isolated by guild/user.
- [ ] `/profile` actually reflects saved customization.
- [ ] Invalid/malformed stored values do not crash rendering.

---

# 20. VOICE STATISTICS

## Status

`IMPLEMENTED / QA PENDING`

## Source

```text
cogs/logging/voice_stats.py
databases/voice_stats.py
```

## Commands

```text
/voice
/voice_ranking
```

## Persistence

Tracks:

- total voice seconds per guild/user;
- per-channel voice seconds;
- active persistent sessions.

## Rules

- AFK channel is excluded;
- bot users are excluded;
- sessions survive restart through persistent `voice_sessions`;
- moving between channels closes the old session and starts a new one;
- active sessions are reconciled on `on_ready`.

## Integration dependencies

Voice statistics are a foundational source for:

- voice XP;
- voice quest progress;
- voice achievements;
- `/voice`;
- `/voice_ranking`;
- future profile/stat displays.

Do not create duplicate persistent voice counters in individual features.

## QA checklist

- [ ] Join counted voice.
- [ ] Leave counted voice.
- [ ] Stay in voice for a known interval.
- [ ] AFK channel is excluded.
- [ ] Move between voice channels.
- [ ] Restart while a user is in voice.
- [ ] Reconcile stale sessions.
- [ ] `/voice` includes active current session.
- [ ] `/voice_ranking` includes correct accumulated totals.
- [ ] Per-channel totals are correct.

---

# 21. VOICE ROOMS / CREATE VOICE

## Status

`IMPLEMENTED / QA PENDING`

## Source

```text
cogs/user_cmd/create_voice.py
databases/voice_rooms.py
```

This is the user-created/private voice-room system.

Current functionality includes room management such as:

- rename;
- participant limit;
- co-owner management;
- access management;
- main-room selection;
- room control panel;
- persistent room data;
- permission management.

This system is separate from voice statistics, although both respond to Discord voice events.

## QA checklist

- [ ] Create room.
- [ ] Room owner permissions.
- [ ] Rename.
- [ ] User limit.
- [ ] Add/remove access.
- [ ] Add/remove co-owner.
- [ ] Main-room selection.
- [ ] Permission cleanup.
- [ ] Restart recovery.
- [ ] Room deletion/cleanup behavior.
- [ ] Interaction timeout behavior.

---

# 22. VERIFICATION

## Status

`RUNTIME TESTED / QA PENDING`

## Source

```text
cogs/verification.py
```

## Current flow

New/unverified members receive the Not verified role.

The verification panel uses a simple generated arithmetic challenge.

Successful verification:

```text
Not verified → Member
```

The server owner is synchronized to the Owner role.

## Previously live-verified hierarchy

```text
Owner
  > Administrator
    > Moderator
      > Helper
        > Member
          > Not verified
            > @everyone
```

Previously verified runtime behavior:

- ordinary user receives Not verified;
- owner receives Owner;
- verification changes Not verified to Member.

## Known technical note

`on_guild_role_create` in the current verification source contains a TEST-guild-specific condition. This is acceptable for the current TEST workflow but is a technical audit candidate before production is treated as fully supported.

## QA checklist

- [ ] New member receives Not verified.
- [ ] Verification panel exists exactly as intended.
- [ ] Challenge answers work.
- [ ] Wrong answer stops the attempt.
- [ ] Correct answer changes roles.
- [ ] Already verified user cannot repeat unnecessarily.
- [ ] Owner synchronization works.
- [ ] Rebuild-created roles are handled correctly.
- [ ] Production environment does not depend on TEST-only conditions.
- [ ] Persistent panel behavior survives restart.

---

# 23. MODERATION

## Status

`IMPLEMENTED / QA PENDING`

## Source

```text
cogs/moderation.py
databases/moderation.py
```

## Commands

```text
/warn
/timeout
/kick
/ban
/unban
/history
```

The moderation panel also provides modal-based moderation actions.

## Implemented

- staff role checks;
- configurable enable/disable settings;
- warning persistence;
- timeout persistence;
- kick persistence;
- ban persistence;
- unban;
- moderation history;
- configurable timeout maximum;
- logging integration;
- modal-based actions;
- interaction timeout hardening;
- reuse of the existing Moderation COG from modal callbacks.

## Known fixes

Interaction/modal cog-instantiation issue was fixed so modal callbacks retrieve the already loaded `Moderation` COG instead of creating a second instance.

## Known technical audit candidates

- `_log_action` can potentially fail after a punishment if the subsequent log send raises.
- Discord role hierarchy behavior needs explicit QA for staff-vs-target combinations.
- Permission edge cases need testing.

Do not silently alter punishment semantics while fixing these issues.

## QA checklist

- [ ] Warn.
- [ ] Timeout minimum.
- [ ] Timeout maximum.
- [ ] Kick.
- [ ] Ban.
- [ ] Unban.
- [ ] History.
- [ ] Disabled moderation action.
- [ ] Unauthorized user.
- [ ] Bot/Discord permission failure.
- [ ] Role hierarchy.
- [ ] Logging success.
- [ ] Logging failure does not create inconsistent user-facing behavior.
- [ ] Modal path and slash-command path behave consistently.

---

# 24. TICKETS

## Status

`IMPLEMENTED / QA PENDING`

## Source

```text
cogs/tickets.py
databases/tickets.py
```

## Current flow

```text
Ticket panel
   ↓
Create Ticket
   ↓
Modal
   ├── short description
   ├── detailed description
   ├── expected result
   └── additional information
   ↓
Private thread
   ↓
Support/moderation access
   ↓
Close confirmation
   ↓
Transcript
   ↓
Archive + lock
```

## Implemented

- persistent ticket records;
- one open ticket per user logic;
- private threads;
- support/moderation access;
- ticket creation modal;
- close button;
- close confirmation;
- transcript generation;
- transcript configuration;
- ticket restoration/recovery on ready;
- interaction timeout fixes;
- parent-channel privacy fix.

## Known fixes

Parent-channel privacy issue was fixed in commit:

```text
041dcb14bc4f2b9db0c01c0f1b687b03e6ce379c
```

Interaction timeout hardening was applied in:

```text
1755d209f4bacf859a9da3396fef94e252140f6
```

Rebuild-command interaction timeout hardening:

```text
a6257712676522a2e31d4bf20ea773a8f4d0ca5e
```

## QA checklist

- [ ] Ticket panel exists.
- [ ] User can create a ticket.
- [ ] Required fields validate.
- [ ] Duplicate open ticket is blocked/recovered correctly.
- [ ] Thread is private.
- [ ] Correct users/roles have access.
- [ ] Unauthorized users cannot close tickets.
- [ ] Close confirmation works.
- [ ] Transcript contains expected history.
- [ ] Transcript disabled setting works.
- [ ] Ticket is archived/locked after close.
- [ ] Restart recovers open tickets.
- [ ] Stale DB tickets are reconciled.
- [ ] Interaction timeout paths are safe.

---

# 25. LOGGING

## Status

`IMPLEMENTED / QA PENDING`

## Source

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

`reaction_logs.py` exists but is intentionally not loaded.

## Current logging groups

- chat logs;
- guild/member/server logs;
- moderation logs;
- setup logs;
- system logs;
- voice logs/statistics.

## System logging

`logs.py` sends Python logging records to the configured Discord system log channel when configured.

It also writes local rotating files:

```text
logs/bot.log
logs/errors.log
```

## Logging configuration

Persistent configuration is stored in `.logging_channels.json` at runtime.

Compatibility exists for the older `server_logs` key and current `guild_logs` naming.

## Known historical fix

A logging cache/rebuild issue that produced invalid channel references was fixed. Full server rebuild on 2026-09-01 completed without the previously observed Unknown Channel / 404 logging errors.

## QA checklist

- [ ] Message create.
- [ ] Message edit.
- [ ] Message delete.
- [ ] Member join.
- [ ] Member leave.
- [ ] Member update.
- [ ] Role changes.
- [ ] Channel changes.
- [ ] Server changes.
- [ ] Moderation actions.
- [ ] Voice join/leave/move.
- [ ] Voice status changes.
- [ ] System logs.
- [ ] Missing log channel.
- [ ] Deleted log channel.
- [ ] Rebuild/recovery.
- [ ] No repeated duplicate logging.
- [ ] No stale channel IDs.

---

# 26. SERVER MANAGER / SERVER STRUCTURE

## Status

`IMPLEMENTED / QA PENDING`

## Source

```text
cogs/server_manager.py
server_structure.py
```

## Current responsibilities

- identify active TEST/production guild;
- synchronize managed category permissions;
- synchronize managed channel permissions;
- create channels with correct permissions;
- automatically apply permissions to new channels inside managed categories;
- update permissions when channels are moved between managed categories;
- owner-only `/sync_server`;
- owner-only `/channel_create`.

## Managed categories

```text
🔐 ВХОД
📢 ИНФОРМАЦИЯ
💬 ОБЩЕНИЕ
🎮 ИГРА
🎫 ПОДДЕРЖКА
🛡️ МОДЕРАЦИЯ
🔊 ГОЛОСОВЫЕ КАНАЛЫ
```

## Important safety rule

Server Manager only operates on the active environment guild.

## Known fix

Role hierarchy/server structure issue was fixed in:

```text
4dea2a9d80e05672af8c5fd77dad12a1732db0f0
```

## QA checklist

- [ ] `/sync_server` only works on active guild.
- [ ] `/channel_create` only works on active guild.
- [ ] Category permissions are correct.
- [ ] Managed channels inherit correct permissions.
- [ ] New channel auto-sync works.
- [ ] Channel move auto-sync works.
- [ ] Ticket privacy remains correct.
- [ ] Staff roles retain intended access.
- [ ] Member/Not verified access is correct.
- [ ] Production does not use TEST IDs.

---

# 27. REBUILD

## Status

`IMPLEMENTED / QA PENDING`

## Source

```text
cogs/rebuild_command.py
cogs/rebuild_test_server.py
```

Current `/rebuild_test_server` is intentionally restricted to:

```text
ENVIRONMENT=test
TEST_GUILD_ID
owner
```

It requires explicit confirmation before destructive rebuild actions.

The rebuild system recreates the configured server structure and generates/updates runtime mappings used by the rest of the bot.

## Safety requirements

- never allow TEST rebuild to target MAIN;
- never silently use a TEST map in production;
- preserve runtime databases;
- restore logging mappings correctly;
- restore role/channel references correctly;
- keep verification/tickets/logging compatible with the rebuilt structure.

## QA checklist

- [ ] Confirmation required.
- [ ] Non-owner blocked.
- [ ] Production blocked from TEST rebuild command.
- [ ] Correct roles created.
- [ ] Correct categories created.
- [ ] Correct channels created.
- [ ] Mapping generated.
- [ ] Logging mappings generated/recovered.
- [ ] Verification panel survives/reappears.
- [ ] Ticket panel survives/reappears.
- [ ] Runtime databases remain untouched.
- [ ] Existing progression remains intact.
- [ ] Post-rebuild bot startup works.

---

# 28. ADMIN PANEL

## Status

`IMPLEMENTED / QA PENDING`

## Source

```text
cogs/admin_panel.py
databases/settings.py
```

The Admin Panel is the central UI for server configuration.

Current areas:

- general settings;
- moderation settings;
- tickets;
- shop;
- logging;
- economy.

## Current configurable progression/economy settings

```text
xp_message_min
xp_message_max
xp_message_cooldown
xp_voice_per_minute
economy_message_reward
economy_daily_reward
xp_enabled
economy_enabled
```

## Moderation settings

```text
moderation_timeout_max
moderation_warn_enabled
moderation_timeout_enabled
moderation_kick_enabled
moderation_ban_enabled
moderation_owner_role
moderation_administrator_role
moderation_moderator_role
moderation_helper_role
```

## Ticket settings

```text
tickets_enabled
tickets_create_channel
tickets_channel
tickets_support_role
tickets_transcript_enabled
```

## Settings persistence

Settings are stored per guild and audited in `settings_audit`.

## QA checklist

- [ ] Unauthorized user blocked.
- [ ] Settings display current values.
- [ ] Boolean settings parse correctly.
- [ ] Numeric validation works.
- [ ] XP min/max validation works.
- [ ] Role IDs validate.
- [ ] Channel IDs validate.
- [ ] Economy adjustment works.
- [ ] Shop controls open correct flows.
- [ ] Logging channel changes persist.
- [ ] Settings survive restart.
- [ ] Audit entries are correct.

---

# 29. OWNER / OWNER DUMP

## Status

`IMPLEMENTED / QA PENDING`

## Source

```text
cogs/owner.py
cogs/owner_dump.py
```

These are owner-level infrastructure tools.

They are not part of the user-facing progression loop but are part of the operational bot architecture.

QA should verify:

- owner-only protection;
- correct operation;
- no accidental exposure of sensitive runtime data;
- compatibility with current TEST/MAIN model.

---

# 30. FUTURE MINI-GAMES

## Status

`PLANNED`

Mini-games are intentionally part of the long-term community/progression roadmap.

They can be implemented either:

1. directly through Discord bot commands/components;
2. through Discord Activities;
3. through a combination of both.

Possible future games:

- blackjack;
- quiz;
- racing;
- other small competitive/cooperative games.

Do not implement a game until its reward/economy/progression rules are defined.

The game system should not create its own isolated progression model.

---

# 31. DISCORD ACTIVITIES

## Status

`PLANNED`

Discord Activities are a future major architectural direction.

The intended model is:

```text
Discord Activity
      │
      │ game result
      ▼
InsaneBot backend/progression
      │
      ├── XP
      ├── 🪙 economy
      ├── 💎 rare currency
      ├── quests
      ├── achievements
      ├── rankings
      └── profile
```

The Activity should be treated as a **game interface**, while InsaneBot remains the central progression system.

Future Activity integration must define:

- trusted result delivery;
- user identity verification;
- guild identity verification;
- anti-cheat/anti-spoofing rules;
- reward calculation;
- idempotency so a result cannot be claimed repeatedly;
- persistence;
- failure/retry behavior.

Do not start implementation until the integration contract is designed.

---

# 32. FUTURE SOCIAL SYSTEMS

## Status

`PLANNED / NOT STARTED`

Possible future systems:

- social interactions;
- friends;
- romantic relationships.

These are deliberately lower priority than the existing progression core.

No database or command architecture should be added for them until the actual gameplay/social purpose is defined.

---

# 33. REMOVED SYSTEMS

## PvP

`REMOVED`

Do not implement unless explicitly reopened.

## Collecting

`REMOVED FOR NOW`

Possible future concepts may include collections of profile badges, frames, titles or medals, but there is no active collection system.

Do not create a collection database just to have one.

---

# 34. INTEGRATION MAP — IMPORTANT FOR FUTURE CHATS

The following relationships are intentional.

```text
XP
 ├── Levels
 ├── XP ranking
 ├── Profile
 ├── Achievements
 └── future quests

VoiceStats
 ├── Voice XP
 ├── Voice quests
 ├── Voice achievements
 ├── /voice
 └── /voice_ranking

Economy
 ├── Message rewards
 ├── Daily
 ├── Pay
 ├── Rich ranking
 ├── Shop purchases
 ├── Quest rewards
 ├── Achievement balance progress
 └── Profile

Shop
 ├── Economy
 ├── Discord roles
 └── Achievement shop_purchase event

Quests
 ├── Economy rewards
 ├── future XP rewards
 ├── future achievement integration
 └── future cosmetic rewards

Achievements
 └── Profile achievement count

Profile Customization
 └── Profile Card renderer

Verification
 └── Server access / role hierarchy

Moderation
 └── Moderation logging / punishment persistence

Tickets
 └── Support workflow / transcripts / logging

Server Manager + Rebuild
 └── Physical Discord server structure used by all systems
```

When modifying one system, inspect the systems connected to it before changing shared behavior.

---

# 35. EVENT / SHARED-STATE PRINCIPLES

Important current event interactions:

### Message activity

A user message can affect:

```text
XP
Economy
Quests
Achievements
Chat logging
```

Each system must preserve its own intended rules, especially XP cooldown versus quest/achievement message counting.

### Voice activity

A voice state update can affect:

```text
VoiceStats
XP
Quests
Achievements
Voice logging
Voice rooms
```

The persistent VoiceStats session is a foundational source of counted voice time.

### Shop purchase

A successful purchase:

```text
Economy balance decreases
        ↓
Discord role is assigned if configured
        ↓
shop_purchase event
        ↓
Achievements update
```

A failed role assignment must refund the purchase.

### Profile

Profile reads data from existing persistence systems rather than creating duplicate counters.

---

# 36. KNOWN TECHNICAL AUDIT ITEMS

These are known issues/candidates discovered during repository inspection. They are **not silently considered fixed**.

## HIGH PRIORITY / BEFORE FINAL QA

### 1. Quest reward atomicity

Quest completion and economy reward currently happen through separate persistence operations.

Current flow is effectively:

```text
mark quest completed
      ↓
add economy reward
```

A crash between those operations could create an edge case where completion is stored but reward is not granted.

This needs to be explicitly tested and, if necessary, hardened before `QA PASSED`.

Do not redesign it blindly; inspect the current database behavior first.

### 2. Moderation logging failure window

Some moderation flows perform the Discord punishment and then attempt logging. A logging failure can affect the user-facing operation depending on the exact path.

QA must determine whether the resulting behavior is acceptable.

### 3. Production verification condition

The current `Verification.on_guild_role_create` path contains a TEST-guild-specific condition.

Before production is considered fully supported, audit whether that condition should use the active environment target instead.

### 4. Profile card font/visual quality

The current renderer uses `DejaVuSans.ttf` with a default font fallback.

Cyrillic/Unicode rendering and long names should be explicitly tested.

## MEDIUM / LOW PRIORITY AUDIT ITEMS

### 5. Active-days achievement semantics

`active_7_days` currently records activity days from message/voice activity. Its exact intended definition should remain consistent with the product wording.

### 6. Voice achievement timing

Some voice achievement checks occur on voice-state transitions, so an achievement may unlock after a session is completed rather than immediately while the user is still connected.

This is acceptable unless QA shows it conflicts with the intended UX.

### 7. Legacy `get_roles.py`

Exists but is not loaded. Determine during technical cleanup whether it should remain as legacy or be removed.

### 8. Disabled `reaction_logs.py`

Exists but is not loaded. Keep disabled unless reaction logging becomes an explicit requirement.

### 9. DM/guild-only command behavior

Profile and other guild systems should be checked for clean behavior if invoked outside a guild.

Do not add speculative checks everywhere; fix only demonstrated behavior.

---

# 37. RECENT FIX HISTORY / IMPORTANT COMMITS

These commits are useful context when debugging regressions.

```text
4dea2a9d80e05672af8c5fd77dad12a1732db0f0
Server/role hierarchy fix.

041dcb14bc4f2b9db0c01c0f1b687b03e6ce379c
Ticket parent-channel privacy fix.

1755d209f4bacf859a9da3396fef94e252140f6
Ticket interaction timeout hardening.

a6257712676522a2e31d4bf20ea773a8f4d0ca5e
Rebuild-command interaction timeout hardening.

64c80fb3ab96fcb954ae7524d799a57feaa0247f
Moderation interaction timeout hardening.

d2c0509599b11359c1bc056dcac88c08deb7b141
Moderation modal now reuses the loaded Moderation COG.

3767d4b7406f61b73437250ecc577259cd589371
Verification persistent view registration hardened.

55ac0a9043eed6cffc5e8d8d2fa60bf5fa020f21
Voice achievement switched to persistent actual voice time.

b90d279960ba0a83822afd00fdf2e2aa0c39db07
Profile customization database added.

231fdab6110a6818028f4a2095d322be8de06884
Profile card renderer updated for customization.

06af69d097c5a9e45638e7f3a3897528d94f5057
Profile customization command/integration added.

f4321d9aa022b7085c19b510cf965d073d4ed544
TEST/MAIN config and server-map isolation fix.

f19eedcf4f3bbc1476aabc9f17f6f355602e5590
Logging map compatibility fix.
```

Current audited baseline is `f19eedcf4f3bbc1476aabc9f17f6f355602e5590`.

GitHub Actions workflow `Check` run #214 for this baseline completed successfully.

---

# 38. CURRENT DEVELOPMENT PHASE

## Current phase

**FUNCTIONALITY COMPLETE FOR THE CURRENT CORE SET — DETAILED QA NOT STARTED.**

The following three systems were the required pre-QA focus:

```text
Quests
Achievements
Profile Card
```

All three now have implementation in the source.

Profile customization is also already implemented on top of the profile-card architecture.

Therefore the project should **not** go back and reimplement these systems from scratch merely because QA has not happened yet.

The next step is integration verification, followed by detailed QA.

---

# 39. LOCKED DEVELOPMENT ORDER

This order is now the default project order.

## Phase 1 — Core functionality

Already implemented:

1. Quests
2. Achievements
3. Generated Profile Card
4. Profile customization

## Phase 2 — Integration audit

Before detailed QA, verify the connected systems together:

1. XP ↔ Levels
2. XP ↔ Economy
3. XP ↔ Quests
4. XP ↔ Achievements
5. Economy ↔ Daily
6. Economy ↔ Shop
7. Economy ↔ Quests
8. Economy ↔ Achievements
9. Shop ↔ Achievements
10. VoiceStats ↔ XP
11. VoiceStats ↔ Quests
12. VoiceStats ↔ Achievements
13. Achievements ↔ Profile Card
14. Profile Customization ↔ Profile Card
15. Commands ↔ COG loading/sync
16. Rebuild ↔ server mappings
17. Rebuild ↔ logging
18. Rebuild ↔ verification
19. Rebuild ↔ tickets
20. Restart ↔ persistent progression

The integration audit is intended to catch:

- missing imports;
- stale references;
- wrong event names;
- duplicate state;
- unloaded COGs;
- broken command sync;
- persistence gaps;
- restart/recovery gaps;
- guild/config isolation problems.

## Phase 3 — Detailed QA

Only after Phase 2 is complete.

QA must be done **one system at a time**, not as an uncontrolled full-server test.

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
16. Logging groups
17. Runner
18. Full regression

When a system is QA-tested, update its row/checklist here immediately.

## Phase 4 — Technical audit / cleanup

After functional QA:

- dead code;
- stale imports;
- stale references;
- duplicate logic;
- async correctness;
- interaction acknowledgement;
- permission/hierarchy correctness;
- channel/thread correctness;
- TEST/MAIN isolation;
- database consistency;
- event ordering;
- race conditions;
- exception handling;
- COG architecture;
- runner behavior;
- documentation/comments.

Only after this phase should the project be considered technically mature enough for broader expansion.

---

# 40. QA RECORD

This section is intentionally persistent. Every future QA session should update it instead of relying on chat history.

## Current QA state

```text
Detailed QA started: NO
Current QA system: NONE
Current QA phase: PRE-QA / INTEGRATION AUDIT
```

## Verified already

### Verification

`LIVE VERIFIED`

Previously verified role hierarchy and basic verification flow as documented above.

### Shop

`RUNTIME TESTED`

The scenarios listed in Section 15 were tested on 2026-08-31.

### Server rebuild/logging

A full rebuild on 2026-09-01 completed without the previously observed Unknown Channel / 404 logging errors.

### GitHub CI

Latest known Check workflow:

```text
Run: #214
Commit: f19eedcf4f3bbc1476aabc9f17f6f355602e5590
Status: completed
Conclusion: success
```

CI success is **not** equivalent to runtime QA.

---

# 41. WHAT NOT TO DO IN A NEW CHAT

A new chat must not:

- assume this is an RPG;
- reintroduce PvP;
- reintroduce collecting without an explicit decision;
- invent talismans/equipment/loot boxes/consumables;
- redesign the shop UI without request;
- start mini-games before core QA unless explicitly requested;
- start Discord Activities implementation before its integration contract is designed;
- reset databases to solve development issues;
- replace working systems merely because they have not yet been QA-tested;
- create duplicate voice/XP/economy counters when existing persistence already provides the data;
- claim QA completion from source inspection or CI alone;
- ignore TEST/MAIN isolation;
- assume `PROJECT_STATE.md` is more current than actual source code.

---

# 42. HOW TO CONTINUE DEVELOPMENT FROM THIS FILE

When opening a new development chat, the default procedure is:

1. Read this entire `PROJECT_STATE.md`.
2. Inspect current GitHub `main` and verify the source baseline.
3. Determine the exact system being worked on.
4. Check its status in the master table.
5. Inspect connected systems from the integration map.
6. Make the smallest necessary change.
7. Check callers/imports/events/references.
8. Validate with CI/runtime tests when appropriate.
9. Update this file with the result.
10. Commit directly to `main`.

For code fixes, return complete replacement functions/fragments rather than abbreviated snippets.

For QA, record:

```text
Date
System
Scenario
Expected
Actual
Result
Regression notes
```

For a discovered bug, record it in the relevant system section and in the technical audit list if it affects multiple systems.

---

# 43. NEXT ACTION — DO THIS FIRST

**Do not begin feature expansion yet.**

The immediate task after this state rewrite is:

```text
1. Integration audit of the current implemented core.
2. Resolve only critical integration problems found there.
3. Update PROJECT_STATE with the fixes/results.
4. Begin detailed QA one system at a time.
```

The first QA target should be **Tickets**, followed by the order in Section 39.

After the core systems reach `QA PASSED`, the next major product-development stage is:

```text
Mini-games
      ↓
Discord Activities
      ↓
Integration with XP / Economy / Quests / Achievements / Rankings / Profile
```

Social systems remain future work and PvP/Collecting remain outside the active roadmap.

---

# 44. FINAL PRODUCT CHECKPOINT

The current project is considered conceptually complete at the following core level:

```text
Infrastructure
    ✓
Server management
    ✓
Verification
    ✓
Moderation
    ✓
Tickets
    ✓
Logging
    ✓
Voice
    ✓
XP / Levels
    ✓
Economy / Daily
    ✓
Shop
    ✓
Quests
    ✓
Achievements
    ✓
Profile Card
    ✓
Profile Customization
    ✓
```

The checkmarks above mean **implemented/established**, not automatically QA-passed.

The next project milestone is:

> **Integration-clean core → system-by-system QA → regression → technical cleanup → expansion into mini-games/Discord Activities.**

This roadmap is binding until the user explicitly changes the product direction.
