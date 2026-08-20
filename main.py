"""Entrypoint for the web-kernel and CLI tools (imperal validate/build).

Sets up sys.path, purges stale module cache, then imports ext/chat and all
handler modules so their decorators register on the same Extension instance
-- same pattern as MuleSoft Connector's / UiPath Connector's main.py.
"""

import os
import sys

_EXT_DIR = os.path.dirname(os.path.abspath(__file__))
if _EXT_DIR not in sys.path:
    sys.path.insert(0, _EXT_DIR)

_LOCAL = (
    "app",
    "schemas", "schemas_cms", "schemas_assets", "schemas_forms",
    "schemas_ecommerce", "schemas_webhooks", "schemas_site_config",
    "webflow_client", "webflow_cms_client", "webflow_assets_client",
    "webflow_forms_client", "webflow_ecommerce_client",
    "webflow_webhooks_client", "webflow_site_config_client",
    "handlers", "handlers_cms", "handlers_assets", "handlers_forms",
    "handlers_ecommerce", "handlers_webhooks", "handlers_site_config",
    "panels", "panels_settings",
)
for _mod in _LOCAL:
    sys.modules.pop(_mod, None)

from app import ext, chat  # noqa: E402,F401
import handlers  # noqa: E402,F401
import handlers_cms  # noqa: E402,F401
import handlers_assets  # noqa: E402,F401
import handlers_forms  # noqa: E402,F401
import handlers_ecommerce  # noqa: E402,F401
import handlers_webhooks  # noqa: E402,F401
import handlers_site_config  # noqa: E402,F401
import panels  # noqa: E402,F401
import panels_settings  # noqa: E402,F401
