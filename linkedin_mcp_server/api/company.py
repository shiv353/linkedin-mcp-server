"""Company REST API routes."""

import logging
from typing import Any

from fastapi import APIRouter, Query, Path

from linkedin_mcp_server.api.callbacks import LoggingProgressCallback
from linkedin_mcp_server.core.exceptions import AuthenticationError
from linkedin_mcp_server.dependencies import get_ready_extractor, handle_auth_error
from linkedin_mcp_server.error_handler import raise_api_error
from linkedin_mcp_server.scraping import parse_company_sections
from linkedin_mcp_server.scraping.extractor import _RATE_LIMITED_MSG
from linkedin_mcp_server.scraping.link_metadata import Reference

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["company"])


@router.get("/companies/{company_name}")
async def get_company_profile(
    company_name: str = Path(..., description="LinkedIn company slug"),
    sections: str | None = Query(
        None, description="Comma-separated sections: posts, jobs"
    ),
) -> dict[str, Any]:
    """Get a company's LinkedIn profile."""
    try:
        extractor = await get_ready_extractor(endpoint_name="get_company_profile")
        requested, unknown = parse_company_sections(sections)
        cb = LoggingProgressCallback()
        result = await extractor.scrape_company(company_name, requested, callbacks=cb)
        if unknown:
            result["unknown_sections"] = unknown
        return result
    except AuthenticationError as e:
        await handle_auth_error(e)
    except Exception as e:
        raise_api_error(e, "get_company_profile")


@router.get("/companies/{company_name}/posts")
async def get_company_posts(
    company_name: str = Path(..., description="LinkedIn company slug"),
) -> dict[str, Any]:
    """Get recent posts from a company's LinkedIn feed."""
    try:
        extractor = await get_ready_extractor(endpoint_name="get_company_posts")
        url = f"https://www.linkedin.com/company/{company_name}/posts/"
        extracted = await extractor.extract_page(url, section_name="posts")

        sections: dict[str, str] = {}
        references: dict[str, list[Reference]] = {}
        section_errors: dict[str, dict[str, Any]] = {}
        if extracted.text and extracted.text != _RATE_LIMITED_MSG:
            sections["posts"] = extracted.text
            if extracted.references:
                references["posts"] = extracted.references
        elif extracted.error:
            section_errors["posts"] = extracted.error

        result: dict[str, Any] = {"url": url, "sections": sections}
        if references:
            result["references"] = references
        if section_errors:
            result["section_errors"] = section_errors
        return result
    except AuthenticationError as e:
        await handle_auth_error(e)
    except Exception as e:
        raise_api_error(e, "get_company_posts")


@router.get("/companies/{company_name}/employees")
async def get_company_employees(
    company_name: str = Path(..., description="LinkedIn company slug"),
    keywords: str | None = Query(None, description="Filter by name, title, or skill"),
) -> dict[str, Any]:
    """List employees at a company."""
    try:
        extractor = await get_ready_extractor(endpoint_name="get_company_employees")
        return await extractor.get_company_employees(company_name, keywords=keywords)
    except AuthenticationError as e:
        await handle_auth_error(e)
    except Exception as e:
        raise_api_error(e, "get_company_employees")


@router.get("/search/companies")
async def search_companies(
    keywords: str = Query(..., description="Search keywords"),
) -> dict[str, Any]:
    """Search for companies on LinkedIn."""
    try:
        extractor = await get_ready_extractor(endpoint_name="search_companies")
        return await extractor.search_companies(keywords)
    except AuthenticationError as e:
        await handle_auth_error(e)
    except Exception as e:
        raise_api_error(e, "search_companies")
