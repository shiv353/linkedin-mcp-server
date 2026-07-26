"""Progress callback base class for LinkedIn scraping operations."""

from typing import Any


class ProgressCallback:
    """Base callback class for progress tracking."""

    async def on_start(self, scraper_type: str, url: str) -> None:
        pass

    async def on_progress(self, message: str, percent: int) -> None:
        pass

    async def on_complete(self, scraper_type: str, result: Any) -> None:
        pass

    async def on_error(self, error: Exception) -> None:
        pass
