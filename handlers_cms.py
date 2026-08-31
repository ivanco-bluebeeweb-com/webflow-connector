"""Chat functions for Webflow Connector -- CMS domain (Collections,
Collection Fields, Collection Items)."""
from __future__ import annotations

from imperal_sdk import ActionResult

import webflow_cms_client as wcc
from app import chat
from handlers import _resolve_connection
from schemas_cms import (
    ListCollectionsParams, WebflowCollection, WebflowCollectionList,
    GetCollectionParams, WebflowCollectionDetail, WebflowCollectionField,
    CreateCollectionParams, DeleteCollectionParams, DeleteResult,
    ListCollectionItemsParams, WebflowCollectionItem, WebflowCollectionItemList,
    GetCollectionItemParams, CreateCollectionItemParams,
    UpdateCollectionItemParams, DeleteCollectionItemParams,
    PublishCollectionItemsParams, PublishItemsResult,
)


def _to_collection(c: dict) -> WebflowCollection:
    return WebflowCollection(
        id=c.get("id", ""), display_name=c.get("displayName", ""),
        singular_name=c.get("singularName", ""), slug=c.get("slug", ""),
        created_on=c.get("createdOn", ""), last_updated=c.get("lastUpdated", ""),
    )


def _to_item(it: dict) -> WebflowCollectionItem:
    return WebflowCollectionItem(
        id=it.get("id", ""), collection_id=it.get("cmsLocaleId", "") or it.get("collectionId", ""),
        is_draft=bool(it.get("isDraft", False)), is_archived=bool(it.get("isArchived", False)),
        last_published=it.get("lastPublished", "") or "", last_updated=it.get("lastUpdated", ""),
        created_on=it.get("createdOn", ""), field_data=it.get("fieldData", {}) or {},
    )


@chat.function(
    "list_collections",
    "List all CMS Collections on a Webflow site (e.g. Blog Posts, Products, Categories).",
    action_type="read", chain_callable=True, data_model=WebflowCollectionList,
    event="webflow-connector.list_collections",
)
async def list_collections(ctx, params: ListCollectionsParams) -> ActionResult:
    conn = await _resolve_connection(ctx, params.connection_id)
    if not conn:
        return ActionResult.error("No Webflow site connected. Use connect_webflow first.", code="WEBFLOW_NOT_CONNECTED")
    raw = await wcc.list_collections(ctx, conn["token"], params.site_id)
    return ActionResult.success(WebflowCollectionList(items=[_to_collection(c) for c in raw])), summary="Collections listed."


@chat.function(
    "get_collection",
    "Read one CMS Collection's schema in full -- its fields, types, and which are required/editable. Call before creating or updating an Item so you know the exact field slugs to use.",
    action_type="read", chain_callable=True, data_model=WebflowCollectionDetail,
    event="webflow-connector.get_collection",
)
async def get_collection(ctx, params: GetCollectionParams) -> ActionResult:
    conn = await _resolve_connection(ctx, params.connection_id)
    if not conn:
        return ActionResult.error("No Webflow site connected. Use connect_webflow first.", code="WEBFLOW_NOT_CONNECTED")
    c = await wcc.get_collection(ctx, conn["token"], params.collection_id)
    fields = [
        WebflowCollectionField(
            id=f.get("id", ""), display_name=f.get("displayName", ""), slug=f.get("slug", ""),
            type=f.get("type", ""), is_required=bool(f.get("isRequired", False)),
            is_editable=bool(f.get("isEditable", True)), help_text=f.get("helpText", "") or "",
        )
        for f in c.get("fields", [])
    ]
    return ActionResult.success(WebflowCollectionDetail(
        id=c.get("id", ""), display_name=c.get("displayName", ""), singular_name=c.get("singularName", ""),
        slug=c.get("slug", ""), created_on=c.get("createdOn", ""), last_updated=c.get("lastUpdated", ""),
        fields=fields,
    )), summary="Collection retrieved."


@chat.function(
    "create_collection",
    "Create a new CMS Collection on a Webflow site -- a new content type like 'Blog Posts' or 'Team Members'. Use get_collection afterwards to see the default fields Webflow adds, before adding your own via the Designer (field creation beyond the Name/Slug defaults is Designer-only).",
    action_type="write", chain_callable=True, data_model=WebflowCollection,
    event="webflow-connector.create_collection",
    effects=["webflow.collection.created"],
)
async def create_collection(ctx, params: CreateCollectionParams) -> ActionResult:
    conn = await _resolve_connection(ctx, params.connection_id)
    if not conn:
        return ActionResult.error("No Webflow site connected. Use connect_webflow first.", code="WEBFLOW_NOT_CONNECTED")
    c = await wcc.create_collection(ctx, conn["token"], params.site_id, params.display_name, params.singular_name, params.slug)
    return ActionResult.success(_to_collection(c), message=f"Collection '{params.display_name}' created."), summary="Collection created."


@chat.function(
    "delete_collection",
    "Permanently delete a CMS Collection and every Item inside it. Cannot be undone.",
    action_type="write", chain_callable=True, data_model=DeleteResult,
    event="webflow-connector.delete_collection",
    effects=["webflow.collection.deleted"],
)
async def delete_collection(ctx, params: DeleteCollectionParams) -> ActionResult:
    conn = await _resolve_connection(ctx, params.connection_id)
    if not conn:
        return ActionResult.error("No Webflow site connected. Use connect_webflow first.", code="WEBFLOW_NOT_CONNECTED")
    await wcc.delete_collection(ctx, conn["token"], params.collection_id)
    return ActionResult.success(DeleteResult(id=params.collection_id), message="Collection deleted."), summary="Collection deleted."


@chat.function(
    "list_collection_items",
    "List Items inside a CMS Collection -- e.g. all blog posts or all products, with their field data.",
    action_type="read", chain_callable=True, data_model=WebflowCollectionItemList,
    event="webflow-connector.list_collection_items",
)
async def list_collection_items(ctx, params: ListCollectionItemsParams) -> ActionResult:
    conn = await _resolve_connection(ctx, params.connection_id)
    if not conn:
        return ActionResult.error("No Webflow site connected. Use connect_webflow first.", code="WEBFLOW_NOT_CONNECTED")
    body = await wcc.list_items(ctx, conn["token"], params.collection_id, params.limit, params.offset)
    items = body.get("items", []) if isinstance(body, dict) else []
    return ActionResult.success(WebflowCollectionItemList(items=[_to_item(i) for i in items])), summary="Collection items listed."


@chat.function(
    "get_collection_item",
    "Read one CMS Item in full, including all of its field data.",
    action_type="read", chain_callable=True, data_model=WebflowCollectionItem,
    event="webflow-connector.get_collection_item",
)
async def get_collection_item(ctx, params: GetCollectionItemParams) -> ActionResult:
    conn = await _resolve_connection(ctx, params.connection_id)
    if not conn:
        return ActionResult.error("No Webflow site connected. Use connect_webflow first.", code="WEBFLOW_NOT_CONNECTED")
    i = await wcc.get_item(ctx, conn["token"], params.collection_id, params.item_id)
    return ActionResult.success(_to_item(i)), summary="Collection item retrieved."


@chat.function(
    "create_collection_item",
    "Create a new CMS Item (e.g. a new blog post or product) with the given field data. Call get_collection first to see the exact field slugs the Collection expects. Defaults to a draft that will NOT appear on the live site until publish_collection_items is called.",
    action_type="write", chain_callable=True, data_model=WebflowCollectionItem,
    event="webflow-connector.create_collection_item",
    effects=["webflow.item.created"],
)
async def create_collection_item(ctx, params: CreateCollectionItemParams) -> ActionResult:
    conn = await _resolve_connection(ctx, params.connection_id)
    if not conn:
        return ActionResult.error("No Webflow site connected. Use connect_webflow first.", code="WEBFLOW_NOT_CONNECTED")
    i = await wcc.create_item(ctx, conn["token"], params.collection_id, params.field_data, params.is_draft)
    msg = "Item created as a draft -- call publish_collection_items to make it live." if params.is_draft else "Item created and published live."
    return ActionResult.success(_to_item(i), message=msg), summary="Collection item created."


@chat.function(
    "update_collection_item",
    "Update field data on an existing CMS Item. Only the fields you pass are changed.",
    action_type="write", chain_callable=True, data_model=WebflowCollectionItem,
    event="webflow-connector.update_collection_item",
    effects=["webflow.item.updated"],
)
async def update_collection_item(ctx, params: UpdateCollectionItemParams) -> ActionResult:
    conn = await _resolve_connection(ctx, params.connection_id)
    if not conn:
        return ActionResult.error("No Webflow site connected. Use connect_webflow first.", code="WEBFLOW_NOT_CONNECTED")
    i = await wcc.update_item(ctx, conn["token"], params.collection_id, params.item_id, params.field_data, params.is_draft)
    return ActionResult.success(_to_item(i), message="Item updated."), summary="Collection item updated."


@chat.function(
    "delete_collection_item",
    "Permanently delete a CMS Item. Cannot be undone.",
    action_type="write", chain_callable=True, data_model=DeleteResult,
    event="webflow-connector.delete_collection_item",
    effects=["webflow.item.deleted"],
)
async def delete_collection_item(ctx, params: DeleteCollectionItemParams) -> ActionResult:
    conn = await _resolve_connection(ctx, params.connection_id)
    if not conn:
        return ActionResult.error("No Webflow site connected. Use connect_webflow first.", code="WEBFLOW_NOT_CONNECTED")
    await wcc.delete_item(ctx, conn["token"], params.collection_id, params.item_id)
    return ActionResult.success(DeleteResult(id=params.item_id), message="Item deleted."), summary="Collection item deleted."


@chat.function(
    "publish_collection_items",
    "Push one or more staged/draft CMS Items live on the published site -- the step that actually makes new or edited content publicly visible.",
    action_type="write", chain_callable=True, data_model=PublishItemsResult,
    event="webflow-connector.publish_collection_items",
    effects=["webflow.item.published"],
)
async def publish_collection_items(ctx, params: PublishCollectionItemsParams) -> ActionResult:
    conn = await _resolve_connection(ctx, params.connection_id)
    if not conn:
        return ActionResult.error("No Webflow site connected. Use connect_webflow first.", code="WEBFLOW_NOT_CONNECTED")
    await wcc.publish_items(ctx, conn["token"], params.collection_id, params.item_ids)
    return ActionResult.success(
        PublishItemsResult(collection_id=params.collection_id, published_item_ids=params.item_ids),
        message=f"{len(params.item_ids)} item(s) published live.",
    ), summary="Collection items publish requested."
