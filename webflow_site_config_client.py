"""Webflow Data API v2 client functions -- Components (read-only) and
Site Configuration (301 redirects -- Enterprise plan). Reuses
_headers/_check_status from webflow_client.py.
"""
from __future__ import annotations

from webflow_client import _headers, _check_status, _API_BASE  # noqa: F401


# ──────────────────────────────────────────────────────────────────────────
# Components (read-only -- authored only in the Webflow Designer)
# ──────────────────────────────────────────────────────────────────────────


async def list_components(ctx, token: str, site_id: str) -> list[dict]:
    resp = await ctx.http.get(f"{_API_BASE}/sites/{site_id}/components", headers=_headers(token))
    body = _check_status(resp, "list components")
    return body.get("components", []) if isinstance(body, dict) else []


async def get_component_content(ctx, token: str, site_id: str, component_id: str, locale_id: str = "") -> dict:
    params = {"localeId": locale_id} if locale_id else {}
    resp = await ctx.http.get(f"{_API_BASE}/sites/{site_id}/components/{component_id}/dom", headers=_headers(token), params=params)
    return _check_status(resp, "read the component content")


# ──────────────────────────────────────────────────────────────────────────
# Site Configuration -- 301 redirects (Enterprise plan)
# ──────────────────────────────────────────────────────────────────────────


async def list_redirects(ctx, token: str, site_id: str) -> list[dict]:
    resp = await ctx.http.get(f"{_API_BASE}/sites/{site_id}/redirects", headers=_headers(token))
    body = _check_status(resp, "list 301 redirects")
    return body.get("redirects", []) if isinstance(body, dict) else []


async def create_redirect(ctx, token: str, site_id: str, from_url: str, to_url: str) -> dict:
    resp = await ctx.http.post(
        f"{_API_BASE}/sites/{site_id}/redirects",
        headers=_headers(token), json={"fromUrl": from_url, "toUrl": to_url},
    )
    return _check_status(resp, "create the 301 redirect")


async def delete_redirect(ctx, token: str, site_id: str, redirect_id: str) -> dict:
    resp = await ctx.http.delete(f"{_API_BASE}/sites/{site_id}/redirects/{redirect_id}", headers=_headers(token))
    return _check_status(resp, "delete the 301 redirect")
