import os
from pathlib import Path
from typing import Dict, Iterable, Tuple

import disnake

BASE_DIR = Path(__file__).resolve().parent
ASSETS_DIR = BASE_DIR / "img"

# The token is now expected to be stored in an environment variable to avoid
# committing secrets. Configure the token locally before running the bot:
#   set DISCORD_TOKEN=your_token_here
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")

# Core cog paths
COGS: Tuple[str, ...] = (
    "cogs.moderation_cmd.one_used",
    "cogs.moderation_cmd.moderation",
    "cogs.user_cmd.get_roles",
    "cogs.user_cmd.create_voice",
    "cogs.logging.logs",
    "cogs.logging.chat_logs",
)

# Channel and role configuration
CHANNEL_LOGS: Dict[str, int] = {
    "moderation_logs": 1330604583000473732,
    "chat_logs": 1330604289957302350,
    "guild_logs": 1338651230565695558,
}

CHANNELS: Dict[str, int] = {
    "create_voice": 1336547276059050004,
}

MODERATION_ROLES: Dict[str, int] = {
    "owner": 519209664748191759,
    "administrator": 519209661535223808,
    "moderator": 519209662181277726,
    "helper": 519209663519129600,
}

OTHER_ROLES: Dict[str, int] = {
    "Not verified": 1334302190625361994,
}

GAME_ROLES: Dict[str, int] = {
    "Dota 2": 1332487694252638320,
    "CS 2": 1332487739932934165,
    "PAYDAY 2": 1332487809600323624,
    "Bellwright": 1334981997780795444,
    "Stardew Valley": 1334984540862808205,
}

GAME_ROLE_OPTIONS: Tuple[disnake.SelectOption, ...] = tuple(
    disnake.SelectOption(label=name, value=str(role_id))
    for name, role_id in GAME_ROLES.items()
)

ASSETS: Dict[str, Path] = {
    "rules_image": ASSETS_DIR / "RULES.png",
}


def ensure_asset(path: Path) -> Path:
    """Validate that a configured asset exists on disk."""
    if not path.exists():
        raise FileNotFoundError(f"Configured asset was not found: {path}")
    return path


def iter_role_ids(role_mapping: Dict[str, int]) -> Iterable[int]:
    """Helper to iterate over role IDs from a mapping."""
    return role_mapping.values()
