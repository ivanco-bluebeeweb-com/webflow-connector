"""Webflow Data API v2 client functions -- Webhooks + Comments domains.
Reuses _headers/_check_status from webflow_client.py.
"""
from __future__ import annotations

from webflow_client import _headers, _check_status, _API_BASE  # noqa: F401


# ──────────────────────────────────────────────────────────────────────────
# Webhooks
# ──────────────────────────────────────────────────────────────────────────


async def list_webhooks(ctx, token: str, site_id: str) -> list[dict]:
    resp = await ctx.http.get(f"{_API_BASE}/sites/{site_id}/webhooks", headers=_headers(token))
    body = _check_status(resp, "list webhooks")
    return body.get("webhooks", []) if isinstance(body, dict) else []


async def get_webhook(ctx, token: str, webhook_id: str) -> dict:
    resp = await ctx.http.get(f"{_API_BASE}/webhooks/{webhook_id}", headers=_headers(token))
    return _check_status(resp, "read the webhook")


async def create_webhook(ctx, token: str, site_id: str, trigger_type: str, url: str, filter_: dict) -> dict:
    payload = {"triggerType": trigger_type, "url": url}
    if filter_:
        payload["filter"] = filter_
    resp = await ctx.http.post(f"{_API_BASE}/sites/{site_id}/webhooks", headers=_headers(token), json=payload)
    return _check_status(resp, "create the webhook")


async def delete_webhook(ctx, token: str, webhook_id: str) -> dict:
    resp = await ctx.http.delete(f"{_API_BASE}/webhooks/{webhook_id}", headers=_headers(token))
    return _check_status(resp, "delete the webhook")


# ──────────────────────────────────────────────────────────────────────────
# Comments (Webflow Editor comment threads)
# ──────────────────────────────────────────────────────────────────────────


async def list_comment_threads(ctx, token: str, site_id: str, limit: int = 50, offset: int = 0) -> dict:
    resp = await ctx.http.get(
        f"{_API_BASE}/sites/{site_id}/comments/threads",
        headers=_headers(token), params={"limit": limit, "offset": offset},
    )
    return _check_status(resp, "list comment threads")
