"""Webflow Data API v2 client functions -- Ecommerce domain (Products,
SKUs, Orders, Inventory). Reuses _headers/_check_status from
webflow_client.py. Only meaningful on sites with Webflow Ecommerce
enabled -- confirmed against developers.webflow.com/data/reference/
ecommerce/* during Discovery 2026-08-20.

WHY FULFILL/UNFULFILL/REFUND ARE SEPARATE ENDPOINTS, NOT ONE GENERIC
STATUS UPDATE. Confirmed against Webflow's own Ecommerce Orders reference:
order status transitions are modelled as dedicated actions
(POST .../fulfill, POST .../unfulfill, POST .../refund) rather than a
free-form PATCH status field, matching how the schemas_ecommerce.py
params are shaped.

WHY INVENTORY IS KEYED BY sku_id, NOT collection_id+item_id. Confirmed:
Webflow's Inventory endpoints (GET/POST .../inventory/{skuId}) address a
SKU directly by its own id -- a SKU already implies which product/
collection it belongs to, so no separate collection_id is needed.
"""
from __future__ import annotations

from webflow_client import _headers, _check_status, _API_BASE  # noqa: F401


# ──────────────────────────────────────────────────────────────────────────
# Products / SKUs
# ──────────────────────────────────────────────────────────────────────────


async def list_products(ctx, token: str, site_id: str, limit: int = 100, offset: int = 0) -> dict:
    resp = await ctx.http.get(f"{_API_BASE}/sites/{site_id}/products", headers=_headers(token), params={"limit": limit, "offset": offset})
    return _check_status(resp, "list products")


async def get_product(ctx, token: str, site_id: str, product_id: str) -> dict:
    resp = await ctx.http.get(f"{_API_BASE}/sites/{site_id}/products/{product_id}", headers=_headers(token))
    return _check_status(resp, "read the product")


async def create_product(ctx, token: str, site_id: str, name: str, description: str, price_amount: int, price_currency: str, sku_name: str, is_visible: bool) -> dict:
    payload = {
        "publishStatus": "staging",
        "product": {
            "fieldData": {"name": name, "description": description, "shippable": True},
            "isVisible": is_visible,
        },
        "sku": {
            "fieldData": {
                "name": sku_name or name,
                "price": {"value": price_amount, "unit": price_currency},
            },
        },
    }
    resp = await ctx.http.post(f"{_API_BASE}/sites/{site_id}/products", headers=_headers(token), json=payload)
    return _check_status(resp, "create the product")


async def update_product(ctx, token: str, site_id: str, product_id: str, name: str, description: str, is_visible: bool | None) -> dict:
    field_data: dict = {}
    if name:
        field_data["name"] = name
    if description:
        field_data["description"] = description
    payload: dict = {"product": {"fieldData": field_data}} if field_data else {"product": {}}
    if is_visible is not None:
        payload["product"]["isVisible"] = is_visible
    resp = await ctx.http.patch(f"{_API_BASE}/sites/{site_id}/products/{product_id}", headers=_headers(token), json=payload)
    return _check_status(resp, "update the product")


async def update_sku(ctx, token: str, site_id: str, product_id: str, sku_id: str, price_amount: int | None, sku_values: dict) -> dict:
    field_data: dict = dict(sku_values or {})
    if price_amount is not None:
        field_data["price"] = {"value": price_amount}
    payload = {"skus": [{"id": sku_id, "fieldData": field_data}]}
    resp = await ctx.http.patch(f"{_API_BASE}/sites/{site_id}/products/{product_id}", headers=_headers(token), json=payload)
    return _check_status(resp, "update the SKU")


async def delete_product(ctx, token: str, site_id: str, product_id: str) -> dict:
    resp = await ctx.http.delete(f"{_API_BASE}/sites/{site_id}/products/{product_id}", headers=_headers(token))
    return _check_status(resp, "delete the product")


# ──────────────────────────────────────────────────────────────────────────
# Inventory
# ──────────────────────────────────────────────────────────────────────────


async def get_inventory(ctx, token: str, site_id: str, sku_id: str) -> dict:
    resp = await ctx.http.get(f"{_API_BASE}/sites/{site_id}/inventory/{sku_id}", headers=_headers(token))
    return _check_status(resp, "read the inventory level")


async def update_inventory(ctx, token: str, site_id: str, sku_id: str, quantity: int, inventory_type: str) -> dict:
    payload = {"inventoryType": inventory_type, "quantity": quantity}
    resp = await ctx.http.patch(f"{_API_BASE}/sites/{site_id}/inventory/{sku_id}", headers=_headers(token), json=payload)
    return _check_status(resp, "update the inventory level")


# ──────────────────────────────────────────────────────────────────────────
# Orders
# ──────────────────────────────────────────────────────────────────────────


async def list_orders(ctx, token: str, site_id: str, status: str, limit: int = 50, offset: int = 0) -> dict:
    params = {"limit": limit, "offset": offset}
    if status:
        params["status"] = status
    resp = await ctx.http.get(f"{_API_BASE}/sites/{site_id}/orders", headers=_headers(token), params=params)
    return _check_status(resp, "list orders")


async def get_order(ctx, token: str, site_id: str, order_id: str) -> dict:
    resp = await ctx.http.get(f"{_API_BASE}/sites/{site_id}/orders/{order_id}", headers=_headers(token))
    return _check_status(resp, "read the order")


async def update_order(ctx, token: str, site_id: str, order_id: str, shipping_provider: str, shipping_tracking: str, shipping_tracking_url: str) -> dict:
    payload: dict = {}
    shipping: dict = {}
    if shipping_provider:
        shipping["shippingProvider"] = shipping_provider
    if shipping_tracking:
        shipping["shippingTracking"] = shipping_tracking
    if shipping_tracking_url:
        shipping["shippingTrackingURL"] = shipping_tracking_url
    if shipping:
        payload["shippingDetails"] = shipping
    resp = await ctx.http.patch(f"{_API_BASE}/sites/{site_id}/orders/{order_id}", headers=_headers(token), json=payload)
    return _check_status(resp, "update the order")


async def fulfill_order(ctx, token: str, site_id: str, order_id: str, send_customer_notification: bool) -> dict:
    resp = await ctx.http.post(
        f"{_API_BASE}/sites/{site_id}/orders/{order_id}/fulfill",
        headers=_headers(token), params={"sendOrderFulfilledEmail": send_customer_notification},
    )
    return _check_status(resp, "fulfill the order")


async def unfulfill_order(ctx, token: str, site_id: str, order_id: str) -> dict:
    resp = await ctx.http.post(f"{_API_BASE}/sites/{site_id}/orders/{order_id}/unfulfill", headers=_headers(token))
    return _check_status(resp, "unfulfill the order")


async def refund_order(ctx, token: str, site_id: str, order_id: str) -> dict:
    resp = await ctx.http.post(f"{_API_BASE}/sites/{site_id}/orders/{order_id}/refund", headers=_headers(token))
    return _check_status(resp, "refund the order")
