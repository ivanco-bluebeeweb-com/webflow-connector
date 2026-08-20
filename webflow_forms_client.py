"""Webflow Data API v2 client functions -- Forms domain (native forms +
submissions). Reuses _headers/_check_status from webflow_client.py.
"""
from __future__ import annotations

from webflow_client import _headers, _check_status, _API_BASE  # noqa: F401


async def list_forms(ctx, token: str, site_id: str) -> list[dict]:
    resp = await ctx.http.get(f"{_API_BASE}/sites/{site_id}/forms", headers=_headers(token))
    body = _check_status(resp, "list forms")
    return body.get("forms", []) if isinstance(body, dict) else []


async def get_form(ctx, token: str, form_id: str) -> dict:
    resp = await ctx.http.get(f"{_API_BASE}/forms/{form_id}", headers=_headers(token))
    return _check_status(resp, "read the form")


async def list_form_submissions(ctx, token: str, form_id: str, limit: int = 50, offset: int = 0) -> dict:
    resp = await ctx.http.get(
        f"{_API_BASE}/forms/{form_id}/submissions",
        headers=_headers(token), params={"limit": limit, "offset": offset},
    )
    return _check_status(resp, "list form submissions")


async def get_form_submission(ctx, token: str, submission_id: str) -> dict:
    resp = await ctx.http.get(f"{_API_BASE}/form_submissions/{submission_id}", headers=_headers(token))
    return _check_status(resp, "read the form submission")


async def delete_form_submission(ctx, token: str, submission_id: str) -> dict:
    resp = await ctx.http.delete(f"{_API_BASE}/form_submissions/{submission_id}", headers=_headers(token))
    return _check_status(resp, "delete the form submission")
