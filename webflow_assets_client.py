"""Webflow Data API v2 client functions -- Assets domain (media library,
folders, custom fonts). Reuses _headers/_check_status from
webflow_client.py.

WHY UPLOAD GOES THROUGH A PRE-SIGNED S3 POST, NOT A DIRECT PUT. Confirmed
during Discovery 2026-08-20 (developers.webflow.com/data/reference/assets/
assets/create): Webflow's own Create Asset endpoint registers the asset
record and returns an S3 `uploadUrl` + `uploadDetails` form-field map; the
actual file bytes are then POSTed to that S3 URL as multipart form data,
never to api.webflow.com itself. upload_asset_from_url fetches the source
URL's bytes once, then performs that second POST server-side so callers
only ever deal with a single https:// URL.
"""
from __future__ import annotations

from webflow_client import _headers, _check_status, ClientFail, _API_BASE  # noqa: F401


async def list_assets(ctx, token: str, site_id: str, limit: int = 100, offset: int = 0) -> dict:
    resp = await ctx.http.get(f"{_API_BASE}/sites/{site_id}/assets", headers=_headers(token), params={"limit": limit, "offset": offset})
    return _check_status(resp, "list assets")


async def get_asset(ctx, token: str, asset_id: str) -> dict:
    resp = await ctx.http.get(f"{_API_BASE}/assets/{asset_id}", headers=_headers(token))
    return _check_status(resp, "read the asset")


async def upload_asset_from_url(ctx, token: str, site_id: str, source_url: str, file_name: str) -> dict:
    """Two-step upload: (1) fetch the source file's bytes and hash, (2)
    register the asset to get a pre-signed S3 POST, (3) POST the bytes to
    S3. Returns the final registered asset record."""
    import hashlib

    src_resp = await ctx.http.get(source_url)
    if src_resp.status_code >= 400:
        raise ClientFail({
            "ok": False,
            "error": f"Could not fetch the source file at {source_url} (HTTP {src_resp.status_code}).",
            "code": "WEBFLOW_SOURCE_FETCH_FAILED",
        })
    file_bytes = src_resp.content
    file_hash = hashlib.md5(file_bytes).hexdigest()

    reg_resp = await ctx.http.post(
        f"{_API_BASE}/sites/{site_id}/assets",
        headers=_headers(token),
        json={"fileName": file_name, "fileHash": file_hash},
    )
    reg = _check_status(reg_resp, "register the asset")
    upload_url = reg.get("uploadUrl")
    upload_details = reg.get("uploadDetails", {})
    if not upload_url:
        raise ClientFail({
            "ok": False,
            "error": "Webflow did not return an upload URL for this asset -- it may already exist with the same file hash.",
            "code": "WEBFLOW_ASSET_REGISTER_FAILED",
        })

    form_fields = {k: (None, str(v)) for k, v in upload_details.items()}
    form_fields["file"] = (file_name, file_bytes)
    up_resp = await ctx.http.post(upload_url, files=form_fields)
    if up_resp.status_code >= 300:
        raise ClientFail({
            "ok": False,
            "error": f"Webflow's storage rejected the upload (HTTP {up_resp.status_code}). The asset record was registered but has no file attached.",
            "code": "WEBFLOW_ASSET_UPLOAD_FAILED",
        })
    return reg


async def update_asset(ctx, token: str, asset_id: str, display_name: str) -> dict:
    resp = await ctx.http.patch(f"{_API_BASE}/assets/{asset_id}", headers=_headers(token), json={"displayName": display_name})
    return _check_status(resp, "update the asset")


async def delete_asset(ctx, token: str, asset_id: str) -> dict:
    resp = await ctx.http.delete(f"{_API_BASE}/assets/{asset_id}", headers=_headers(token))
    return _check_status(resp, "delete the asset")


async def create_asset_folder(ctx, token: str, site_id: str, display_name: str, parent_folder_id: str = "") -> dict:
    payload = {"displayName": display_name}
    if parent_folder_id:
        payload["parentFolder"] = parent_folder_id
    resp = await ctx.http.post(f"{_API_BASE}/sites/{site_id}/asset_folders", headers=_headers(token), json=payload)
    return _check_status(resp, "create the asset folder")


async def list_asset_folders(ctx, token: str, site_id: str) -> list[dict]:
    resp = await ctx.http.get(f"{_API_BASE}/sites/{site_id}/asset_folders", headers=_headers(token))
    body = _check_status(resp, "list asset folders")
    return body.get("assetFolders", []) if isinstance(body, dict) else []


async def list_custom_fonts(ctx, token: str, site_id: str) -> list[dict]:
    resp = await ctx.http.get(f"{_API_BASE}/sites/{site_id}/customFonts", headers=_headers(token))
    body = _check_status(resp, "list custom fonts")
    return body.get("customFonts", []) if isinstance(body, dict) else []
