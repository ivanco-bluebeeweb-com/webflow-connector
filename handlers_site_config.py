"""Chat functions for Webflow Connector -- Components (read-only) and
Site Configuration (301 redirects -- Enterprise plan)."""
from __future__ import annotations

from imperal_sdk import ActionResult

import webflow_site_config_client as wsc
from app import chat
from handlers import _resolve_connection
from schemas_site_config import (
    ListComponentsParams, WebflowComponent, WebflowComponentList,
    GetComponentContentParams, WebflowComponentContent,
    ListRedirectsParams, WebflowRedirect, WebflowRedirectList,
    CreateRedirectParams, DeleteRedirectParams, DeleteResult,
)


@chat.function(
    "list_components",
    "List reusable Components on a Webflow site (shared page fragments authored in the Designer, e.g. a shared header/footer/card). Read-only -- Components can only be created/edited inside the Webflow Designer itself.",
    action_type="read", chain_callable=True, data_model=WebflowComponentList,
    event="webflow-connector.list_components",
)
async def list_components(ctx, params: ListComponentsParams) -> ActionResult:
    conn = await _resolve_connection(ctx, params.connection_id)
    if not conn:
        return ActionResult.error("No Webflow site connected. Use connect_webflow first.", code="WEBFLOW_NOT_CONNECTED")
    raw = await wsc.list_components(ctx, conn["token"], params.site_id)
    items = [WebflowComponent(id=c.get("id", ""), name=c.get("name", ""), group=c.get("group", "") or "") for c in raw]
    return ActionResult.success(WebflowComponentList(items=items), summary="Components listed.")


@chat.function(
    "get_component_content",
    "Read one Component's DOM node tree -- what's actually inside a reusable Component instance.",
    action_type="read", chain_callable=True, data_model=WebflowComponentContent,
    event="webflow-connector.get_component_content",
)
async def get_component_content(ctx, params: GetComponentContentParams) -> ActionResult:
    conn = await _resolve_connection(ctx, params.connection_id)
    if not conn:
        return ActionResult.error("No Webflow site connected. Use connect_webflow first.", code="WEBFLOW_NOT_CONNECTED")
    body = await wsc.get_component_content(ctx, conn["token"], params.site_id, params.component_id, params.locale_id)
    return ActionResult.success(WebflowComponentContent(component_id=params.component_id, nodes=body.get("nodes", []) if isinstance(body, dict) else []), summary="Component content retrieved.")


@chat.function(
    "list_redirects",
    "List 301 URL redirects configured on a Webflow site (Enterprise plan feature) -- which old URLs redirect to which new ones.",
    action_type="read", chain_callable=True, data_model=WebflowRedirectList,
    event="webflow-connector.list_redirects",
)
async def list_redirects(ctx, params: ListRedirectsParams) -> ActionResult:
    conn = await _resolve_connection(ctx, params.connection_id)
    if not conn:
        return ActionResult.error("No Webflow site connected. Use connect_webflow first.", code="WEBFLOW_NOT_CONNECTED")
    raw = await wsc.list_redirects(ctx, conn["token"], params.site_id)
    items = [WebflowRedirect(id=r.get("id", ""), from_url=r.get("fromUrl", ""), to_url=r.get("toUrl", "")) for r in raw]
    return ActionResult.success(WebflowRedirectList(items=items), summary="Redirects listed.")


@chat.function(
    "create_redirect",
    "Create a 301 redirect from an old URL to a new one (Enterprise plan feature) -- essential after a page slug change or migration, so old links/backlinks/search rankings aren't lost.",
    action_type="write", chain_callable=True, data_model=WebflowRedirect,
    event="webflow-connector.create_redirect",
    effects=["webflow.redirect.created"],
)
async def create_redirect(ctx, params: CreateRedirectParams) -> ActionResult:
    conn = await _resolve_connection(ctx, params.connection_id)
    if not conn:
        return ActionResult.error("No Webflow site connected. Use connect_webflow first.", code="WEBFLOW_NOT_CONNECTED")
    r = await wsc.create_redirect(ctx, conn["token"], params.site_id, params.from_url, params.to_url)
    return ActionResult.success(WebflowRedirect(id=r.get("id", ""), from_url=r.get("fromUrl", params.from_url), to_url=r.get("toUrl", params.to_url)), message="Redirect created.", summary="Redirect created.")


@chat.function(
    "delete_redirect",
    "Permanently delete a 301 redirect.",
    action_type="write", chain_callable=True, data_model=DeleteResult,
    event="webflow-connector.delete_redirect",
    effects=["webflow.redirect.deleted"],
)
async def delete_redirect(ctx, params: DeleteRedirectParams) -> ActionResult:
    conn = await _resolve_connection(ctx, params.connection_id)
    if not conn:
        return ActionResult.error("No Webflow site connected. Use connect_webflow first.", code="WEBFLOW_NOT_CONNECTED")
    await wsc.delete_redirect(ctx, conn["token"], params.site_id, params.redirect_id)
    return ActionResult.success(DeleteResult(id=params.redirect_id), message="Redirect deleted.", summary="Redirect deleted.")
