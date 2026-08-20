"""Pydantic params models + SDL entity contracts for Webflow Connector's
Forms domain -- native Webflow forms and their submissions. Confirmed
against developers.webflow.com/data/reference/forms/* during Discovery
2026-08-20.
"""
from __future__ import annotations

from pydantic import BaseModel, Field
from imperal_sdk import sdl

from schemas import DeleteResult  # noqa: F401 -- re-exported for handlers_forms.py


class ListFormsParams(BaseModel):
    connection_id: str = Field("", description="Connection id from list_connections. Omit if only one is connected.")
    site_id: str = Field(..., description="Site id from list_sites.")


class WebflowForm(sdl.Entity):
    id: str
    display_name: str = ""
    site_id: str = ""
    page_id: str = ""
    created_on: str = ""
    last_updated: str = ""
    fields: dict = {}


class WebflowFormList(sdl.Entity):
    title: str = "Forms"
    items: list[WebflowForm] = []


class GetFormParams(BaseModel):
    connection_id: str = Field("", description="Connection id from list_connections. Omit if only one is connected.")
    form_id: str = Field(..., description="Form id from list_forms.")


class ListFormSubmissionsParams(BaseModel):
    connection_id: str = Field("", description="Connection id from list_connections. Omit if only one is connected.")
    form_id: str = Field(..., description="Form id from list_forms.")
    limit: int = Field(50, ge=1, le=100, description="Max submissions to return (1-100).")
    offset: int = Field(0, ge=0, description="Pagination offset.")


class WebflowFormSubmission(sdl.Entity):
    id: str
    form_id: str = ""
    site_id: str = ""
    submitted_on: str = ""
    form_response: dict = {}


class WebflowFormSubmissionList(sdl.Entity):
    title: str = "Form submissions"
    items: list[WebflowFormSubmission] = []


class GetFormSubmissionParams(BaseModel):
    connection_id: str = Field("", description="Connection id from list_connections. Omit if only one is connected.")
    submission_id: str = Field(..., description="Submission id from list_form_submissions.")


class DeleteFormSubmissionParams(BaseModel):
    connection_id: str = Field("", description="Connection id from list_connections. Omit if only one is connected.")
    submission_id: str = Field(..., description="Submission id from list_form_submissions.")
