"""Feed and post search REST API routes."""

import logging
from typing import Any

from fastapi import APIRouter, HTTPException, Query

from linkedin_mcp_server.core.exceptions import AuthenticationError
from linkedin_mcp_server.dependencies import get_ready_extractor, handle_auth_error
from linkedin_mcp_server.error_handler import raise_api_error
from linkedin_mcp_server.scraping.extractor import (
    FilterValidationError,
    _RATE_LIMITED_MSG,
)
from linkedin_mcp_server.scraping.link_metadata import Reference

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["feed"])


@router.get("/feed")
async def get_feed(
    num_posts: int = Query(10, ge=1, le=50, description="Number of posts to fetch"),
) -> dict[str, Any]:
    """Get posts from the authenticated user's LinkedIn feed."""
    try:
        extractor = await get_ready_extractor(endpoint_name="get_feed")
        extracted = await extractor.extract_feed(num_posts=num_posts)

        url = "https://www.linkedin.com/feed/"
        sections: dict[str, str] = {}
        references: dict[str, list[Reference]] = {}
        section_errors: dict[str, dict[str, Any]] = {}
        if extracted.text and extracted.text != _RATE_LIMITED_MSG:
            sections["feed"] = extracted.text
            if extracted.references:
                references["feed"] = extracted.references
        elif extracted.text == _RATE_LIMITED_MSG:
            section_errors["feed"] = {
                "error_type": "rate_limit",
                "error_message": extracted.text,
            }
        elif extracted.error:
            section_errors["feed"] = extracted.error

        result: dict[str, Any] = {"url": url, "sections": sections}
        if references:
            result["references"] = references
        if section_errors:
            result["section_errors"] = section_errors
        return result
    except AuthenticationError as e:
        await handle_auth_error(e)
    except Exception as e:
        raise_api_error(e, "get_feed")


@router.get("/search/posts")
async def search_posts(
    keywords: str = Query(..., description="Search keywords"),
    date_posted: str | None = Query(
        None, description="past-24h, past-week, past-month"
    ),
    max_pages: int = Query(3, ge=1, le=10, description="Scroll depth"),
) -> dict[str, Any]:
    """Search LinkedIn posts/content globally by keyword."""
    try:
        extractor = await get_ready_extractor(endpoint_name="search_posts")
        try:
            return await extractor.search_posts(
                keywords, date_posted=date_posted, max_pages=max_pages
            )
        except FilterValidationError as e:
            raise HTTPException(status_code=400, detail=str(e)) from e
    except HTTPException:
        raise
    except AuthenticationError as e:
        await handle_auth_error(e)
    except Exception as e:
        raise_api_error(e, "search_posts")
