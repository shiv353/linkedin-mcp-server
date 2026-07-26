"""Pydantic models for API request/response schemas."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


# --- Response Models ---


class LinkedInResponse(BaseModel):
    """Base response for all LinkedIn scraping endpoints."""

    url: str
    sections: dict[str, str] = Field(default_factory=dict)
    references: dict[str, list[dict[str, Any]]] | None = None
    unknown_sections: list[str] | None = None
    section_errors: dict[str, dict[str, Any]] | None = None


class JobSearchResponse(LinkedInResponse):
    """Response for job search endpoints that include job IDs."""

    job_ids: list[str] = Field(default_factory=list)


class SidebarProfilesResponse(BaseModel):
    """Response for sidebar profile extraction."""

    url: str
    sidebar_profiles: dict[str, list[str]] = Field(default_factory=dict)


class ConnectResponse(BaseModel):
    """Response for connection request."""

    url: str
    status: str
    message: str
    note_sent: bool = False


class MessageResponse(BaseModel):
    """Response for send message."""

    url: str
    status: str
    message: str
    recipient_selected: bool = False
    sent: bool = False


class SessionResponse(BaseModel):
    """Response for session operations."""

    status: str
    message: str


class SessionStatusResponse(BaseModel):
    """Response for session health check."""

    status: str
    authenticated: bool
    version: str
    message: str = ""


# --- Request Models ---


class ConnectRequest(BaseModel):
    """Request body for connection request."""

    note: str | None = None


class MessageRequest(BaseModel):
    """Request body for sending a message."""

    linkedin_username: str
    message: str
    confirm_send: bool = False
    profile_urn: str | None = None


class ErrorResponse(BaseModel):
    """Standard error response."""

    detail: str
    error_type: str | None = None
