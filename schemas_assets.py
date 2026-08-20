"""Pydantic params models + SDL entity contracts for Webflow Connector's
Assets domain -- the site media library (images/files) plus Custom Fonts.
Confirmed against developers.webflow.com/data/reference/assets/* and
/data/reference/custom-fonts/* during Discovery 2026-08-20.

WHY UPLOAD IS TWO-STEP. Webflow's own Create Asset endpoint does not
accept raw bytes -- it returns a pre-signed AWS S3 POST URL + form fields;
the caller (or the browser) then POSTs the file bytes directly to S3.
upload_asset_from_url therefore takes an already-public https:// URL (the
same shape as WordPress Hub's upload_media) and streams it through that
S3 POST server-side, so callers never have to juggle raw multipart bytes
or S3 form fields themselves.
"""
from __future__ import annotations

from pydantic import BaseModel, Field
from imperal_sdk import sdl

from schemas import DeleteResult  # noqa: F401 -- re-exported for handlers_assets.py


class ListAssetsParams(BaseModel):
    connection_id: str = Field("", description="Connection id from list_connections. Omit if only one is connected.")
    site_id: str = Field(..., description="Site id from list_sites.")
    limit: int = Field(100, ge=1, le=100, description="Max assets to return (1-100).")
    offset: int = Field(0, ge=0, description="Pagination offset.")


class WebflowAsset(sdl.Entity):
    id: str
    site_id: str = ""
    original_file_name: str = ""
    display_name: str = ""
    content_type: str = ""
    size: int = 0
    hosted_url: str = ""
    thumbnail_url: str = ""
    created_on: str = ""
    last_updated: str = ""


class WebflowAssetList(sdl.Entity):
    title: str = "Assets"
    items: list[WebflowAsset] = []


class GetAssetParams(BaseModel):
    connection_id: str = Field("", description="Connection id from list_connections. Omit if only one is connected.")
    asset_id: str = Field(..., description="Asset id from list_assets.")


class UploadAssetFromUrlParams(BaseModel):
    connection_id: str = Field("", description="Connection id from list_connections. Omit if only one is connected.")
    site_id: str = Field(..., description="Site id from list_sites.")
    source_url: str = Field(..., description="Publicly reachable https:// URL of the image/file to add to this site's Assets library.")
    file_name: str = Field(..., description="File name to store it under, including extension, e.g. 'hero-image.jpg'.")


class UpdateAssetParams(BaseModel):
    connection_id: str = Field("", description="Connection id from list_connections. Omit if only one is connected.")
    asset_id: str = Field(..., description="Asset id from list_assets.")
    display_name: str = Field(..., description="New display name for the asset.")


class DeleteAssetParams(BaseModel):
    connection_id: str = Field("", description="Connection id from list_connections. Omit if only one is connected.")
    asset_id: str = Field(..., description="Asset id from list_assets.")


class CreateAssetFolderParams(BaseModel):
    connection_id: str = Field("", description="Connection id from list_connections. Omit if only one is connected.")
    site_id: str = Field(..., description="Site id from list_sites.")
    display_name: str = Field(..., description="Folder name shown in the Assets panel.")
    parent_folder_id: str = Field("", description="Parent folder id, to nest this folder. Omit for a top-level folder.")


class WebflowAssetFolder(sdl.Entity):
    id: str
    display_name: str = ""
    parent_folder_id: str = ""
    asset_ids: list[str] = []


class ListAssetFoldersParams(BaseModel):
    connection_id: str = Field("", description="Connection id from list_connections. Omit if only one is connected.")
    site_id: str = Field(..., description="Site id from list_sites.")


class WebflowAssetFolderList(sdl.Entity):
    title: str = "Asset folders"
    items: list[WebflowAssetFolder] = []


class ListCustomFontsParams(BaseModel):
    connection_id: str = Field("", description="Connection id from list_connections. Omit if only one is connected.")
    site_id: str = Field(..., description="Site id from list_sites.")


class WebflowCustomFont(sdl.Entity):
    id: str
    display_name: str = ""
    variant_count: int = 0


class WebflowCustomFontList(sdl.Entity):
    title: str = "Custom fonts"
    items: list[WebflowCustomFont] = []
