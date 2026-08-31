"""Chat functions for Webflow Connector -- core: connection management,
Sites, Pages. Domain-specific handlers (CMS, Assets, Forms, Ecommerce,
Webhooks, Comments, Components, Site Configuration) live in their own
handlers_<domain>.py modules, same convention as Aidentika's
handlers_core.py / handlers_generate.py / handlers_projects.py /
handlers_webhooks.py.
"""
from __future__ import annotations

import uuid

from imperal_sdk import ActionResult

import webflow_client as wc
from app import ext, chat
from schemas import (
    NoParams,
    ConnectWebflowParams, ConnectWebflowWorkspaceParams,
    ProviderConnection, ProviderConnectionList,
    DisconnectWebflowParams, DeleteResult,
    ListSitesParams, WebflowSite, WebflowSiteList,
    GetSiteParams, PublishSiteParams, PublishSiteResult,
    ListPagesParams, WebflowPage, WebflowPageList,
    GetPageParams, UpdatePageMetaParams,
    GetPageContentParams, WebflowPageContent, WebflowPageNode,
    UpdatePageContentParams, DuplicatePageParams,
)

_SECRET_NAME = "webflow_connections"


# ──────────────────────────────────────────────────────────────────────────
# Connection management
# ──────────────────────────────────────────────────────────────────────────


async def _load_connections(ctx) -> list[dict]:
    import json
    raw = await ctx.secrets.get(_SECRET_NAME)
    if not raw:
        return []
    try:
        data = json.loads(raw)
    except Exception:
        return []
    return data if isinstance(data, list) else []


async def _save_connections(ctx, connections: list[dict]) -> None:
    import json
    await ctx.secrets.set(_SECRET_NAME, json.dumps(connections))


async def _resolve_connection(ctx, connection_id: str = "") -> dict | None:
    connections = await _load_connections(ctx)
    if not connections:
        return None
    if connection_id:
        for c in connections:
            if c.get("id") == connection_id:
                return c
        return None
    return connections[0] if connections else None


def _conn_label(site_data: dict, label: str) -> str:
    return label or site_data.get("displayName") or site_data.get("shortName") or site_data.get("id", "")


@chat.function(
    "connect_webflow",
    "Connect a Webflow site by saving its Site Token (Site Settings > Apps & integrations > API access), after checking it actually works.",
    action_type="write", chain_callable=True, data_model=ProviderConnection,
    event="webflow-connector.connect_webflow",
    effects=["webflow.provider.connected"],
)
async def connect_webflow(ctx, params: ConnectWebflowParams) -> ActionResult:
    if not params.site_token:
        return ActionResult.error("A Site Token is required. Generate one in Webflow: Site Settings > Apps & integrations > API access.", code="WEBFLOW_MISSING_TOKEN")
    check = await wc.verify_connection(ctx, params.site_token)
    if not check.get("ok"):
        return ActionResult.error(check.get("error", "Could not verify the Site Token."), code=check.get("code", "WEBFLOW_AUTH_FAILED"))
    sites = check.get("sites", [])
    site_data = sites[0] if sites else {}
    label = _conn_label(site_data, params.label)
    connections = await _load_connections(ctx)
    conn_id = str(uuid.uuid4())
    connections.append({
        "id": conn_id, "kind": "site", "token": params.site_token,
        "title": label, "detail": site_data.get("id", ""),
    })
    await _save_connections(ctx, connections)
    return ActionResult.success(
        ProviderConnection(id=conn_id, title=label, detail=site_data.get("id", ""), kind="site"),
        message=f"Connected Webflow site '{label}'.",
        summary="Webflow connected.",
    )


@chat.function(
    "connect_webflow_workspace",
    "Connect a Webflow Workspace by saving its Workspace Token (read-only, all sites in the workspace), after checking it actually works.",
    action_type="write", chain_callable=True, data_model=ProviderConnection,
    event="webflow-connector.connect_webflow_workspace",
    effects=["webflow.provider.connected"],
)
async def connect_webflow_workspace(ctx, params: ConnectWebflowWorkspaceParams) -> ActionResult:
    if not params.workspace_token:
        return ActionResult.error("A Workspace Token is required.", code="WEBFLOW_MISSING_TOKEN")
    check = await wc.verify_connection(ctx, params.workspace_token)
    if not check.get("ok"):
        return ActionResult.error(check.get("error", "Could not verify the Workspace Token."), code=check.get("code", "WEBFLOW_AUTH_FAILED"))
    label = params.label or "Workspace"
    connections = await _load_connections(ctx)
    conn_id = str(uuid.uuid4())
    connections.append({
        "id": conn_id, "kind": "workspace", "token": params.workspace_token,
        "title": label, "detail": f"{len(check.get('sites', []))} sites",
    })
    await _save_connections(ctx, connections)
    return ActionResult.success(
        ProviderConnection(id=conn_id, title=label, detail=f"{len(check.get('sites', []))} sites", kind="workspace"),
        message=f"Connected Webflow workspace '{label}'.",
        summary="Webflow workspace connected.",
    )


@chat.function(
    "list_connections",
    "List the connected Webflow sites/workspaces.",
    action_type="read", chain_callable=True, data_model=ProviderConnectionList,
    event="webflow-connector.list_connections",
)
async def list_connections(ctx, params: NoParams) -> ActionResult:
    connections = await _load_connections(ctx)
    items = [ProviderConnection(id=c.get("id", ""), title=c.get("title", ""), detail=c.get("detail", ""), kind=c.get("kind", "site")) for c in connections]
    return ActionResult.success(ProviderConnectionList(title="Webflow connections", items=items), summary="Connections listed.")


@chat.function(
    "disconnect_webflow",
    "Disconnect one Webflow site/workspace. Nothing in Webflow itself is changed; the saved token is deleted here.",
    action_type="write", chain_callable=True, data_model=DeleteResult,
    event="webflow-connector.disconnect_webflow",
    effects=["webflow.provider.disconnected"],
)
async def disconnect_webflow(ctx, params: DisconnectWebflowParams) -> ActionResult:
    connections = await _load_connections(ctx)
    remaining = [c for c in connections if c.get("id") != params.connection_id]
    if len(remaining) == len(connections):
        return ActionResult.error("Connection not found.", code="WEBFLOW_NOT_FOUND")
    await _save_connections(ctx, remaining)
    return ActionResult.success(DeleteResult(id=params.connection_id, title="Disconnected", ok=True), message="Webflow connection disconnected.", summary="Webflow disconnected.")


# ──────────────────────────────────────────────────────────────────────────
# Sites
# ──────────────────────────────────────────────────────────────────────────


@chat.function(
    "list_sites",
    "List Webflow sites reachable from the connected token(s).",
    action_type="read", chain_callable=True, data_model=WebflowSiteList,
    event="webflow-connector.list_sites",
)
async def list_sites(ctx, params: ListSitesParams) -> ActionResult:
    conn = await _resolve_connection(ctx, params.connection_id)
    if not conn:
        return ActionResult.error("No Webflow site/workspace connected. Use connect_webflow first.", code="WEBFLOW_NOT_CONNECTED")
    raw_sites = await wc.list_sites(ctx, conn["token"])
    items = [
        WebflowSite(
            id=s.get("id", ""), display_name=s.get("displayName", ""), short_name=s.get("shortName", ""),
            workspace_id=s.get("workspaceId", ""),
            custom_domains=[d.get("url", "") for d in s.get("customDomains", [])] if isinstance(s.get("customDomains"), list) else [],
            last_published=s.get("lastPublished", ""), created_on=s.get("createdOn", ""), preview_url=s.get("previewUrl", ""),
            time_zone=s.get("timeZone", ""), parent_folder_id=s.get("parentFolderId", ""),
        )
        for s in raw_sites
    ]
    return ActionResult.success(WebflowSiteList(title="Webflow sites", items=items), summary="Sites listed.")


@chat.function(
    "get_site",
    "Read one Webflow site in full.",
    action_type="read", chain_callable=True, data_model=WebflowSite,
    event="webflow-connector.get_site",
)
async def get_site(ctx, params: GetSiteParams) -> ActionResult:
    conn = await _resolve_connection(ctx, params.connection_id)
    if not conn:
        return ActionResult.error("No Webflow site connected. Use connect_webflow first.", code="WEBFLOW_NOT_CONNECTED")
    s = await wc.get_site(ctx, conn["token"], params.site_id)
    return ActionResult.success(WebflowSite(
        id=s.get("id", ""), display_name=s.get("displayName", ""), short_name=s.get("shortName", ""),
        workspace_id=s.get("workspaceId", ""),
        custom_domains=[d.get("url", "") for d in s.get("customDomains", [])] if isinstance(s.get("customDomains"), list) else [],
        last_published=s.get("lastPublished", ""), created_on=s.get("createdOn", ""), preview_url=s.get("previewUrl", ""),
        time_zone=s.get("timeZone", ""), parent_folder_id=s.get("parentFolderId", ""),
    ), summary="Site retrieved.")


@chat.function(
    "publish_site",
    "Publish a Webflow site to its live domain(s) and/or webflow.io staging domain -- pushes any staged CMS/page changes live. Confirm with the user before calling this on a production domain.",
    action_type="write", chain_callable=True, data_model=PublishSiteResult,
    event="webflow-connector.publish_site",
    effects=["webflow.site.published"],
)
async def publish_site(ctx, params: PublishSiteParams) -> ActionResult:
    conn = await _resolve_connection(ctx, params.connection_id)
    if not conn:
        return ActionResult.error("No Webflow site connected. Use connect_webflow first.", code="WEBFLOW_NOT_CONNECTED")
    domains = params.custom_domains or None
    await wc.publish_site(ctx, conn["token"], params.site_id, domains)
    return ActionResult.success(
        PublishSiteResult(site_id=params.site_id, queued=True, domains=params.custom_domains),
        message="Site publish requested.",
        summary="Site publish requested.",
    )


# ──────────────────────────────────────────────────────────────────────────
# Pages
# ──────────────────────────────────────────────────────────────────────────


@chat.function(
    "list_pages",
    "List the pages (and page folders) of a Webflow site.",
    action_type="read", chain_callable=True, data_model=WebflowPageList,
    event="webflow-connector.list_pages",
)
async def list_pages(ctx, params: ListPagesParams) -> ActionResult:
    conn = await _resolve_connection(ctx, params.connection_id)
    if not conn:
        return ActionResult.error("No Webflow site connected. Use connect_webflow first.", code="WEBFLOW_NOT_CONNECTED")
    raw_pages = await wc.list_pages(ctx, conn["token"], params.site_id)
    items = [
        WebflowPage(
            id=p.get("id", ""), site_id=p.get("siteId", ""), title=p.get("title", ""), slug=p.get("slug", ""),
            parent_id=p.get("parentId", "") or "", collection_id=p.get("collectionId", "") or "",
            created_on=p.get("createdOn", ""), last_updated=p.get("lastUpdated", ""),
            archived=bool(p.get("archived", False)), draft=bool(p.get("draft", False)),
            can_branch=bool(p.get("canBranch", False)), seo_title=(p.get("seo") or {}).get("title", ""),
            seo_description=(p.get("seo") or {}).get("description", ""),
        )
        for p in raw_pages
    ]
    return ActionResult.success(WebflowPageList(title="Pages", items=items), summary="Pages listed.")


@chat.function(
    "get_page",
    "Read one Webflow page's metadata (title, slug, SEO fields, publish state) -- not its content nodes, use get_page_content for those.",
    action_type="read", chain_callable=True, data_model=WebflowPage,
    event="webflow-connector.get_page",
)
async def get_page(ctx, params: GetPageParams) -> ActionResult:
    conn = await _resolve_connection(ctx, params.connection_id)
    if not conn:
        return ActionResult.error("No Webflow site connected. Use connect_webflow first.", code="WEBFLOW_NOT_CONNECTED")
    p = await wc.get_page_metadata(ctx, conn["token"], params.page_id)
    return ActionResult.success(WebflowPage(
        id=p.get("id", ""), site_id=p.get("siteId", ""), title=p.get("title", ""), slug=p.get("slug", ""),
        parent_id=p.get("parentId", "") or "", collection_id=p.get("collectionId", "") or "",
        created_on=p.get("createdOn", ""), last_updated=p.get("lastUpdated", ""),
        archived=bool(p.get("archived", False)), draft=bool(p.get("draft", False)),
        can_branch=bool(p.get("canBranch", False)), seo_title=(p.get("seo") or {}).get("title", ""),
        seo_description=(p.get("seo") or {}).get("description", ""),
    ), summary="Page retrieved.")


@chat.function(
    "update_page_metadata",
    "Update a Webflow page's title, slug, SEO title/description, and/or Open Graph image -- does not touch the page's content nodes.",
    action_type="write", chain_callable=True, data_model=WebflowPage,
    event="webflow-connector.update_page_metadata",
    effects=["webflow.page.metadata_updated"],
)
async def update_page_metadata(ctx, params: UpdatePageMetaParams) -> ActionResult:
    conn = await _resolve_connection(ctx, params.connection_id)
    if not conn:
        return ActionResult.error("No Webflow site connected. Use connect_webflow first.", code="WEBFLOW_NOT_CONNECTED")
    payload: dict = {}
    if params.title:
        payload["title"] = params.title
    if params.slug:
        payload["slug"] = params.slug
    seo: dict = {}
    if params.seo_title:
        seo["title"] = params.seo_title
    if params.seo_description:
        seo["description"] = params.seo_description
    if seo:
        payload["seo"] = seo
    if params.og_image_url:
        payload["openGraphImage"] = params.og_image_url
    p = await wc.update_page_metadata(ctx, conn["token"], params.page_id, payload)
    return ActionResult.success(WebflowPage(
        id=p.get("id", ""), site_id=p.get("siteId", ""), title=p.get("title", ""), slug=p.get("slug", ""),
        parent_id=p.get("parentId", "") or "", collection_id=p.get("collectionId", "") or "",
        created_on=p.get("createdOn", ""), last_updated=p.get("lastUpdated", ""),
        archived=bool(p.get("archived", False)), draft=bool(p.get("draft", False)),
        can_branch=bool(p.get("canBranch", False)), seo_title=(p.get("seo") or {}).get("title", ""),
        seo_description=(p.get("seo") or {}).get("description", ""),
    ), message="Page metadata updated.", summary="Page metadata updated.")


@chat.function(
    "get_page_content",
    "Read one Webflow page's DOM nodes (the actual editable page content -- text nodes and component instances), for review or before making a targeted edit.",
    action_type="read", chain_callable=True, data_model=WebflowPageContent,
    event="webflow-connector.get_page_content",
)
async def get_page_content(ctx, params: GetPageContentParams) -> ActionResult:
    conn = await _resolve_connection(ctx, params.connection_id)
    if not conn:
        return ActionResult.error("No Webflow site connected. Use connect_webflow first.", code="WEBFLOW_NOT_CONNECTED")
    body = await wc.get_page_content(ctx, conn["token"], params.page_id, params.locale_id)
    nodes = [
        WebflowPageNode(
            id=n.get("id", ""), type=n.get("type", ""), tag=n.get("tag", ""),
            text=(n.get("text") or {}).get("text", "") if isinstance(n.get("text"), dict) else str(n.get("text") or ""),
        )
        for n in (body.get("nodes", []) if isinstance(body, dict) else [])
    ]
    return ActionResult.success(WebflowPageContent(page_id=params.page_id, nodes=nodes), summary="Page content retrieved.")


@chat.function(
    "update_page_content",
    "Update one or more DOM text nodes on a Webflow page -- e.g. change a heading's or paragraph's text. Pass node ids from get_page_content plus their new text.",
    action_type="write", chain_callable=True, data_model=WebflowPageContent,
    event="webflow-connector.update_page_content",
    effects=["webflow.page.content_updated"],
)
async def update_page_content(ctx, params: UpdatePageContentParams) -> ActionResult:
    conn = await _resolve_connection(ctx, params.connection_id)
    if not conn:
        return ActionResult.error("No Webflow site connected. Use connect_webflow first.", code="WEBFLOW_NOT_CONNECTED")
    updates = [{"nodeId": u.node_id, "text": {"text": u.text, "html": u.text}} for u in params.updates]
    body = await wc.update_page_content(ctx, conn["token"], params.page_id, updates, params.locale_id)
    nodes = [
        WebflowPageNode(
            id=n.get("id", ""), type=n.get("type", ""), tag=n.get("tag", ""),
            text=(n.get("text") or {}).get("text", "") if isinstance(n.get("text"), dict) else str(n.get("text") or ""),
        )
        for n in (body.get("nodes", []) if isinstance(body, dict) else [])
    ]
    return ActionResult.success(WebflowPageContent(page_id=params.page_id, nodes=nodes), message="Page content updated.", summary="Page content updated.")


@chat.function(
    "duplicate_page",
    "Duplicate an existing Webflow page under a new title/slug -- a quick way to spin up an A/B variant or a localized copy without rebuilding it from scratch in the Designer.",
    action_type="write", chain_callable=True, data_model=WebflowPage,
    event="webflow-connector.duplicate_page",
    effects=["webflow.page.duplicated"],
)
async def duplicate_page(ctx, params: DuplicatePageParams) -> ActionResult:
    conn = await _resolve_connection(ctx, params.connection_id)
    if not conn:
        return ActionResult.error("No Webflow site connected. Use connect_webflow first.", code="WEBFLOW_NOT_CONNECTED")
    p = await wc.duplicate_page(ctx, conn["token"], params.page_id, params.title, params.slug)
    return ActionResult.success(WebflowPage(
        id=p.get("id", ""), site_id=p.get("siteId", ""), title=p.get("title", ""), slug=p.get("slug", ""),
        parent_id=p.get("parentId", "") or "", collection_id=p.get("collectionId", "") or "",
        created_on=p.get("createdOn", ""), last_updated=p.get("lastUpdated", ""),
        archived=bool(p.get("archived", False)), draft=bool(p.get("draft", False)),
        can_branch=bool(p.get("canBranch", False)), seo_title=(p.get("seo") or {}).get("title", ""),
        seo_description=(p.get("seo") or {}).get("description", ""),
    ), message="Page duplicated.", summary="Duplicate page done.")
