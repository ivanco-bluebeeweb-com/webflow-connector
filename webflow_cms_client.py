"""Webflow Data API v2 client functions -- CMS domain (Collections,
Collection Fields, Collection Items). Reuses _headers/_check_status from
webflow_client.py so error handling (401/403/404/429) stays identical
across every domain module.

WHY STAGED vs LIVE ITEMS ARE TWO CALL SHAPES, NOT ONE. Webflow's CMS
model lets an Item exist in a "staged" (draft) state that only becomes
visible on the published site once explicitly pushed live -- either by
creating with isDraft=false (rare, most integrations want to review
first) or by calling the dedicated /publish endpoint. create_item
defaults is_draft=True so a new item never silently goes live without an
explicit publish_collection_items call, matching this connector's general
"never silently mutate what a visitor sees" posture.
"""
from __future__ import annotations

from webflow_client import _headers, _check_status, _API_BASE  # noqa: F401


# ──────────────────────────────────────────────────────────────────────────
# Collections
# ──────────────────────────────────────────────────────────────────────────


async def list_collections(ctx, token: str, site_id: str) -> list[dict]:
    resp = await ctx.http.get(f"{_API_BASE}/sites/{site_id}/collections", headers=_headers(token))
    body = _check_status(resp, "list collections")
    return body.get("collections", []) if isinstance(body, dict) else []


async def get_collection(ctx, token: str, collection_id: str) -> dict:
    resp = await ctx.http.get(f"{_API_BASE}/collections/{collection_id}", headers=_headers(token))
    return _check_status(resp, "read the collection")


async def create_collection(ctx, token: str, site_id: str, display_name: str, singular_name: str, slug: str = "") -> dict:
    payload = {"displayName": display_name, "singularName": singular_name}
    if slug:
        payload["slug"] = slug
    resp = await ctx.http.post(f"{_API_BASE}/sites/{site_id}/collections", headers=_headers(token), json=payload)
    return _check_status(resp, "create the collection")


async def delete_collection(ctx, token: str, collection_id: str) -> dict:
    resp = await ctx.http.delete(f"{_API_BASE}/collections/{collection_id}", headers=_headers(token))
    return _check_status(resp, "delete the collection")


# ──────────────────────────────────────────────────────────────────────────
# Collection Fields
# ──────────────────────────────────────────────────────────────────────────


async def create_collection_field(ctx, token: str, collection_id: str, display_name: str, field_type: str, is_required: bool = False, help_text: str = "") -> dict:
    payload = {
        "displayName": display_name,
        "type": field_type,
        "isRequired": is_required,
    }
    if help_text:
        payload["helpText"] = help_text
    resp = await ctx.http.post(f"{_API_BASE}/collections/{collection_id}/fields", headers=_headers(token), json=payload)
    return _check_status(resp, "create the collection field")


# ──────────────────────────────────────────────────────────────────────────
# Collection Items
# ──────────────────────────────────────────────────────────────────────────


async def list_items(ctx, token: str, collection_id: str, limit: int = 100, offset: int = 0) -> dict:
    resp = await ctx.http.get(
        f"{_API_BASE}/collections/{collection_id}/items",
        headers=_headers(token), params={"limit": limit, "offset": offset},
    )
    return _check_status(resp, "list collection items")


async def get_item(ctx, token: str, collection_id: str, item_id: str) -> dict:
    resp = await ctx.http.get(f"{_API_BASE}/collections/{collection_id}/items/{item_id}", headers=_headers(token))
    return _check_status(resp, "read the collection item")


async def create_item(ctx, token: str, collection_id: str, field_data: dict, is_draft: bool = True) -> dict:
    payload = {"isDraft": is_draft, "fieldData": field_data}
    resp = await ctx.http.post(f"{_API_BASE}/collections/{collection_id}/items", headers=_headers(token), json=payload)
    return _check_status(resp, "create the collection item")


async def create_items_bulk(ctx, token: str, collection_id: str, items: list[dict], is_draft: bool = True) -> dict:
    payload = {"items": [{"isDraft": is_draft, "fieldData": fd} for fd in items]}
    resp = await ctx.http.post(f"{_API_BASE}/collections/{collection_id}/items/bulk", headers=_headers(token), json=payload)
    return _check_status(resp, "bulk-create collection items")


async def update_item(ctx, token: str, collection_id: str, item_id: str, field_data: dict, is_draft: bool | None = None) -> dict:
    item: dict = {"fieldData": field_data}
    if is_draft is not None:
        item["isDraft"] = is_draft
    resp = await ctx.http.patch(f"{_API_BASE}/collections/{collection_id}/items/{item_id}", headers=_headers(token), json=item)
    return _check_status(resp, "update the collection item")


async def delete_item(ctx, token: str, collection_id: str, item_id: str) -> dict:
    resp = await ctx.http.delete(f"{_API_BASE}/collections/{collection_id}/items/{item_id}", headers=_headers(token))
    return _check_status(resp, "delete the collection item")


async def publish_items(ctx, token: str, collection_id: str, item_ids: list[str]) -> dict:
    resp = await ctx.http.post(
        f"{_API_BASE}/collections/{collection_id}/items/publish",
        headers=_headers(token), json={"itemIds": item_ids},
    )
    return _check_status(resp, "publish collection items")
