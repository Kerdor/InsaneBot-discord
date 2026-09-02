"""Discord Activity backend lifecycle integration."""

import logging
import os
import threading

from activities.server import create_activity_server

logger = logging.getLogger(__name__)


class ActivityServerCog:
    """Keep the local Activity OAuth backend alive with the bot process."""

    def __init__(self, bot):
        self.bot = bot
        host = os.getenv("DISCORD_ACTIVITY_HOST", "127.0.0.1").strip() or "127.0.0.1"
        port_value = os.getenv("DISCORD_ACTIVITY_PORT", "8080").strip() or "8080"
        try:
            port = int(port_value)
        except ValueError as exc:
            raise RuntimeError("DISCORD_ACTIVITY_PORT должен быть числом") from exc
        if not 1 <= port <= 65535:
            raise RuntimeError("DISCORD_ACTIVITY_PORT должен быть в диапазоне 1-65535")

        self.server = create_activity_server(host, port)
        self.thread = threading.Thread(
            target=self.server.serve_forever,
            name="insanebot-activity-server",
            daemon=True,
        )
        self.thread.start()
        logger.info("Activity backend started on %s:%s", host, port)

    def cog_unload(self) -> None:
        """Stop the Activity backend when this extension is unloaded."""
        self.server.shutdown()
        self.server.server_close()
        logger.info("Activity backend stopped")


def setup(bot) -> None:
    """Register the Activity backend lifecycle cog."""
    bot.add_cog(ActivityServerCog(bot))
