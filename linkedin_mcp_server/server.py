"""FastAPI server implementation for LinkedIn REST API.

Creates and configures the FastAPI app with comprehensive LinkedIn endpoint suite
including person profiles, company data, job information, and session management.
"""

import asyncio
import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager, suppress

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from linkedin_mcp_server import __version__
from linkedin_mcp_server.bootstrap import (
    get_runtime_policy,
    initialize_bootstrap,
    start_background_browser_setup_if_needed,
)
from linkedin_mcp_server.drivers.browser import (
    close_browser,
    watch_for_handoff_requests,
)
from linkedin_mcp_server.sequential_tool_middleware import SequentialExecutionMiddleware
from linkedin_mcp_server.api.person import router as person_router
from linkedin_mcp_server.api.company import router as company_router
from linkedin_mcp_server.api.job import router as job_router
from linkedin_mcp_server.api.messaging import router as messaging_router
from linkedin_mcp_server.api.feed import router as feed_router
from linkedin_mcp_server.api.session import router as session_router

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Manage browser lifecycle — startup and shutdown."""
    logger.info("LinkedIn API Server starting...")
    initialize_bootstrap(get_runtime_policy())
    await start_background_browser_setup_if_needed()

    handoff_watch = asyncio.create_task(
        watch_for_handoff_requests(), name="linkedin-profile-handoff"
    )
    try:
        yield
    finally:
        logger.info("LinkedIn API Server shutting down...")
        handoff_watch.cancel()
        with suppress(asyncio.CancelledError):
            await handoff_watch
        await close_browser()


def create_app() -> FastAPI:
    """Create and configure the FastAPI app with all LinkedIn endpoints."""
    app = FastAPI(
        title="LinkedIn API Server",
        description="REST API for LinkedIn data extraction through browser automation.",
        version=__version__,
        lifespan=lifespan,
    )

    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Sequential execution middleware — serializes all /api/ requests
    app.add_middleware(SequentialExecutionMiddleware)

    # Register all API routers
    app.include_router(person_router)
    app.include_router(company_router)
    app.include_router(job_router)
    app.include_router(messaging_router)
    app.include_router(feed_router)
    app.include_router(session_router)

    @app.get("/", tags=["health"])
    async def root() -> dict[str, str]:
        """Health check endpoint."""
        return {
            "status": "ok",
            "service": "linkedin-api-server",
            "version": __version__,
        }

    return app
