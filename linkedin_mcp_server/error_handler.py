"""Centralized error handling for LinkedIn API Server using FastAPI HTTPException.

Provides raise_api_error() which maps known LinkedIn exceptions to user-friendly
HTTPException responses with appropriate HTTP status codes.
"""

import logging
from typing import NoReturn

from fastapi import HTTPException

from linkedin_mcp_server.core.exceptions import (
    AuthenticationError,
    ElementNotFoundError,
    LinkedInScraperException,
    NetworkError,
    ProfileNotFoundError,
    RateLimitError,
    ScrapingError,
)

from linkedin_mcp_server.exceptions import (
    AuthenticationBootstrapFailedError,
    AuthenticationInProgressError,
    AuthenticationStartedError,
    BrowserBinaryMissingError,
    BrowserBusyError,
    BrowserSetupFailedError,
    BrowserSetupInProgressError,
    CredentialsNotFoundError,
    DockerHostLoginRequiredError,
    LinuxBrowserDependencyError,
    LinkedInMCPError,
    SessionExpiredError,
)
from linkedin_mcp_server.error_diagnostics import (
    build_issue_diagnostics,
    format_tool_error_with_diagnostics,
)

logger = logging.getLogger(__name__)


def _build_detail(exception: Exception, message: str, *, context: str) -> str:
    try:
        diagnostics = build_issue_diagnostics(exception, context=context)
    except Exception:
        logger.debug("Could not build issue diagnostics", exc_info=True)
        diagnostics = None

    if diagnostics is not None:
        return format_tool_error_with_diagnostics(message, diagnostics)
    return message


def raise_api_error(exception: Exception, context: str = "") -> NoReturn:
    """Raise an HTTPException for known LinkedIn exceptions, or re-raise unknown ones.

    Known exceptions are mapped to appropriate HTTP status codes.
    Unknown exceptions are re-raised as 500 Internal Server Error.

    Args:
        exception: The exception that occurred
        context: Optional context about which endpoint failed

    Raises:
        HTTPException: For known LinkedIn exception types
    """
    ctx = f" in {context}" if context else ""

    if isinstance(exception, CredentialsNotFoundError):
        logger.warning("Credentials not found%s: %s", ctx, exception)
        raise HTTPException(
            status_code=401,
            detail=_build_detail(
                exception,
                "Authentication not found. Run with --login to create a browser profile.",
                context=context,
            ),
        ) from exception

    elif isinstance(exception, BrowserSetupInProgressError):
        logger.info("Browser setup in progress%s: %s", ctx, exception)
        raise HTTPException(status_code=503, detail=str(exception)) from exception

    elif isinstance(exception, BrowserSetupFailedError):
        logger.warning("Browser setup failed%s: %s", ctx, exception)
        raise HTTPException(
            status_code=503,
            detail="LinkedIn browser setup was not ready. A fresh setup attempt has started in the background. Retry in a few minutes.",
        ) from exception

    elif isinstance(exception, AuthenticationStartedError):
        logger.info("Authentication started%s: %s", ctx, exception)
        raise HTTPException(status_code=401, detail=str(exception)) from exception

    elif isinstance(exception, AuthenticationInProgressError):
        logger.info("Authentication in progress%s: %s", ctx, exception)
        raise HTTPException(status_code=401, detail=str(exception)) from exception

    elif isinstance(exception, AuthenticationBootstrapFailedError):
        logger.warning("Authentication bootstrap failed%s: %s", ctx, exception)
        raise HTTPException(status_code=401, detail=str(exception)) from exception

    elif isinstance(exception, BrowserBusyError):
        logger.info("Shared browser busy%s: %s", ctx, exception)
        raise HTTPException(status_code=503, detail=str(exception)) from exception

    elif isinstance(exception, DockerHostLoginRequiredError):
        logger.warning("Docker host login required%s: %s", ctx, exception)
        raise HTTPException(status_code=401, detail=str(exception)) from exception

    elif isinstance(exception, LinuxBrowserDependencyError):
        logger.warning("Linux browser dependency missing%s: %s", ctx, exception)
        raise HTTPException(status_code=503, detail=str(exception)) from exception

    elif isinstance(exception, BrowserBinaryMissingError):
        logger.warning("Browser binary missing%s: %s", ctx, exception)
        raise HTTPException(status_code=503, detail=str(exception)) from exception

    elif isinstance(exception, SessionExpiredError):
        logger.warning("Session expired%s: %s", ctx, exception)
        raise HTTPException(
            status_code=401,
            detail=_build_detail(
                exception,
                "Session expired. Run with --login to create a new browser profile.",
                context=context,
            ),
        ) from exception

    elif isinstance(exception, AuthenticationError):
        logger.warning("Authentication failed%s: %s", ctx, exception)
        raise HTTPException(
            status_code=401,
            detail=_build_detail(
                exception,
                "Authentication failed. Run with --login to re-authenticate.",
                context=context,
            ),
        ) from exception

    elif isinstance(exception, RateLimitError):
        wait_time = getattr(exception, "suggested_wait_time", 300)
        logger.warning("Rate limit%s: %s (wait=%ds)", ctx, exception, wait_time)
        raise HTTPException(
            status_code=429,
            detail=f"Rate limit detected. Wait {wait_time} seconds before trying again.",
        ) from exception

    elif isinstance(exception, ProfileNotFoundError):
        logger.warning("Profile not found%s: %s", ctx, exception)
        raise HTTPException(
            status_code=404,
            detail="Profile not found. Check the profile URL is correct.",
        ) from exception

    elif isinstance(exception, ElementNotFoundError):
        logger.warning("Element not found%s: %s", ctx, exception)
        raise HTTPException(
            status_code=500,
            detail=_build_detail(
                exception,
                "Element not found. LinkedIn page structure may have changed.",
                context=context,
            ),
        ) from exception

    elif isinstance(exception, NetworkError):
        logger.warning("Network error%s: %s", ctx, exception)
        raise HTTPException(
            status_code=502,
            detail=_build_detail(
                exception,
                "Network error. Check your connection and try again.",
                context=context,
            ),
        ) from exception

    elif isinstance(exception, ScrapingError):
        logger.warning("Scraping error%s: %s", ctx, exception)
        raise HTTPException(
            status_code=500,
            detail=_build_detail(
                exception,
                "Scraping failed. LinkedIn page structure may have changed.",
                context=context,
            ),
        ) from exception

    elif isinstance(exception, (LinkedInScraperException, LinkedInMCPError)):
        logger.warning("LinkedIn error%s: %s", ctx, exception)
        raise HTTPException(
            status_code=500,
            detail=_build_detail(exception, str(exception), context=context),
        ) from exception

    else:
        logger.error("Unexpected error%s: %s", ctx, exception, exc_info=True)
        raise HTTPException(
            status_code=500, detail="Internal server error"
        ) from exception


# Backward compatibility alias
raise_tool_error = raise_api_error
