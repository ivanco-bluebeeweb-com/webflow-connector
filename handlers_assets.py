"""Chat functions for Webflow Connector -- Assets domain (media library)."""
from __future__ import annotations

from imperal_sdk import ActionResult

import webflow_assets_client as wac
from app import chat
from handlers import _resolve_connection
from schemas_assets import (
    ListAssetsParams, WebflowAsset, WebflowAssetList,
    GetAssetParams, UploadAssetFromUrlParams, DeleteAssetParams, DeleteResult,
)


def _to_asset(a: dict) -> WebflowAsset:
    return WebflowAsset(
        id=a.get("id", ""), site_id=a.get("siteId", ""),
        original_file_name=a.get("originalFileName", ""), display_name=a.get("displayName", ""),
        content_type=a.get("contentType", ""), size=int(a.get("size", 0) or 0),
        hosted_url=a.get("hostedUrl", ""), thumbnail_url=(a.get("variants") or [{}])[0].get("hostedUrl", "") if a.get("variants") else "",
        created_on=a.get("createdOn", ""), last_updated=a.get("lastUpdated", ""),
    )


@chat.function(
    "list_assets",
    "List images/files in a Webflow site's media library.",
    action_type="read", chain_callable=True, data_model=WebflowAssetList,
    event="webflow-connector.list_assets",
)
async def list_assets(ctx, params: ListAssetsParams) -> ActionResult:
    conn = await _resolve_connection(ctx, params.connection_id)
    if not conn:
        return ActionResult.error("No Webflow site connected. Use connect_webflow first.", code="WEBFLOW_NOT_CONNECTED")
    body = await wac.list_assets(ctx, conn["token"], params.site_id, params.limit, params.offset)
    items = body.get("assets", []) if isinstance(body, dict) else []
    return ActionResult.success(WebflowAssetList(items=[_to_asset(a) for a in items]), summary="Assets listed.")


@chat.function(
    "get_asset",
    "Read one media library asset's full metadata and hosted URL.",
    action_type="read", chain_callable=True, data_model=WebflowAsset,
    event="webflow-connector.get_asset",
)
async def get_asset(ctx, params: GetAssetParams) -> ActionResult:
    conn = await _resolve_connection(ctx, params.connection_id)
    if not conn:
        return ActionResult.error("No Webflow site connected. Use connect_webflow first.", code="WEBFLOW_NOT_CONNECTED")
    a = await wac.get_asset(ctx, conn["token"], params.asset_id)
    return ActionResult.success(_to_asset(a), summary="Asset retrieved.")


@chat.function(
    "upload_asset_from_url",
    "Add a publicly reachable https:// image/file to a Webflow site's media library, so it can be referenced from CMS Items or page content (e.g. an AI-generated image from Media Studio).",
    action_type="write", chain_callable=True, data_model=WebflowAsset,
    event="webflow-connector.upload_asset_from_url",
    effects=["webflow.asset.uploaded"],
)
async def upload_asset_from_url(ctx, params: UploadAssetFromUrlParams) -> ActionResult:
    conn = await _resolve_connection(ctx, params.connection_id)
    if not conn:
        return ActionResult.error("No Webflow site connected. Use connect_webflow first.", code="WEBFLOW_NOT_CONNECTED")
    a = await wac.upload_asset_from_url(ctx, conn["token"], params.site_id, params.source_url, params.file_name)
    return ActionResult.success(_to_asset(a), message="Asset uploaded to the media library.", summary="Upload asset from url done.")


@chat.function(
    "delete_asset",
    "Permanently delete a media library asset. Cannot be undone -- any page/CMS content still referencing it will show a broken image.",
    action_type="write", chain_callable=True, data_model=DeleteResult,
    event="webflow-connector.delete_asset",
    effects=["webflow.asset.deleted"],
)
async def delete_asset(ctx, params: DeleteAssetParams) -> ActionResult:
    conn = await _resolve_connection(ctx, params.connection_id)
    if not conn:
        return ActionResult.error("No Webflow site connected. Use connect_webflow first.", code="WEBFLOW_NOT_CONNECTED")
    await wac.delete_asset(ctx, conn["token"], params.asset_id)
    return ActionResult.success(DeleteResult(id=params.asset_id), message="Asset deleted.", summary="Asset deleted.")
