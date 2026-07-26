"""Messaging REST API routes."""

import logging
from typing import Any

from fastapi import APIRouter, HTTPException, Query

from linkedin_mcp_server.api.schemas import MessageRequest
from linkedin_mcp_server.core.exceptions import AuthenticationError
from linkedin_mcp_server.dependencies import get_ready_extractor, handle_auth_error
from linkedin_mcp_server.error_handler import raise_api_error

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["messaging"])


@router.get("/inbox")
async def get_inbox(
    limit: int = Query(20, ge=1, le=50, description="Max conversations to load"),
) -> dict[str, Any]:
    """List recent conversations from the LinkedIn messaging inbox."""
    try:
        extractor = await get_ready_extractor(endpoint_name="get_inbox")
        return await extractor.get_inbox(limit=limit)
    except AuthenticationError as e:
        await handle_auth_error(e)
    except Exception as e:
        raise_api_error(e, "get_inbox")


@router.get("/conversations")
async def get_conversation(
    linkedin_username: str | None = Query(
        None, description="LinkedIn username of participant"
    ),
    thread_id: str | None = Query(None, description="LinkedIn thread ID"),
    index: int = Query(0, ge=0, description="0-based thread selector"),
) -> dict[str, Any]:
    """Read a specific messaging conversation."""
    if not linkedin_username and not thread_id:
        raise HTTPException(
            status_code=400,
            detail="Provide at least one of linkedin_username or thread_id",
        )
    try:
        extractor = await get_ready_extractor(endpoint_name="get_conversation")
        return await extractor.get_conversation(
            linkedin_username=linkedin_username, thread_id=thread_id, index=index
        )
    except AuthenticationError as e:
        await handle_auth_error(e)
    except Exception as e:
        raise_api_error(e, "get_conversation")


@router.get("/search/conversations")
async def search_conversations(
    keywords: str = Query(..., description="Search keywords"),
    limit: int = Query(20, ge=1, le=50, description="Max results"),
) -> dict[str, Any]:
    """Search messages by keyword."""
    try:
        extractor = await get_ready_extractor(endpoint_name="search_conversations")
        return await extractor.search_conversations(keywords, limit=limit)
    except AuthenticationError as e:
        await handle_auth_error(e)
    except Exception as e:
        raise_api_error(e, "search_conversations")


@router.post("/messages")
async def send_message(body: MessageRequest) -> dict[str, Any]:
    """Send a message to a LinkedIn user."""
    try:
        extractor = await get_ready_extractor(endpoint_name="send_message")
        return await extractor.send_message(
            body.linkedin_username,
            body.message,
            confirm_send=body.confirm_send,
            profile_urn=body.profile_urn,
        )
    except AuthenticationError as e:
        await handle_auth_error(e)
    except Exception as e:
        raise_api_error(e, "send_message")
