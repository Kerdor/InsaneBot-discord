import os
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any, Iterable
import disnake
from disnake import SelectOption, ButtonStyle

class BotConfig:
    # File paths (declared first as they're used by other variables)
    BASE_DIR: Path = Path(__file__).resolve().parent
    ASSETS_DIR: Path = BASE_DIR / "img"
    
    # Bot configuration
    TOKEN: str = "MTMyOTg2MzY5NzM1ODc4MjUwNA.G0tBzW.rvRrZ4ZUeHNtWBqwWWFRVUMFBosU4abLig_rbs"
    PREFIX: str = "/"
    TEST_GUILDS: List[int] = [519209364280573954]
    
    # Cogs to load
    COGS: Tuple[str, ...] = (
        "cogs.owner",
        "cogs.moderation_cmd.one_used",
        "cogs.moderation_cmd.moderation",
        "cogs.user_cmd.get_roles",
        "cogs.user_cmd.create_voice",
        "cogs.logging.chat_logs",
        "cogs.logging.guild_logs",
        "cogs.logging.moderation_logs"
    )
    
    # Channel IDs
    CHAT_LOGS_CHANNEL: int = 1446250206201905295
    GUILD_LOGS_CHANNEL: int = 1446250230743044217
    MODERATION_LOGS_CHANNEL: int = 1446250190205096068
    
    # Logging and channels configuration
    LOG_COLORS: Dict[str, int] = {
        'GREEN': 0x00ff00,
        'ORANGE': 0xffa500,
        'RED': 0xff0000,
        'BLUE': 0x3498db,
    }
    
    CHANNEL_LOGS: Dict[str, int] = {
        "moderation_logs": 1446250190205096068,
        "chat_logs": 1446250206201905295,
        "guild_logs": 1446250230743044217,
    }
    
    CHANNELS: Dict[str, int] = {
        "create_voice": 1336547276059050004,
    }
    
    # Roles configuration - moved to module level for easier access
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
    
    # Assets
    ASSETS: Dict[str, Path] = {
        "rules_image": ASSETS_DIR / "RULES.png",
    }
    
    # Dynamic options (declared after all dependencies)
    GAME_ROLE_OPTIONS: Tuple[SelectOption, ...] = None
    
    # Button styles
    class ButtonStyles:
        PRIMARY = ButtonStyle.primary
        SECONDARY = ButtonStyle.secondary
        SUCCESS = ButtonStyle.success
        DANGER = ButtonStyle.danger
    
    @classmethod
    def initialize(cls) -> None:
        """Initialize dynamic configurations that depend on other variables"""
        cls.GAME_ROLE_OPTIONS = tuple(
            SelectOption(label=name, value=str(role_id))
            for name, role_id in cls.GAME_ROLES.items()
        )
    
    @classmethod
    def validate(cls) -> None:
        if not cls.TOKEN or cls.TOKEN == "your_bot_token_here":
            raise ValueError("Bot token is not set in config.py")
        if not all(isinstance(guild_id, int) for guild_id in cls.TEST_GUILDS):
            raise ValueError("TEST_GUILDS must contain only integers")
        if not all(isinstance(cog, str) for cog in cls.COGS):
            raise ValueError("COGS must contain only strings")

# Initialize the configuration
BotConfig.initialize()

# Make important configurations available at module level
MODERATION_ROLES = BotConfig.MODERATION_ROLES
LOG_COLORS = BotConfig.LOG_COLORS
CHANNELS = BotConfig.CHANNELS
GAME_ROLE_OPTIONS = BotConfig.GAME_ROLE_OPTIONS
GAME_ROLES = BotConfig.GAME_ROLES


def ensure_asset(path: Path) -> Path:
    """Validate that a configured asset exists on disk."""
    if not path.exists():
        raise FileNotFoundError(f"Configured asset was not found: {path}")
    return path


def iter_role_ids(role_mapping: Dict[str, int]) -> Iterable[int]:
    """Helper to iterate over role IDs from a mapping."""
    return role_mapping.values()
