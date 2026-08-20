"""Pydantic params models + SDL entity contracts for Webflow Connector's
CMS domain -- Collections, Collection Fields, and Collection Items
(staged/draft vs live, matching Webflow's own CMS model where an Item can
be created/updated as a draft and only appears on the live site once
explicitly published). Confirmed against developers.webflow.com/data/
reference/cms/* during Discovery 2026-08-20.
"""
from __future__ import annotations

from pydantic import BaseModel, Field
from imperal_sdk import sdl

from schemas import DeleteResult  # noqa: F401 -- re-exported for handlers_cms.py


# ──────────────────────────────────────────────────────────────────────────
# Collections
# ──────────────────────────────────────────────────────────────────────────


class ListCollectionsParams(BaseModel):
    connection_id: str = Field("", description="Connection id from list_connections. Omit if only one is connected.")
    site_id: str = Field(..., description="Site id from list_sites.")


class WebflowCollection(sdl.Entity):
    id: str
    display_name: str = ""
    singular_name: str = ""
    slug: str = ""
    created_on: str = ""
    last_updated: str = ""


class WebflowCollectionList(sdl.Entity):
    title: str = "Collections"
    items: list[WebflowCollection] = []


class GetCollectionParams(BaseModel):
    connection_id: str = Field("", description="Connection id from list_connections. Omit if only one is connected.")
    collection_id: str = Field(..., description="Collection id from list_collections.")


class WebflowCollectionField(sdl.Entity):
    id: str
    display_name: str = ""
    slug: str = ""
    type: str = ""
    is_required: bool = False
    is_editable: bool = True
    help_text: str = ""


class WebflowCollectionDetail(sdl.Entity):
    id: str
    display_name: str = ""
    singular_name: str = ""
    slug: str = ""
    created_on: str = ""
    last_updated: str = ""
    fields: list[WebflowCollectionField] = []


class CreateCollectionParams(BaseModel):
    connection_id: str = Field("", description="Connection id from list_connections. Omit if only one is connected.")
    site_id: str = Field(..., description="Site id from list_sites.")
    display_name: str = Field(..., description="Name shown in the Webflow Designer, e.g. 'Blog Posts'.")
    singular_name: str = Field(..., description="Name of one Item, e.g. 'Blog Post'.")
    slug: str = Field("", description="URL slug for the Collection. Auto-generated from display_name if omitted.")


class DeleteCollectionParams(BaseModel):
    connection_id: str = Field("", description="Connection id from list_connections. Omit if only one is connected.")
    collection_id: str = Field(..., description="Collection id from list_collections.")


# ──────────────────────────────────────────────────────────────────────────
# Collection Fields
# ──────────────────────────────────────────────────────────────────────────


class CreateCollectionFieldParams(BaseModel):
    connection_id: str = Field("", description="Connection id from list_connections. Omit if only one is connected.")
    collection_id: str = Field(..., description="Collection id from list_collections.")
    display_name: str = Field(..., description="Field name shown in the Designer, e.g. 'Author'.")
    field_type: str = Field(..., description="Webflow field type: PlainText, RichText, Image, MultiImage, Video, Link, Email, Phone, Number, DateTime, Switch, Color, Option, Reference, MultiReference, File.")
    is_required: bool = Field(False, description="Whether this field must be filled on every Item.")
    help_text: str = Field("", description="Helper text shown to editors in the Webflow Editor.")


class UpdateCollectionFieldParams(BaseModel):
    connection_id: str = Field("", description="Connection id from list_connections. Omit if only one is connected.")
    collection_id: str = Field(..., description="Collection id from list_collections.")
    field_id: str = Field(..., description="Field id from get_collection.")
    display_name: str = Field("", description="New display name. Omit to leave unchanged.")
    help_text: str = Field("", description="New helper text. Omit to leave unchanged.")
    is_required: bool | None = Field(None, description="Change required status. Omit to leave unchanged.")


class DeleteCollectionFieldParams(BaseModel):
    connection_id: str = Field("", description="Connection id from list_connections. Omit if only one is connected.")
    collection_id: str = Field(..., description="Collection id from list_collections.")
    field_id: str = Field(..., description="Field id from get_collection.")


# ──────────────────────────────────────────────────────────────────────────
# Collection Items (staged/draft + live)
# ──────────────────────────────────────────────────────────────────────────


class ListCollectionItemsParams(BaseModel):
    connection_id: str = Field("", description="Connection id from list_connections. Omit if only one is connected.")
    collection_id: str = Field(..., description="Collection id from list_collections.")
    limit: int = Field(100, ge=1, le=100, description="Max items to return (1-100).")
    offset: int = Field(0, ge=0, description="Pagination offset.")


class WebflowCollectionItem(sdl.Entity):
    id: str
    cms_locale_id: str = ""
    last_published: str = ""
    last_updated: str = ""
    created_on: str = ""
    is_archived: bool = False
    is_draft: bool = False
    field_data: dict = {}


class WebflowCollectionItemList(sdl.Entity):
    title: str = "Collection items"
    items: list[WebflowCollectionItem] = []
    total: int = 0


class GetCollectionItemParams(BaseModel):
    connection_id: str = Field("", description="Connection id from list_connections. Omit if only one is connected.")
    collection_id: str = Field(..., description="Collection id from list_collections.")
    item_id: str = Field(..., description="Item id from list_collection_items.")


class CreateCollectionItemParams(BaseModel):
    connection_id: str = Field("", description="Connection id from list_connections. Omit if only one is connected.")
    collection_id: str = Field(..., description="Collection id from list_collections.")
    field_data: dict = Field(..., description="Field slug -> value map matching the Collection's own field schema, e.g. {'name': 'My Post', 'slug': 'my-post', 'body-content': '<p>...</p>'}.")
    is_archived: bool = Field(False, description="Create as archived (hidden from the live site and CMS list by default).")
    is_draft: bool = Field(True, description="Create as a draft. Draft items are NOT visible on the live site until publish_collection_items is called.")


class UpdateCollectionItemParams(BaseModel):
    connection_id: str = Field("", description="Connection id from list_connections. Omit if only one is connected.")
    collection_id: str = Field(..., description="Collection id from list_collections.")
    item_id: str = Field(..., description="Item id from list_collection_items.")
    field_data: dict = Field(..., description="Field slug -> value map for the fields being changed. Omitted fields keep their current value.")
    is_archived: bool | None = Field(None, description="Change archived status. Omit to leave unchanged.")
    is_draft: bool | None = Field(None, description="Change draft status. Omit to leave unchanged.")


class DeleteCollectionItemParams(BaseModel):
    connection_id: str = Field("", description="Connection id from list_connections. Omit if only one is connected.")
    collection_id: str = Field(..., description="Collection id from list_collections.")
    item_id: str = Field(..., description="Item id from list_collection_items.")


class PublishCollectionItemsParams(BaseModel):
    connection_id: str = Field("", description="Connection id from list_connections. Omit if only one is connected.")
    collection_id: str = Field(..., description="Collection id from list_collections.")
    item_ids: list[str] = Field(..., description="Item ids to push live (staged -> published), 1-100 per call.")


class PublishItemsResult(sdl.Entity):
    collection_id: str
    published_item_ids: list[str] = []
    errors: list[str] = []


class BulkCreateCollectionItemsParams(BaseModel):
    connection_id: str = Field("", description="Connection id from list_connections. Omit if only one is connected.")
    collection_id: str = Field(..., description="Collection id from list_collections.")
    items: list[dict] = Field(..., description="List of field_data maps, one per Item to create (1-100 per call, Webflow's own bulk create limit).")
    is_draft: bool = Field(True, description="Create all as drafts. Draft items are NOT visible live until publish_collection_items is called.")
