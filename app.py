"""Extension declaration, secrets, lifecycle hooks.

WHY BYOK (bring-your-own-key), same reasoning as MuleSoft Connector /
UiPath Connector / Power Automate Connector / n8n Connector. A Webflow
site lives inside the USER'S OWN Webflow account/workspace -- Imperal
cannot and should not broker access to someone else's Webflow site
centrally.

WHY SITE TOKEN (not a full OAuth Data Client App), CONFIRMED DURING
DISCOVERY 2026-08-20 (CONNECTOR_DISCOVERY.md).

Webflow's Data API v2 offers three distinct bearer-token models
(developers.webflow.com/data/reference/authentication):
  - Site Token -- generated directly by a site admin in
    Site Settings > Apps & integrations > API access, no external
    OAuth redirect. Scoped to one site. Best for "internal tools and
    single-site integrations where you control the environment" (exact
    wording from Webflow's own docs) -- precisely this connector's BYOK
    shape, same as a WordPress Application Password.
  - Workspace Token -- read-only across every site in a Workspace. Best
    for monitoring/auditing many sites at once.
  - OAuth Data Client App -- full OAuth 2.0 flow, required for Webflow
    Marketplace apps or multi-tenant/user-specific access; NOT needed
    for a BYOK connector where the user is themselves the site owner.

The connector therefore asks for a Site Token per connected site (the
friendly, zero-approval path), with an optional Workspace Token for
read-only cross-site rollups -- no OAuth redirect required at all.

WHY `custom_code:read`/`custom_code:write` ARE OUT OF SCOPE FOR THIS
CONNECTOR (hard platform limit, not a design choice).

Confirmed verbatim on developers.webflow.com/data/reference/scopes.md
(2026-08-20): "The `custom_code:read` and `custom_code:write` scopes are
available only to Data Client apps. Site tokens cannot access custom
code endpoints." A Site-Token-only connector structurally cannot call
Custom Code endpoints (register/apply/list scripts) -- this is a
Webflow-side restriction, not something Imperal chose to exclude.

WHY `write_mode="both"`, SAME REASONING AS MuleSoft/UiPath/n8n/Make.com/
Power Automate CONNECTOR.

Declaring `write_mode="user"` would mean only the platform's generic
Secrets screen could write these -- leaving a first-time user with no
in-app screen explaining what a Site Token even is or where to create
one. `"both"` keeps the generic Secrets screen as a fallback while
letting `connect_webflow` be the friendly guided path.

WHY SCOPE IS PER-ACCOUNT, NOT APP-LEVEL, SAME AS MuleSoft/UiPath/n8n/
Make.com/Power Automate CONNECTOR.

Each user connects their OWN Webflow site(s) -- these are not
developer-owned app credentials, so the connections secret is declared
per-account (default scope), not `scope="app"`.

WHY ONE SECRET HOLDING A JSON ARRAY, NOT FLAT SECRETS FOR "the" SITE
(multi-site support).

A Webflow account/Workspace can host many sites, each needing its own
Site Token -- same structural problem MuleSoft solved for
multi-environment orgs and UiPath solved for multi-tenant Automation
Cloud accounts. `ctx.secrets` only supports a fixed, manifest-declared
set of NAMES -- there is no "one secret per connection_id" primitive.
This connector follows the same precedent: `webflow_connections` holds
a JSON array of `{id, label, site_token, site_id, site_name}` objects.
`schemas.py`'s `connection_id` parameter on every tool call addresses
one specific entry in that array -- see handlers_core.py's
`_load_connections`/`_save_connections` helpers. `webflow_workspace_token`
is a separate, optional, single-value secret (one Workspace Token is
enough to read every site in a Workspace -- there is no per-site
multiplicity to model there).

SCOPE OF THIS RELEASE (Ярус 1 + 2 + 3, Влад заявил "максимальный
функционал, полный максимум" в первом сообщении 2026-08-20 -- см.
PREPARATION.md/CONNECTOR_DISCOVERY.md):
Sites, Pages, Components (read), CMS Collections + Fields + Items
(staged + live), Assets + Asset Folders, Forms + Submissions, Comments,
Ecommerce (Products/SKUs/Orders/Inventory/Settings), Webhooks, Site
Configuration (301 redirects), plus this connector's own value-add
bulk/audit layer (Ярус 3). Custom Code and Enterprise-only Workspace
Management/Audit Logs are explicitly out of scope for a Site-Token-only
BYOK connector -- see the docstring above and CONNECTOR_DISCOVERY.md §6.
"""
from __future__ import annotations

from imperal_sdk import ChatExtension, Extension

ext = Extension(
    "webflow-connector",
    version="0.1.0",
    display_name="Webflow",
    description=(
        "Connect your own Webflow site(s) via a Site Token to manage them "
        "from Imperal -- publish and edit CMS Collection items, manage "
        "Pages and static/dynamic content, browse and moderate Form "
        "submissions, upload media Assets, read and reply to Comments, "
        "manage Ecommerce products/SKUs/orders/inventory, set up "
        "Webhooks, and configure 301 redirects. Uses your own Webflow "
        "Site Token (or an optional read-only Workspace Token for "
        "cross-site rollups) -- nothing is hosted or proxied by Imperal "
        "beyond the request itself. Note: Custom Code (registering/"
        "applying scripts) requires Webflow's own OAuth Data Client App "
        "flow and is not available to Site Tokens -- out of scope here; "
        "Enterprise-only Workspace Management and Audit Logs are also "
        "out of scope."
    ),
    icon="icon.svg",
    capabilities=[
        "webflow:read",
        "webflow:write",
    ],
    actions_explicit=True,
    system=False,
)

chat = ChatExtension(
    ext,
    tool_name="webflow",
    description=(
        "Webflow Connector -- connect your own Webflow site(s) via a Site "
        "Token, then manage Sites/Pages, CMS Collections and Items, "
        "Assets, Forms and submissions, Comments, Ecommerce, Webhooks, "
        "and 301 redirects."
    ),
)

ext.secret(
    "webflow_connections",
    (
        "Your connected Webflow sites -- stored as a JSON array, one "
        "entry per site, each with its own Site Token (site_token) plus "
        "site_id/site_name. Managed through connect_webflow / "
        "disconnect_webflow -- you should not need to edit this "
        "directly."
    ),
    required=True,
    write_mode="both",
    max_bytes=65536,
    rotation_hint_days=180,
)(lambda: None)

ext.secret(
    "webflow_workspace_token",
    (
        "Optional read-only Workspace Token, giving cross-site access to "
        "every site in one Webflow Workspace (best for monitoring/"
        "auditing many sites at once, instead of connecting each site "
        "individually with its own Site Token). Managed through "
        "connect_webflow_workspace / disconnect_webflow_workspace."
    ),
    required=False,
    write_mode="both",
    max_bytes=4096,
    rotation_hint_days=180,
)(lambda: None)


@ext.health_check
async def health_check(ctx) -> dict:
    """Fast configuration health; no third-party call -- just confirms at
    least one site connection or the workspace token is stored, same
    shape as MuleSoft/UiPath Connector's health_check."""
    import json as _json
    raw = await ctx.secrets.get("webflow_connections")
    try:
        count = len(_json.loads(raw)) if raw else 0
    except Exception:
        count = 0
    ws_token = await ctx.secrets.get("webflow_workspace_token")
    detail_bits = []
    if count:
        detail_bits.append(f"{count} Webflow site(s) connected")
    if ws_token:
        detail_bits.append("Workspace Token set")
    return {
        "healthy": True,
        "detail": (
            ", ".join(detail_bits) + "."
            if detail_bits
            else "Not connected yet -- run connect_webflow."
        ),
    }
