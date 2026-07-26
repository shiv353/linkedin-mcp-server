"""Job REST API routes."""

import logging
from typing import Any

from fastapi import APIRouter, Query, Path

from linkedin_mcp_server.core.exceptions import AuthenticationError
from linkedin_mcp_server.dependencies import get_ready_extractor, handle_auth_error
from linkedin_mcp_server.error_handler import raise_api_error

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["job"])


@router.get("/jobs/saved")
async def get_saved_jobs(
    max_pages: int = Query(3, ge=1, le=10, description="Max pages to load"),
) -> dict[str, Any]:
    """List job postings saved by the authenticated user."""
    try:
        extractor = await get_ready_extractor(endpoint_name="get_saved_jobs")
        return await extractor.get_saved_jobs(max_pages=max_pages)
    except AuthenticationError as e:
        await handle_auth_error(e)
    except Exception as e:
        raise_api_error(e, "get_saved_jobs")


@router.get("/jobs/{job_id}")
async def get_job_details(
    job_id: str = Path(..., description="LinkedIn job ID"),
) -> dict[str, Any]:
    """Get detailed information about a specific job posting."""
    try:
        extractor = await get_ready_extractor(endpoint_name="get_job_details")
        return await extractor.scrape_job(job_id)
    except AuthenticationError as e:
        await handle_auth_error(e)
    except Exception as e:
        raise_api_error(e, "get_job_details")


@router.get("/search/jobs")
async def search_jobs(
    keywords: str = Query(..., description="Search keywords"),
    location: str | None = Query(None, description="Location filter"),
    max_pages: int = Query(3, ge=1, le=10, description="Max result pages"),
    date_posted: str | None = Query(
        None, description="past_hour, past_24_hours, past_week, past_month"
    ),
    job_type: str | None = Query(
        None, description="Comma-separated: full_time, part_time, contract, etc."
    ),
    experience_level: str | None = Query(
        None, description="Comma-separated: internship, entry, associate, etc."
    ),
    work_type: str | None = Query(
        None, description="Comma-separated: on_site, remote, hybrid"
    ),
    easy_apply: bool = Query(False, description="Only show Easy Apply jobs"),
    sort_by: str | None = Query(None, description="date or relevance"),
) -> dict[str, Any]:
    """Search for jobs on LinkedIn."""
    try:
        extractor = await get_ready_extractor(endpoint_name="search_jobs")
        return await extractor.search_jobs(
            keywords,
            location=location,
            max_pages=max_pages,
            date_posted=date_posted,
            job_type=job_type,
            experience_level=experience_level,
            work_type=work_type,
            easy_apply=easy_apply,
            sort_by=sort_by,
        )
    except AuthenticationError as e:
        await handle_auth_error(e)
    except Exception as e:
        raise_api_error(e, "search_jobs")
