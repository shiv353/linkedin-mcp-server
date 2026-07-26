"""Progress callbacks for REST API endpoints.

Replaces the MCP-specific MCPContextProgressCallback with a
logging-based implementation that works without FastMCP Context.
"""

import logging
from typing import Any

from linkedin_mcp_server.callbacks import ProgressCallback

logger = logging.getLogger(__name__)


class LoggingProgressCallback(ProgressCallback):
    """Callback that logs progress instead of reporting to MCP clients."""

    async def on_start(self, scraper_type: str, url: str) -> None:
        logger.info("Starting %s: %s", scraper_type, url)

    async def on_progress(self, message: str, percent: int) -> None:
        logger.info("Progress %d%%: %s", percent, message)

    async def on_complete(self, scraper_type: str, result: Any) -> None:
        logger.info("Completed %s", scraper_type)

    async def on_error(self, error: Exception) -> None:
        logger.error("Scraping error: %s", error)
