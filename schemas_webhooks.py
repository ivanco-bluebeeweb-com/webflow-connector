"""Pydantic params models + SDL entity contracts for Webflow Connector's
Webhooks domain -- push notifications for site/CMS/form/ecommerce events,
plus Comments (Webflow Editor comment threads on pages). Confirmed against
developers.webflow.com/data/reference/webhooks/*,
/data/docs/working-with-webhooks, /data/reference/all-events, and
/data/reference/comments/* during Discovery 2026-08-20.

WHY A FIXED TRIGGER-TYPE ENUM. Webflow validates `triggerType` server-side
against its own fixed event list at webhook-creation time -- passing an
unsupported value is rejected by Webflow itself, not a local convenience
restriction.
"""
from __future__ import annotations

from pydantic import BaseModel, Field
from imperal_sdk import sdl

from schemas import DeleteResult  # noqa: F401 -- re-exported for handlers_webhooks.py


# ──────────────────────────────────────────────────────────────────────────
# Webhooks
# ──────────────────────────────────────────────────────────────────────────

# Confirmed exhaustive list, developers.webflow.com/data/reference/all-events (2026-08-20).
WEBFLOW_TRIGGER_TYPES = [
    "form_submission", "site_publish",
    "page_created", "page_metadata_updated", "page_deleted",
    "ecomm_new_order", "ecomm_order_changed", "ecomm_inventory_changed",
    "user_account_added", "user_account_updated", "user_account_deleted",
    "collection_item_created", "collection_item_changed", "collection_item_deleted",
    "collection_item_unpublished",
]


class ListWebhooksParams(BaseModel):
    connection_id: str = Field("", description="Connection id from list_connections. Omit if only one is connected.")
    site_id: str = Field(..., description="Site id from list_sites.")


class WebflowWebhook(sdl.Entity):
    id: str
    trigger_type: str = ""
    site_id: str = ""
    workspace_id: str = ""
    url: str = ""
    filter: dict = {}
    created_on: str = ""


class WebflowWebhookList(sdl.Entity):
    title: str = "Webhooks"
    items: list[WebflowWebhook] = []


class GetWebhookParams(BaseModel):
    connection_id: str = Field("", description="Connection id from list_connections. Omit if only one is connected.")
    webhook_id: str = Field(..., description="Webhook id from list_webhooks.")


class CreateWebhookParams(BaseModel):
    connection_id: str = Field("", description="Connection id from list_connections. Omit if only one is connected.")
    site_id: str = Field(..., description="Site id from list_sites.")
    trigger_type: str = Field(..., description=f"Event to subscribe to. One of: {', '.join(WEBFLOW_TRIGGER_TYPES)}.")
    url: str = Field(..., description="Publicly reachable https:// URL Webflow will POST the event payload to.")
    filter: dict = Field(default_factory=dict, description="Optional trigger-specific filter (e.g. {'name': 'My Form'} to scope form_submission to one form).")


class DeleteWebhookParams(BaseModel):
    connection_id: str = Field("", description="Connection id from list_connections. Omit if only one is connected.")
    webhook_id: str = Field(..., description="Webhook id from list_webhooks.")


# ──────────────────────────────────────────────────────────────────────────
# Comments (Webflow Editor comment threads)
# ──────────────────────────────────────────────────────────────────────────


class ListCommentThreadsParams(BaseModel):
    connection_id: str = Field("", description="Connection id from list_connections. Omit if only one is connected.")
    site_id: str = Field(..., description="Site id from list_sites.")
    limit: int = Field(50, ge=1, le=100, description="Max threads to return (1-100).")
    offset: int = Field(0, ge=0, description="Pagination offset.")


class WebflowComment(sdl.Entity):
    id: str
    author_name: str = ""
    author_email: str = ""
    body: str = ""
    posted_on: str = ""
    resolved: bool = False


class WebflowCommentThread(sdl.Entity):
    id: str
    site_id: str = ""
    page_id: str = ""
    resolved: bool = False
    comments: list[WebflowComment] = []


class WebflowCommentThreadList(sdl.Entity):
    title: str = "Comment threads"
    items: list[WebflowCommentThread] = []
