"""Discord Activity backend lifecycle integration."""

import logging
import threading

from activities.server import create_activity_server
from config import BotConfig

logger = logging.getLogger(__name__)


class ActivityServerCog:
    """Keep the local Activity OAuth backend alive with the bot process."""

    def __init__(self, bot):
        self.bot = bot
        self.server = create_activity_server(
            BotConfig.ACTIVITY_HOST,
            BotConfig.ACTIVITY_PORT,
        )
        self.thread = threading.Thread(
            target=self.server.serve_forever,
            name="insanebot-activity-server",
            daemon=True,
        )
        self.thread.start()
        logger.info(
            "Activity backend started on %s:%s",
            BotConfig.ACTIVITY_HOST,
            BotConfig.ACTIVITY_PORT,
        )

    def cog_unload(self) -> None:
        """Stop the Activity backend when this extension is unloaded."""
        self.server.shutdown()
        self.server.server_close()
        logger.info("Activity backend stopped")


def setup(bot) -> None:
    """Register the Activity backend lifecycle cog."""
    bot.add_cog(ActivityServerCog(bot))
