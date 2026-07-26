"""Person profile REST API routes."""

import logging
from typing import Any

from fastapi import APIRouter, HTTPException, Query, Path

from linkedin_mcp_server.api.callbacks import LoggingProgressCallback
from linkedin_mcp_server.core.exceptions import AuthenticationError
from linkedin_mcp_server.dependencies import get_ready_extractor, handle_auth_error
from linkedin_mcp_server.error_handler import raise_api_error
from linkedin_mcp_server.scraping import parse_person_sections
from linkedin_mcp_server.scraping.extractor import FilterValidationError
from linkedin_mcp_server.api.schemas import ConnectRequest

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["person"])


@router.get("/profiles/me")
async def get_my_profile(
    sections: str | None = Query(
        None,
        description="Comma-separated sections: experience, education, interests, honors, languages, certifications, skills, projects, contact_info, posts",
    ),
    max_scrolls: int | None = Query(
        None, ge=1, le=50, description="Max pagination attempts per section"
    ),
) -> dict[str, Any]:
    """Get the authenticated user's own LinkedIn profile."""
    try:
        extractor = await get_ready_extractor(endpoint_name="get_my_profile")
        requested, unknown = parse_person_sections(sections)
        cb = LoggingProgressCallback()
        result = await extractor.get_my_profile(
            sections=requested, callbacks=cb, max_scrolls=max_scrolls
        )
        if unknown:
            result["unknown_sections"] = unknown
        return result
    except AuthenticationError as e:
        await handle_auth_error(e)
    except Exception as e:
        raise_api_error(e, "get_my_profile")


@router.get("/profiles/{username}")
async def get_person_profile(
    username: str = Path(..., description="LinkedIn username"),
    sections: str | None = Query(
        None,
        description="Comma-separated sections: experience, education, interests, honors, languages, certifications, skills, projects, contact_info, posts",
    ),
    max_scrolls: int | None = Query(
        None, ge=1, le=50, description="Max pagination attempts per section"
    ),
) -> dict[str, Any]:
    """Get a specific person's LinkedIn profile."""
    try:
        extractor = await get_ready_extractor(endpoint_name="get_person_profile")
        requested, unknown = parse_person_sections(sections)
        cb = LoggingProgressCallback()
        result = await extractor.scrape_person(
            username, requested, callbacks=cb, max_scrolls=max_scrolls
        )
        if unknown:
            result["unknown_sections"] = unknown
        return result
    except AuthenticationError as e:
        await handle_auth_error(e)
    except Exception as e:
        raise_api_error(e, "get_person_profile")


@router.get("/profiles/{username}/sidebar")
async def get_sidebar_profiles(
    username: str = Path(..., description="LinkedIn username"),
) -> dict[str, Any]:
    """Get profile links from sidebar recommendation sections."""
    try:
        extractor = await get_ready_extractor(endpoint_name="get_sidebar_profiles")
        return await extractor.get_sidebar_profiles(username)
    except AuthenticationError as e:
        await handle_auth_error(e)
    except Exception as e:
        raise_api_error(e, "get_sidebar_profiles")


@router.post("/profiles/{username}/connect")
async def connect_with_person(
    username: str = Path(..., description="LinkedIn username"),
    body: ConnectRequest = ConnectRequest(),
) -> dict[str, Any]:
    """Send a LinkedIn connection request or accept an incoming one."""
    try:
        extractor = await get_ready_extractor(endpoint_name="connect_with_person")
        return await extractor.connect_with_person(username, note=body.note)
    except AuthenticationError as e:
        await handle_auth_error(e)
    except Exception as e:
        raise_api_error(e, "connect_with_person")


@router.get("/search/people")
async def search_people(
    keywords: str = Query(..., description="Search keywords"),
    location: str | None = Query(None, description="Location filter"),
    network: list[str] | None = Query(
        None, description="Connection degree: F (1st), S (2nd), O (3rd+)"
    ),
    current_company: str | None = Query(None, description="Company URN id filter"),
) -> dict[str, Any]:
    """Search for people on LinkedIn."""
    try:
        extractor = await get_ready_extractor(endpoint_name="search_people")
        try:
            return await extractor.search_people(
                keywords, location, network=network, current_company=current_company
            )
        except FilterValidationError as e:
            raise HTTPException(status_code=400, detail=str(e)) from e
    except HTTPException:
        raise
    except AuthenticationError as e:
        await handle_auth_error(e)
    except Exception as e:
        raise_api_error(e, "search_people")
