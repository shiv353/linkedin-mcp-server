"""Session management REST API routes."""

import logging
from typing import Any

from fastapi import APIRouter

from linkedin_mcp_server import __version__
from linkedin_mcp_server.drivers.browser import close_browser
from linkedin_mcp_server.error_handler import raise_api_error

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["session"])


@router.delete("/session")
async def close_session() -> dict[str, Any]:
    """Close the current browser session and clean up resources."""
    try:
        await close_browser()
        return {
            "status": "success",
            "message": "Successfully closed the browser session and cleaned up resources",
        }
    except Exception as e:
        raise_api_error(e, "close_session")


@router.get("/session/status")
async def session_status() -> dict[str, Any]:
    """Check server and session health."""
    from linkedin_mcp_server.session_state import profile_exists
    from linkedin_mcp_server.update_check import pending_update_notice

    has_profile = profile_exists()
    notice = pending_update_notice()

    result: dict[str, Any] = {
        "status": "ok",
        "authenticated": has_profile,
        "version": __version__,
    }
    if not has_profile:
        result["message"] = "No active session. Run with --login to authenticate."
    if notice:
        result["update_notice"] = notice
    return result


@router.post("/login")
async def trigger_login() -> dict[str, Any]:
    """Trigger the interactive login flow on the server."""
    from linkedin_mcp_server.setup import interactive_login

    try:
        success = await interactive_login()
        if success:
            return {
                "status": "success",
                "message": "Successfully logged in and saved profile.",
            }

        # If interactive_login returned False without raising, it was likely cancelled.
        from fastapi import HTTPException

        raise HTTPException(status_code=401, detail="Login failed or was cancelled.")
    except Exception as e:
        raise_api_error(e, "trigger_login")
