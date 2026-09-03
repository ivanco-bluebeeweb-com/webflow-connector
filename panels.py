"""Panel UI -- connections list/connect form + connected Sites list.

SIDEBAR CONTENT -- NO CARDS ANYWHERE, per ~/UI_INTERFACE_STANDARD.md's
"left sidebar, no decorated cards" rule (same convention as MuleSoft
Connector's / UiPath Connector's / Power Automate Connector's panels.py).

Every section (connections, connect form, sites) is a plain ui.Stack,
content stacked vertically and left-aligned, sections separated by
ui.Divider() -- no Card border/background/shadow anywhere in this slot.
Disconnect lives only in the "App settings" screen (panels_settings.py).
The one secondary "App settings" button is always the LAST element at the
bottom of the sidebar.

WHY A SIMPLE TOKEN FIELD, NOT A MULTI-FIELD FORM LIKE UiPath/MuleSoft.

Webflow's Site Token is a single opaque string generated in the Webflow
Designer itself (Site Settings > Apps & integrations > API access) -- no
client_id/secret/org/tenant quadruple to collect, so the form is a single
Password field plus an optional label, with a help panel (opened via
ui.Call("__panel__webflow_connect_help")) explaining exactly where to
generate that token in Webflow's own UI.

CENTER SLOT -- per ~/UI_INTERFACE_STANDARD.md, an app with no dedicated
center content needs a base (non-overlay) center panel with the canonical
"Nothing to show here" text, registered with center_overlay=True so the
session-init batch actually picks it up.
"""
from __future__ import annotations

from imperal_sdk import ui

from app import ext
import handlers as h


def _settings_button() -> ui.UINode:
    """The one required secondary entry point into the settings screen --
    always the last element at the bottom of the sidebar."""
    return ui.Button(
        "App settings", variant="secondary", size="sm", icon="settings", on_click=ui.Call("__panel__webflow_settings"),
    )


def _connection_row(c: dict) -> ui.UINode:
    label = c.get("title") or c.get("id", "")
    detail = c.get("detail", "") or c.get("kind", "")
    return ui.Stack(direction="v", gap=1, children=[
        ui.Text(label, variant="body"),
        ui.Text(detail, variant="caption"),
    ])


def _connections_section(connections: list[dict]) -> ui.UINode:
    if not connections:
        return ui.Text("No Webflow sites connected yet.", variant="caption")
    children: list[ui.UINode] = []
    for i, c in enumerate(connections):
        if i > 0:
            children.append(ui.Divider())
        children.append(_connection_row(c))
    return ui.Stack(direction="v", gap=2, children=children)


def _site_row(s) -> ui.UINode:
    """One connected Webflow site row -- plain content, no Card wrapper."""
    return ui.Stack(direction="v", gap=1, children=[
        ui.Text(s.display_name or s.short_name or s.id, variant="body"),
        ui.Text(s.default_domain or s.short_name, variant="caption"),
    ])


def _sites_section(sites: list) -> ui.UINode:
    if not sites:
        return ui.Text("No sites found on this connection yet.", variant="caption")
    children: list[ui.UINode] = []
    for i, s in enumerate(sites[:20]):
        if i > 0:
            children.append(ui.Divider())
        children.append(_site_row(s))
    return ui.Stack(direction="v", gap=2, children=children)


def _connect_section() -> ui.UINode:
    """Plain content, no Card wrapper. Stretched full-width per
    UI_INTERFACE_STANDARD.md (2026-08-20). No intro heading/description
    text here -- the Site Token walkthrough lives ONLY in
    webflow_connect_help's panel (button below opens it)."""
    return ui.Stack(direction="v", gap=3, align="stretch", children=[
        ui.Button("How do I get a Site Token?", variant="ghost", size="sm",
                  icon="HelpCircle",
                  on_click=ui.Call("__panel__webflow_connect_help")),
        ui.Button("Authorize Webflow (OAuth 2.0)", variant="primary", size="sm", icon="login"),
        ui.Divider(),
        ui.Text("Or connect via Site / Workspace Token", variant="caption"),
        ui.Form(
            action="connect_webflow",
            submit_label="Verify and connect",
            children=[
                ui.Stack(direction="v", gap=1, children=[
                    ui.Text("Site Token", variant="caption"),
                    ui.Password(param_name="site_token", placeholder="Site Token"),
                ]),
                ui.Stack(direction="v", gap=1, children=[
                    ui.Text("Label (optional)", variant="caption"),
                    ui.Input(param_name="label", placeholder="e.g. Marketing site"),
                ]),
            ],
        ),
        ui.Divider(),
        ui.Form(
            action="connect_webflow_workspace",
            submit_label="Connect Workspace Token (read-only, all sites)",
            children=[
                ui.Stack(direction="v", gap=1, children=[
                    ui.Text("Workspace Token (optional)", variant="caption"),
                    ui.Password(param_name="workspace_token", placeholder="Workspace Token"),
                ]),
                ui.Stack(direction="v", gap=1, children=[
                    ui.Text("Label (optional)", variant="caption"),
                    ui.Input(param_name="label", placeholder="e.g. All sites (read-only)"),
                ]),
            ],
        ),
    ])


@ext.panel("webflow_connect", slot="left", title="Webflow", icon="🌊",
           default_width=320, min_width=260, max_width=420)
async def webflow_connect_panel(ctx, **kwargs) -> object:
    connections = await h._load_connections(ctx)
    connected = bool(connections)

    header = ui.Header(text="Webflow", level=2,
                        subtitle="Manage your Webflow site(s) from Imperal")

    if not connected:
        return ui.Stack(direction="v", gap=4, align="stretch", children=[
            header,
            _connect_section(),
            ui.Divider(),
            _settings_button(),
        ])

    sites: list = []
    first = connections[0]
    try:
        result = await h.list_sites(ctx, h.ListSitesParams(connection_id=first.get("id", "")))
        if result.ok:
            sites = result.data.items
    except Exception:
        sites = []

    return ui.Stack(direction="v", gap=4, align="stretch", children=[
        header,
        ui.Text("Connected", variant="subtitle"),
        _connections_section(connections),
        ui.Divider(),
        _connect_section(),
        ui.Divider(),
        ui.Text(f"Sites -- {first.get('title', '')}", variant="subtitle"),
        _sites_section(sites),
        ui.Divider(),
        ui.Button("View pages", variant="primary", size="sm", icon="FileText", on_click=ui.Call("__panel__webflow_center")),
        ui.Divider(),
        _settings_button(),
    ])


@ext.panel("webflow_connect_help", slot="center",
           title="How to connect Webflow", center_overlay=True)
async def webflow_connect_help(ctx, **kwargs) -> object:
    content = ui.Stack(direction="v", gap=3, children=[
        ui.Text("1. Open your site in the Webflow Designer or Dashboard."),
        ui.Text("2. Go to Site Settings > Apps & integrations > API access."),
        ui.Text("3. Click \"Generate API token\", pick the scopes you need (or all of them for full functionality), and copy the token -- Webflow shows it only once."),
        ui.Text("4. Paste it into the Site Token field on the left and connect."),
        ui.Divider(),
        ui.Alert(
            title="One token per site",
            message=(
                "A Site Token only reaches the one site it was generated "
                "on. To manage several sites, connect each one with its "
                "own Site Token, or use a read-only Workspace Token to "
                "cover every site in a Webflow Workspace at once."
            ),
            type="info",
        ),
        ui.Divider(),
        ui.Alert(
            title="Custom Code is out of scope",
            message=(
                "Registering or applying Custom Code (scripts) requires "
                "Webflow's own OAuth Data Client App flow and cannot be "
                "done with a Site Token -- this is a Webflow platform "
                "limit, not something this connector chose to skip."
            ),
            type="warning",
        ),
        ui.Divider(),
        ui.Link(
            label="Open Webflow's official API access guide",
            href="https://developers.webflow.com/data/reference/authentication",
        ),
    ])
    return ui.Dialog(
        title="How to connect Webflow",
        content=content,
        confirm_label="",
        cancel_label="Close",
    )


def _page_row(p) -> dict:
    return {
        "title": p.title or p.slug or p.id, "slug": p.slug or "—",
        "status": "Draft" if p.is_draft else ("Archived" if p.is_archived else "Live"),
        "last_updated": (p.last_updated or "")[:10] or "—",
        "page_id": p.id,
    }


@ext.panel("webflow_center", slot="center", title="Webflow", icon="🌊", center_overlay=True)
async def webflow_center_panel(ctx, page_id: str = "", **kwargs) -> object:
    """Post-connect main screen: the connected site's pages, or a page
    detail when `page_id` is passed (master-detail via the same panel_id,
    per UI_COMPONENT_VOCABULARY.md §3)."""
    connections = await h._load_connections(ctx)
    if not connections:
        return ui.Empty(
            message="Connect a Webflow site from the sidebar to see its pages here.",
            icon="🌊",
        )
    if page_id:
        return await _page_detail(ctx, page_id, connections[0].get("id", ""))
    return await _pages_dashboard(ctx, connections[0])


async def _pages_dashboard(ctx, conn: dict) -> ui.UINode:
    sites: list = []
    try:
        result = await h.list_sites(ctx, h.ListSitesParams(connection_id=conn.get("id", "")))
        if result.ok:
            sites = result.data.items
    except Exception:
        sites = []
    if not sites:
        return ui.Empty(message="No sites found on this connection.", icon="🌊")

    site = sites[0]
    pages: list = []
    try:
        result = await h.list_pages(ctx, h.ListPagesParams(connection_id=conn.get("id", ""), site_id=site.id))
        if result.ok:
            pages = result.data.items
    except Exception:
        pages = []

    body: list[ui.UINode] = [
        ui.Stats(children=[
            ui.Stat(label="Total pages", value=str(len(pages))),
            ui.Stat(label="Drafts", value=str(sum(1 for p in pages if p.is_draft))),
        ]),
        ui.Divider(),
        ui.Stack(direction="h", gap=2, align="center", children=[
            ui.Text(f"Pages — {site.display_name or site.short_name}", variant="subtitle"),
            ui.Button("Publish site", variant="primary", size="sm", icon="Upload",
                      on_click=ui.Call("publish_site", connection_id=conn.get("id", ""), site_id=site.id)),
        ]),
    ]
    if pages:
        columns = [
            ui.DataColumn("title", "Title", sortable=True),
            ui.DataColumn("slug", "Slug", sortable=False),
            ui.DataColumn("status", "Status", sortable=True),
            ui.DataColumn("last_updated", "Last updated", sortable=True),
        ]
        body.append(ui.DataTable(
            columns=columns,
            rows=[_page_row(p) for p in pages],
            on_row_click=ui.Call("__panel__webflow_center", page_id=""),
        ))
    else:
        body.append(ui.Text("No pages found on this site.", variant="caption"))
    return ui.Stack(direction="v", gap=4, align="stretch", children=body)


async def _page_detail(ctx, page_id: str, connection_id: str) -> ui.UINode:
    result = await h.get_page(ctx, h.GetPageParams(connection_id=connection_id, page_id=page_id))
    if not result.ok or not result.data:
        return ui.Stack(direction="v", gap=3, align="stretch", children=[
            ui.Button("← Back to pages", variant="ghost", size="sm",
                      on_click=ui.Call("__panel__webflow_center")),
            ui.Alert(title="Could not load this page", message=result.error or "Unknown error.", type="error"),
        ])
    p = result.data
    return ui.Stack(direction="v", gap=3, align="stretch", children=[
        ui.Button("← Back to pages", variant="ghost", size="sm",
                  on_click=ui.Call("__panel__webflow_center")),
        ui.Header(text=p.title or p.slug, level=3,
                  subtitle="Draft" if p.is_draft else ("Archived" if p.is_archived else "Live")),
        ui.KeyValue(columns=2, items=[
            {"key": "Slug", "value": p.slug or "—"},
            {"key": "SEO title", "value": p.seo_title or "—"},
            {"key": "SEO description", "value": p.seo_description or "—"},
            {"key": "Last updated", "value": (p.last_updated or "")[:10] or "—"},
            {"key": "Last published", "value": (p.last_published or "")[:10] or "—"},
        ]),
    ])
