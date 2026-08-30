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

## Current implementation state

Completed major systems:
- persistent voice statistics and user-room system
- private-thread ticket system with transcripts and recovery
- moderation database, slash commands and persistent moderation panel
- message, bulk-delete, guild/member, moderation, voice and system logging
- reaction logging implementation exists but remains disabled by default
- persistent XP and levels
- persistent economy with normal currency, daily reward and user-to-user payments
- persistent admin settings database with settings audit history
- `/admin_panel` restricted to owner/administrator
- admin panel controls for XP/economy values
- admin panel controls for selecting logging destinations by log type

## Economy decisions

There is one normal currency.

There is also a rare special currency with no real-money purchase. It is intentionally difficult to obtain, for example through every 5th level, achievements, daily quests and other special activities.

There is NO RPG item system. Do not invent talismans, energy drinks, loot boxes or consumable RPG mechanics unless explicitly decided later.

Current economy commands:
- `/balance`
- `/daily`
- `/pay`

Current default activity reward is 2 coins per XP-eligible message. It uses the same anti-spam eligibility/cooldown concept as message XP.

## Admin panel

The admin panel is intended to become the central configuration UI instead of hardcoding gameplay/server settings.

Current sections:
- ⚙️ Settings: XP and economy settings
- 📋 Logging: per-log-type destination configuration

Settings are persisted in `databases/settings.db`. Configuration changes are recorded in `settings_audit`.

Only the Owner and Administrator roles may use the panel.

Future sections should include:
- 🛡️ Moderation
- 🎫 Tickets
- 💰 Economy
- 📈 XP
- ⚙️ General

Do not create settings for systems that do not yet exist.

## XP and levels

Completed:
- persistent SQLite XP storage
- XP from chat messages
- 60-second per-user message XP cooldown
- random 15–25 XP per eligible message
- XP from counted voice activity
- 5 XP per completed voice minute
- AFK voice channels excluded
- level calculation and persistence
- `/level`
- `/xp_ranking`
- active voice XP recovery after bot restart using persisted voice sessions

Level formula currently uses `100 * level²` as the cumulative threshold: level 1 starts at 0 XP, level 2 at 100 XP, level 3 at 400 XP, etc.

## Logging

Logs live inside the moderation area.

Logical groups:
- 💬 messages
- 👤 members / server
- 🛡️ moderation
- 📁 server
- 🔊 voice
- 🤖 system

Reaction logs remain OFF by default because they are noisy.

## Immediate next work

1. Validate the combined logging/XP/economy/admin stack locally and fix runtime/API issues.
2. Complete admin panel sections for moderation and tickets using only existing settings/mechanics.
3. Implement profiles and profile cards.
4. Implement friends and social actions.
5. Implement romantic relationships.
6. Then achievements/quests/mini-games/PvP/collections/cosmetics.

Do not redo already agreed product decisions. Continue implementation from the actual repository state.
