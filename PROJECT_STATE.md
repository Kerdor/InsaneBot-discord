# InsaneBot-discord — Project State

Repository: https://github.com/Kerdor/InsaneBot-discord

This file is the persistent project context. Before making changes, read the current repository state and this document. Decisions marked as agreed should not be changed without a new decision.

## Development rules

- Do not ask for permission before implementing an already agreed change.
- Always inspect the current `main` before editing; do not rely on old chat snippets.
- Preserve existing architecture, names, function order and formatting unless a change is necessary.
- Make the smallest necessary change.
- Do not add unnecessary libraries, checks or abstractions.
- Do not replace code with `...`.
- When changing a function, provide the complete replacement function when reporting the change.
- Check related callers/references after changes so removed methods or variables are not left behind.
- Test or validate changes when practical.
- Commit completed changes directly to `main` unless explicitly asked otherwise.
- Do not re-ask questions already settled in this file.

## Project concept

InsaneBot is a Discord moderation/game/social bot. It must NOT depend on an RPG system. The main sources of activity are chat, voice presence, social interactions and optional game systems.

Planned systems:

1. Levels and XP
2. Economy
3. Shop
4. Profiles
5. Daily rewards
6. Quests
7. PvP
8. Mini-games
9. Rankings
10. Achievements
11. Collecting
12. Profile customization
13. Social interactions
14. Voice-time rankings
15. Friends
16. Romantic relationships
17. Tickets
18. Moderation
19. Logging

Systems are implemented incrementally, not all at once.

## Agreed server structure

```text
🔐 ВХОД
└── 🔐・верификация

📢 ИНФОРМАЦИЯ
├── 📌・правила
├── 📢・новости
├── 📖・гайды
└── ℹ️・информация

💬 ОБЩЕНИЕ
└── 💬・чат

🎮 ИГРА
├── 💬・игровой-чат
├── 🏆・рейтинги
└── 🎮・игровая-панель

🎫 ПОДДЕРЖКА
└── 🎫・тикеты

🛡️ МОДЕРАЦИЯ
├── 📜・логи
└── 🔧・панель-модерации

🔊 ГОЛОСОВЫЕ КАНАЛЫ
├── 🔊・Общий 1
├── 🔊・Общий 2
├── 👥・Для двоих [2]
├── 👥・Для троих [3]
└── ➕・Создать канал
```

Names may later be normalized stylistically, but the structure is agreed.

## Rebuild

`rebuild` must create/restore categories, channels, forums, tags, roles, permissions and persistent bot panels. It should use actual Discord state plus persisted configuration rather than relying only on hardcoded IDs. Existing objects should be reused; missing objects should be recreated without duplicates.

## Roles

Base roles:

- 👑 Владелец
- 🛡️ Администратор
- 🔨 Модератор
- 🧪 Хелпер
- 👤 Участник
- 🔐 Не верифицирован

Milestone level roles may exist at selected levels such as 5, 10, 20, 30. Do not create a Discord role for every level.

Do not give everyone Administrator unnecessarily.

## Verification

Before verification a user sees only:

```text
🔐 ВХОД
└── 🔐・верификация
```

Verification uses a small CAPTCHA implemented by the bot. After success the user receives `👤 Участник` and normal server access. Moderation remains staff-only.

## Profiles

Profiles contain level, XP, message count, voice time, ranking, balance, rare currency, achievements, friends, relationships, cosmetics and inventory.

Profile cards can be generated as images. There should be both individual cosmetic items and ready-made polished sets.

Public by default:
- level
- XP
- message count
- voice time
- ranking

User can hide:
- balance
- rare currency
- achievements
- friends
- relationships

Inventory is never public.

Voice-time breakdown by individual channel is private to the user.

## XP and levels

XP sources can include chat activity, voice activity, games, achievements, quests and other activities.

Level benefits:
- shown in profile/rankings
- cosmetics unlocks
- larger daily rewards
- additional/advanced social actions
- special server roles
- other bonuses

Basic social actions should not be unnecessarily locked behind levels.

## Economy

There is one normal currency.

There is also a rare special currency with no real-money purchase. It is intentionally difficult to obtain, for example through every 5th level, achievements, daily quests and other special activities.

Inventory exists and is never public.

## Social system

Friends are separate from romantic relationships.

Social actions include examples such as:
- 🤗 hug
- 💋 kiss
- 👊 hit

Basic actions should be available broadly. Relationship-specific actions may unlock through relationship progression.

## Relationships

Relationships are monogamous: one romantic partner at a time.

Relationships have their own XP and levels. Future relationship progression may unlock additional actions.

Future system: marriage.

On breakup:
- relationship ends
- history remains private
- relationship progress is reduced by about 50%
- a later relationship with the same person does not necessarily start from zero

## Voice system

AFK channels do NOT count toward voice time.

Voice time is stored as:
- total voice time
- private per-channel breakdown
- ranking by voice time

Voice time may also award XP.

Discord status changes (Online/Idle/DND/Offline) are NOT logged.

### Permanent voice channels

- 2 general voice channels
- one channel limited to 2
- one channel limited to 3
- `➕・Создать канал`

### User rooms

`➕・Создать канал` is a voice trigger. Entering it ALWAYS moves the user into their selected primary room.

If no room exists, create it, restore settings, create its text control channel and move the user there.

If the user is already in another voice channel, still move them.

User room default limit is `0`, meaning unlimited. Owner can set 1–99.

A user room has a dedicated text control channel with buttons for:
- rename
- limit
- add co-owner
- grant access
- remove access
- set as primary
- friends-only
- info

The owner has full room management: name, limit, access, users, co-owners, privacy and other room controls.

### Room persistence

The physical Discord channel is temporary. Room configuration is stored in the database.

When a room becomes empty, its physical channel may be deleted while configuration remains in the database. When the user later enters `➕・Создать канал`, the room is recreated with saved settings and permissions.

### Co-owners

A room can have multiple co-owners.

A user can be co-owner of multiple rooms.

A user chooses one available room as their primary room. Entering `➕・Создать канал` moves them to that primary room.

A user who is only a normal member of someone else's room cannot make it their primary room without owner/co-owner approval.

### Timeout

Timeout prevents creation of a NEW user room.

It does NOT delete or disable an existing room. Existing room use and management remain available. After timeout ends, creation is available again.

### Ban

If the owner is banned, the room is not immediately deleted. Co-owners and allowed users keep access. Settings remain. When the owner returns, the room remains configured.

## Voice statistics/logging

Voice events should not create spam. Avoid one log message for every join/leave when possible. Prefer compact session information such as entry time, exit time and duration.

Voice logs may include:
- voice join/leave
- channel moves
- mute/deaf changes
- user-room creation/deletion

Voice logs should be separate from other noisy logs.

## Tickets

Support uses one universal ticket system.

Desired behavior: each ticket is private to its author and moderators.

Discord Forum Posts cannot provide the required per-user privacy in the same way as private threads, so implementation must use an appropriate private Discord thread/channel mechanism rather than pretending ordinary forum posts are private.

Tickets should not be automatically deleted after 24–48 hours. History should remain available and important ticket data should be stored in the database.

### Ticket implementation state

Completed:
- persistent SQLite ticket records
- one open ticket per user
- private Discord threads
- author + moderation access
- persistent creation panel
- category selection
- moderation notification
- close button and `/ticket_close`
- closed ticket metadata
- transcript saved as `.txt` in the ticket parent channel
- closed threads archived and locked
- open ticket recovery after bot restart

## Moderation

Moderation is available through both slash commands and a button-based panel.

Example commands:
- `/warn`
- `/timeout`
- `/kick`
- `/ban`
- `/unban`
- `/history`
- `/user`

Panel may contain:
- users
- punishments
- tickets
- statistics
- history
- settings

Panel actions must respect the moderator's permissions.

### Moderation implementation state

Completed:
- persistent SQLite punishment history
- `/warn`
- `/timeout`
- `/kick`
- `/ban`
- `/unban`
- `/history`
- persistent moderation panel
- panel buttons for warn, timeout, kick and ban
- ephemeral modal input for target user ID, reason and timeout duration
- moderation action logging
- staff-role permission checks
- panel recovery/creation after restart

## Logging

Logs live inside the moderation area.

Logical groups:
- 💬 messages
- 👤 members
- 🛡️ moderation
- 📁 server
- 🔊 voice
- 🤖 system

### Message logs

Log:
- new messages
- deletion
- bulk deletion
- edits
- relevant attachments/links if useful

### Reactions

Reaction add/remove events are OFF by default because they can generate excessive noise. Make this configurable later if needed.

### Status

Discord Online/Idle/DND/Offline changes are not logged.

### Bot logs

Log important bot events such as critical errors, rebuilds, structure restoration, object creation/deletion and configuration changes.

## Game panel

`🎮・игровая-панель` is a persistent bot message with buttons such as:

- 👤 Profile
- 🎒 Inventory
- 🛒 Shop
- 🎁 Daily reward
- 📋 Quests
- 🏆 Achievements
- 📊 Rankings
- 👥 Friends
- ❤️ Relationships
- 🎮 Mini-games
- ⚔️ PvP

Menus should preferably be user-specific/ephemeral to avoid channel spam.

## Information

Guides belong in `📢 ИНФОРМАЦИЯ`, not a separate category. Example: `📖・гайды`.

## Current implementation state

Known completed repository changes before this document:

- voice room database added
- `create_voice.py` substantially changed for persistent user rooms
- room settings persistence
- room recreation after physical channel deletion
- default room limit 0 and configurable 0–99
- text control channel
- access management
- multiple co-owners
- primary-room concept
- timeout behavior
- banned-owner behavior
- database preparation for friends-only setting
- `installed.flag` checked and removed because it was unused
- `.python-version` retained
- persistent voice statistics
- AFK exclusion and channel-move handling
- voice recovery after restart
- ticket database and private-thread ticket system
- ticket creation panel
- ticket categories
- ticket moderation notifications
- ticket transcripts and persistent close metadata
- moderation database
- moderation slash commands
- persistent moderation panel
- functional moderation panel actions with ephemeral modals

## Immediate next work

Continue from the current repository state.

Priority order:

1. Verify ticket and moderation systems locally and fix runtime issues found in testing.
2. Finish/verify logging coverage and structure restoration.
3. Implement XP/levels using existing chat and voice activity.
4. Implement economy, daily rewards and inventory.
5. Implement profiles and profile cards.
6. Implement friends and social actions.
7. Implement romantic relationships.
8. Then achievements/quests/mini-games/PvP/collections/cosmetics.

Do not redo already agreed product decisions. Continue implementation from the actual repository state.
