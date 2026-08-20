"""Webflow Data API v2 HTTP client -- bearer-token auth against a user's
own Site Token (or Workspace Token), thin wrappers over the REST resource
model documented at developers.webflow.com/data/reference/*.

WHY A SINGLE BEARER TOKEN, NO OAUTH DANCE -- see app.py's module docstring
for the full architectural reasoning (Site Token vs Workspace Token vs
OAuth Data Client App, confirmed during Discovery 2026-08-20).

WHY 401 vs 403 vs 429 ARE HANDLED DIFFERENTLY, SAME PRINCIPLE AS
MuleSoft/UiPath/n8n/Make.com/Power Automate CONNECTOR's clients.

A 401 means the token itself is not accepted (wrong/revoked/expired Site
Token). A 403 means the token is valid but lacks the scope needed for
that specific endpoint (e.g. a token without `cms:write` calling a create
endpoint) -- Webflow scopes are assigned per-token at creation time and
cannot be widened without re-generating the token, so callers need a
clearly different message here vs a bad token. A 429 means Webflow's own
rate limit was hit (documented at developers.webflow.com/data/reference/
rate-limits: 60 requests/minute per site on the default plan, higher on
Enterprise) -- surfaced with the `Retry-After` header value so callers
know how long to back off, not a generic failure.
"""
from __future__ import annotations

import json

_API_BASE = "https://api.webflow.com/v2"


class ClientFail(Exception):
    """Raised internally to short-circuit to a structured error payload."""

    def __init__(self, payload: dict):
        self.payload = payload
        super().__init__(payload.get("error", "Webflow API call failed"))


def _headers(token: str, accept_version: bool = True) -> dict:
    h = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }
    return h


def _check_status(resp, action: str) -> dict | list:
    if resp.status_code in (200, 201, 202, 204):
        if not resp.text:
            return {}
        try:
            return resp.json()
        except Exception:
            return {}
    if resp.status_code == 401:
        raise ClientFail({
            "ok": False,
            "error": f"Webflow rejected the token while trying to {action} -- it may be wrong, revoked, or expired. Generate a fresh Site Token in Site Settings > Apps & integrations > API access.",
            "code": "WEBFLOW_UNAUTHORIZED",
        })
    if resp.status_code == 403:
        raise ClientFail({
            "ok": False,
            "error": f"Webflow accepted the token but it lacks the scope needed to {action}. Site Tokens are scoped at creation time -- generate a new one with the required scope (see developers.webflow.com/data/reference/scopes).",
            "code": "WEBFLOW_FORBIDDEN",
        })
    if resp.status_code == 404:
        raise ClientFail({
            "ok": False,
            "error": f"Webflow could not find the resource to {action} -- it may have been deleted, or the id is wrong.",
            "code": "WEBFLOW_NOT_FOUND",
        })
    if resp.status_code == 429:
        retry_after = resp.headers.get("Retry-After", "a few seconds")
        raise ClientFail({
            "ok": False,
            "error": f"Webflow's own rate limit was hit while trying to {action}. Retry after {retry_after}.",
            "code": "WEBFLOW_RATE_LIMITED",
        })
    detail = ""
    try:
        body = resp.json()
        detail = body.get("message") or body.get("err") or json.dumps(body)[:300]
    except Exception:
        detail = (resp.text or "")[:300]
    raise ClientFail({
        "ok": False,
        "error": f"Webflow returned HTTP {resp.status_code} while trying to {action}: {detail}",
        "code": "WEBFLOW_API_ERROR",
    })


async def verify_connection(ctx, token: str) -> dict:
    """Cheap GET /sites to prove the token actually works before saving it."""
    resp = await ctx.http.get(f"{_API_BASE}/sites", headers=_headers(token))
    try:
        body = _check_status(resp, "verify the connection")
    except ClientFail as e:
        return e.payload
    sites = body.get("sites", []) if isinstance(body, dict) else []
    return {"ok": True, "sites": sites}


# ──────────────────────────────────────────────────────────────────────────
# Sites
# ──────────────────────────────────────────────────────────────────────────


async def list_sites(ctx, token: str) -> list[dict]:
    resp = await ctx.http.get(f"{_API_BASE}/sites", headers=_headers(token))
    body = _check_status(resp, "list sites")
    return body.get("sites", []) if isinstance(body, dict) else []


async def get_site(ctx, token: str, site_id: str) -> dict:
    resp = await ctx.http.get(f"{_API_BASE}/sites/{site_id}", headers=_headers(token))
    return _check_status(resp, "read the site")


async def publish_site(ctx, token: str, site_id: str, custom_domains: list[str], publish_to_subdomain: bool) -> dict:
    payload: dict = {"publishToWebflowSubdomain": publish_to_subdomain}
    if custom_domains:
        payload["customDomains"] = custom_domains
    resp = await ctx.http.post(f"{_API_BASE}/sites/{site_id}/publish", headers=_headers(token), json=payload)
    return _check_status(resp, "publish the site")


# ──────────────────────────────────────────────────────────────────────────
# Pages
# ──────────────────────────────────────────────────────────────────────────


async def list_pages(ctx, token: str, site_id: str, locale_id: str = "", limit: int = 100, offset: int = 0) -> dict:
    params = {"limit": limit, "offset": offset}
    if locale_id:
        params["localeId"] = locale_id
    resp = await ctx.http.get(f"{_API_BASE}/sites/{site_id}/pages", headers=_headers(token), params=params)
    return _check_status(resp, "list pages")


async def get_page_metadata(ctx, token: str, page_id: str) -> dict:
    resp = await ctx.http.get(f"{_API_BASE}/pages/{page_id}", headers=_headers(token))
    return _check_status(resp, "read the page")


async def update_page_metadata(ctx, token: str, page_id: str, fields: dict) -> dict:
    resp = await ctx.http.put(f"{_API_BASE}/pages/{page_id}", headers=_headers(token), json=fields)
    return _check_status(resp, "update the page")


async def get_page_content(ctx, token: str, page_id: str, locale_id: str = "", limit: int = 100, offset: int = 0) -> dict:
    params = {"limit": limit, "offset": offset}
    if locale_id:
        params["localeId"] = locale_id
    resp = await ctx.http.get(f"{_API_BASE}/pages/{page_id}/dom", headers=_headers(token), params=params)
    return _check_status(resp, "read the page content")


async def update_page_content(ctx, token: str, page_id: str, nodes: list[dict], locale_id: str = "") -> dict:
    payload: dict = {"nodes": nodes}
    if locale_id:
        payload["localeId"] = locale_id
    resp = await ctx.http.post(f"{_API_BASE}/pages/{page_id}/dom", headers=_headers(token), json=payload)
    return _check_status(resp, "update the page content")
