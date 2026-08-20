"""Pydantic params models + SDL entity contracts for Webflow Connector's
Components domain (reusable page fragments -- read-only via Data API, no
create/delete: Components are authored only in the Designer) and Site
Configuration domain (301 redirects, robots.txt override, well-known
files -- Enterprise-plan features). Confirmed against
developers.webflow.com/data/reference/pages-and-components/components/*
and /data/reference/enterprise/site-configuration/* during Discovery
2026-08-20.
"""
from __future__ import annotations

from pydantic import BaseModel, Field
from imperal_sdk import sdl

from schemas import DeleteResult  # noqa: F401 -- re-exported for handlers_site_config.py


# ──────────────────────────────────────────────────────────────────────────
# Components (read-only -- authored only in the Webflow Designer)
# ──────────────────────────────────────────────────────────────────────────


class ListComponentsParams(BaseModel):
    connection_id: str = Field("", description="Connection id from list_connections. Omit if only one is connected.")
    site_id: str = Field(..., description="Site id from list_sites.")


class WebflowComponent(sdl.Entity):
    id: str
    name: str = ""
    group: str = ""
    readonly: bool = True


class WebflowComponentList(sdl.Entity):
    title: str = "Components"
    items: list[WebflowComponent] = []


class GetComponentContentParams(BaseModel):
    connection_id: str = Field("", description="Connection id from list_connections. Omit if only one is connected.")
    site_id: str = Field(..., description="Site id from list_sites.")
    component_id: str = Field(..., description="Component id from list_components.")
    locale_id: str = Field("", description="Optional locale id, for sites with localization enabled.")


class WebflowComponentContent(sdl.Entity):
    component_id: str
    nodes: list[dict] = []


# ──────────────────────────────────────────────────────────────────────────
# Site Configuration (Enterprise plan)
# ──────────────────────────────────────────────────────────────────────────


class ListRedirectsParams(BaseModel):
    connection_id: str = Field("", description="Connection id from list_connections. Omit if only one is connected.")
    site_id: str = Field(..., description="Site id from list_sites.")


class WebflowRedirect(sdl.Entity):
    id: str
    from_url: str = ""
    to_url: str = ""


class WebflowRedirectList(sdl.Entity):
    title: str = "301 redirects"
    items: list[WebflowRedirect] = []


class CreateRedirectParams(BaseModel):
    connection_id: str = Field("", description="Connection id from list_connections. Omit if only one is connected.")
    site_id: str = Field(..., description="Site id from list_sites.")
    from_url: str = Field(..., description="Path to redirect FROM, relative to the site root, e.g. '/old-page'.")
    to_url: str = Field(..., description="Full destination URL or path to redirect TO.")


class DeleteRedirectParams(BaseModel):
    connection_id: str = Field("", description="Connection id from list_connections. Omit if only one is connected.")
    site_id: str = Field(..., description="Site id from list_sites.")
    redirect_id: str = Field(..., description="Redirect id from list_redirects.")
