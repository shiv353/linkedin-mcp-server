"""Middleware that serializes API request execution across server processes."""

from __future__ import annotations

import asyncio
import logging
import time

from typing import Any

from fastapi import HTTPException
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

from linkedin_mcp_server.config import get_config
from linkedin_mcp_server.exceptions import BrowserBusyError
from linkedin_mcp_server.profile_lease import get_profile_lease

logger = logging.getLogger(__name__)


class SequentialExecutionMiddleware(BaseHTTPMiddleware):
    """Ensure only one API request at a time drives the shared LinkedIn browser.

    Two layers, because one is not enough:

    * an ``asyncio.Lock`` serializes calls inside this process;
    * the profile lease serializes calls across processes, where each server
      instance shares the same Chromium profile.
    """

    def __init__(self, app: Any) -> None:
        super().__init__(app)
        self._lock = asyncio.Lock()

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        # Only serialize /api/ routes — let docs, health, etc. pass through
        if not request.url.path.startswith("/api/"):
            return await call_next(request)

        wait_started = time.perf_counter()
        logger.debug(
            "Waiting for scraper lock for %s %s", request.method, request.url.path
        )

        async with self._lock:
            wait_seconds = time.perf_counter() - wait_started
            logger.debug(
                "Acquired scraper lock for %s %s after %.3fs",
                request.method,
                request.url.path,
                wait_seconds,
            )
            return await self._run_owning_the_profile(request, call_next)

    async def _run_owning_the_profile(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        """Run the request while this process owns the browser profile."""
        from linkedin_mcp_server.drivers.browser import (
            note_activity,
            note_call_started,
            release_profile_if_idle_or_requested,
        )

        lease = get_profile_lease()
        acquired = lease.try_acquire()
        if not acquired:
            budget = get_config().browser.browser_wait_seconds
            acquired = await lease.acquire(timeout=budget)

        if not acquired:
            logger.info(
                "Request %s %s gave up waiting for the shared browser",
                request.method,
                request.url.path,
            )
            raise HTTPException(status_code=503, detail=str(BrowserBusyError()))

        hold_started = time.perf_counter()
        try:
            note_call_started()
            return await call_next(request)
        finally:
            hold_seconds = time.perf_counter() - hold_started
            logger.debug(
                "Released scraper lock for %s %s after %.3fs",
                request.method,
                request.url.path,
                hold_seconds,
            )
            note_activity()
            lease.release()
            try:
                await release_profile_if_idle_or_requested()
            except Exception:
                logger.debug("Profile handoff check failed", exc_info=True)
