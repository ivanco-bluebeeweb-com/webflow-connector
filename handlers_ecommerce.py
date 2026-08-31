"""Chat functions for Webflow Connector -- Ecommerce domain (Products,
SKUs, Orders, Inventory). Only meaningful on sites with Webflow Ecommerce
enabled."""
from __future__ import annotations

from imperal_sdk import ActionResult

import webflow_ecommerce_client as wec
from app import chat
from handlers import _resolve_connection
from schemas_ecommerce import (
    ListProductsParams, WebflowProduct, WebflowProductList, WebflowSku,
    GetProductParams, CreateProductParams, UpdateProductParams,
    UpdateSkuParams, DeleteProductParams, DeleteResult,
    GetInventoryParams, WebflowInventory, UpdateInventoryParams,
    ListOrdersParams, WebflowOrder, WebflowOrderList, GetOrderParams,
    UpdateOrderParams, FulfillOrderParams, UnfulfillOrderParams,
    RefundOrderParams, OrderActionResult,
)


def _to_sku(s: dict) -> WebflowSku:
    fd = s.get("fieldData", {}) or {}
    price = fd.get("price", {}) or {}
    return WebflowSku(
        id=s.get("id", ""), sku_values=fd.get("sku-values", {}) or {},
        price_amount=int(price.get("value", 0) or 0), price_currency=price.get("unit", ""),
        sku_name=fd.get("name", ""),
    )


def _to_product(p: dict) -> WebflowProduct:
    prod = p.get("product", p)
    fd = prod.get("fieldData", {}) or {}
    skus = [_to_sku(s) for s in p.get("skus", [])] if "skus" in p else []
    return WebflowProduct(
        id=prod.get("id", ""), site_id=prod.get("siteId", ""), name=fd.get("name", ""),
        slug=fd.get("slug", ""), description=fd.get("description", "") or "",
        is_visible=bool(prod.get("isVisible", True)), skus=skus,
    )


def _to_order(o: dict) -> WebflowOrder:
    totals = o.get("orderTotals", {}) or {}
    return WebflowOrder(
        id=o.get("orderId", o.get("id", "")), site_id=o.get("siteId", "") or "",
        status=o.get("status", ""), customer_email=(o.get("customerInfo") or {}).get("email", ""),
        order_total_amount=int(totals.get("total", 0) or 0), order_total_currency=totals.get("currency", ""),
        created_on=o.get("acceptedOn", "") or o.get("createdOn", ""),
        fulfilled_on=o.get("fulfilledOn", "") or "",
    )


# ──────────────────────────────────────────────────────────────────────────
# Products / SKUs
# ──────────────────────────────────────────────────────────────────────────


@chat.function(
    "list_products",
    "List Ecommerce products (with their SKUs/variants) on a Webflow site. Only meaningful on sites with Webflow Ecommerce enabled.",
    action_type="read", chain_callable=True, data_model=WebflowProductList,
    event="webflow-connector.list_products",
)
async def list_products(ctx, params: ListProductsParams) -> ActionResult:
    conn = await _resolve_connection(ctx, params.connection_id)
    if not conn:
        return ActionResult.error("No Webflow site connected. Use connect_webflow first.", code="WEBFLOW_NOT_CONNECTED")
    body = await wec.list_products(ctx, conn["token"], params.site_id, params.limit, params.offset)
    items = body.get("items", []) if isinstance(body, dict) else []
    return ActionResult.success(WebflowProductList(items=[_to_product(p) for p in items])), summary="Products listed."


@chat.function(
    "get_product",
    "Read one Ecommerce product in full, including its SKUs and prices.",
    action_type="read", chain_callable=True, data_model=WebflowProduct,
    event="webflow-connector.get_product",
)
async def get_product(ctx, params: GetProductParams) -> ActionResult:
    conn = await _resolve_connection(ctx, params.connection_id)
    if not conn:
        return ActionResult.error("No Webflow site connected. Use connect_webflow first.", code="WEBFLOW_NOT_CONNECTED")
    p = await wec.get_product(ctx, conn["token"], params.product_id)
    return ActionResult.success(_to_product(p)), summary="Product retrieved."


@chat.function(
    "create_product",
    "Create a new Ecommerce product with its default SKU. Created in staging by default -- publish the site to make it live.",
    action_type="write", chain_callable=True, data_model=WebflowProduct,
    event="webflow-connector.create_product",
    effects=["webflow.product.created"],
)
async def create_product(ctx, params: CreateProductParams) -> ActionResult:
    conn = await _resolve_connection(ctx, params.connection_id)
    if not conn:
        return ActionResult.error("No Webflow site connected. Use connect_webflow first.", code="WEBFLOW_NOT_CONNECTED")
    p = await wec.create_product(
        ctx, conn["token"], params.site_id, params.name, params.description,
        params.price_amount, params.price_currency, params.sku_name, params.is_visible,
    )
    return ActionResult.success(_to_product(p)), summary="Product created."


@chat.function(
    "update_product",
    "Update an Ecommerce product's name, description and/or visibility.",
    action_type="write", chain_callable=True, data_model=WebflowProduct,
    event="webflow-connector.update_product",
    effects=["webflow.product.updated"],
)
async def update_product(ctx, params: UpdateProductParams) -> ActionResult:
    conn = await _resolve_connection(ctx, params.connection_id)
    if not conn:
        return ActionResult.error("No Webflow site connected. Use connect_webflow first.", code="WEBFLOW_NOT_CONNECTED")
    # product_id alone doesn't carry site_id -- read the product first to recover it.
    existing = await wec.get_product(ctx, conn["token"], params.product_id)
    site_id = existing.get("product", existing).get("siteId", "")
    p = await wec.update_product(ctx, conn["token"], site_id, params.product_id, params.name, params.description, params.is_visible)
    return ActionResult.success(_to_product(p)), summary="Product updated."


@chat.function(
    "update_sku",
    "Update one SKU/variant's price and/or option values (e.g. color, size) on an Ecommerce product.",
    action_type="write", chain_callable=True, data_model=WebflowProduct,
    event="webflow-connector.update_sku",
    effects=["webflow.sku.updated"],
)
async def update_sku(ctx, params: UpdateSkuParams) -> ActionResult:
    conn = await _resolve_connection(ctx, params.connection_id)
    if not conn:
        return ActionResult.error("No Webflow site connected. Use connect_webflow first.", code="WEBFLOW_NOT_CONNECTED")
    existing = await wec.get_product(ctx, conn["token"], params.product_id)
    site_id = existing.get("product", existing).get("siteId", "")
    p = await wec.update_sku(ctx, conn["token"], site_id, params.product_id, params.sku_id, params.price_amount, params.sku_values)
    return ActionResult.success(_to_product(p)), summary="Sku updated."


@chat.function(
    "delete_product",
    "Permanently delete an Ecommerce product and its SKUs. Cannot be undone.",
    action_type="write", chain_callable=True, data_model=DeleteResult,
    event="webflow-connector.delete_product",
    effects=["webflow.product.deleted"],
)
async def delete_product(ctx, params: DeleteProductParams) -> ActionResult:
    conn = await _resolve_connection(ctx, params.connection_id)
    if not conn:
        return ActionResult.error("No Webflow site connected. Use connect_webflow first.", code="WEBFLOW_NOT_CONNECTED")
    existing = await wec.get_product(ctx, conn["token"], params.product_id)
    site_id = existing.get("product", existing).get("siteId", "")
    await wec.delete_product(ctx, conn["token"], site_id, params.product_id)
    return ActionResult.success(DeleteResult(id=params.product_id, deleted=True)), summary="Product deleted."


# ──────────────────────────────────────────────────────────────────────────
# Inventory
# ──────────────────────────────────────────────────────────────────────────


@chat.function(
    "get_inventory",
    "Read one SKU's current stock level and inventory type (finite/infinite).",
    action_type="read", chain_callable=True, data_model=WebflowInventory,
    event="webflow-connector.get_inventory",
)
async def get_inventory(ctx, params: GetInventoryParams) -> ActionResult:
    conn = await _resolve_connection(ctx, params.connection_id)
    if not conn:
        return ActionResult.error("No Webflow site connected. Use connect_webflow first.", code="WEBFLOW_NOT_CONNECTED")
    body = await wec.get_inventory(ctx, conn["token"], params.site_id, params.sku_id)
    return ActionResult.success(WebflowInventory(
        sku_id=params.sku_id, quantity=int(body.get("quantity", 0) or 0),
        inventory_type=body.get("inventoryType", ""),
    )), summary="Inventory retrieved."


@chat.function(
    "update_inventory",
    "Set a SKU's stock quantity and/or inventory type (finite vs infinite).",
    action_type="write", chain_callable=True, data_model=WebflowInventory,
    event="webflow-connector.update_inventory",
    effects=["webflow.inventory.updated"],
)
async def update_inventory(ctx, params: UpdateInventoryParams) -> ActionResult:
    conn = await _resolve_connection(ctx, params.connection_id)
    if not conn:
        return ActionResult.error("No Webflow site connected. Use connect_webflow first.", code="WEBFLOW_NOT_CONNECTED")
    await wec.update_inventory(ctx, conn["token"], params.site_id, params.sku_id, params.quantity, params.inventory_type)
    return ActionResult.success(WebflowInventory(sku_id=params.sku_id, quantity=params.quantity, inventory_type=params.inventory_type)), summary="Inventory updated."


# ──────────────────────────────────────────────────────────────────────────
# Orders
# ──────────────────────────────────────────────────────────────────────────


@chat.function(
    "list_orders",
    "List Ecommerce orders on a Webflow site, optionally filtered by status.",
    action_type="read", chain_callable=True, data_model=WebflowOrderList,
    event="webflow-connector.list_orders",
)
async def list_orders(ctx, params: ListOrdersParams) -> ActionResult:
    conn = await _resolve_connection(ctx, params.connection_id)
    if not conn:
        return ActionResult.error("No Webflow site connected. Use connect_webflow first.", code="WEBFLOW_NOT_CONNECTED")
    body = await wec.list_orders(ctx, conn["token"], params.site_id, params.status, params.limit, params.offset)
    items = body.get("orders", []) if isinstance(body, dict) else []
    return ActionResult.success(WebflowOrderList(items=[_to_order(o) for o in items])), summary="Orders listed."


@chat.function(
    "get_order",
    "Read one Ecommerce order in full -- status, customer, totals, shipping.",
    action_type="read", chain_callable=True, data_model=WebflowOrder,
    event="webflow-connector.get_order",
)
async def get_order(ctx, params: GetOrderParams) -> ActionResult:
    conn = await _resolve_connection(ctx, params.connection_id)
    if not conn:
        return ActionResult.error("No Webflow site connected. Use connect_webflow first.", code="WEBFLOW_NOT_CONNECTED")
    conns_site = await _resolve_connection(ctx, params.connection_id)
    site_id = conns_site.get("site_id", "") if isinstance(conns_site, dict) else ""
    o = await wec.get_order(ctx, conn["token"], site_id, params.order_id)
    return ActionResult.success(_to_order(o)), summary="Order retrieved."


@chat.function(
    "update_order",
    "Set shipping/tracking details on an existing Ecommerce order.",
    action_type="write", chain_callable=True, data_model=WebflowOrder,
    event="webflow-connector.update_order",
    effects=["webflow.order.updated"],
)
async def update_order(ctx, params: UpdateOrderParams) -> ActionResult:
    conn = await _resolve_connection(ctx, params.connection_id)
    if not conn:
        return ActionResult.error("No Webflow site connected. Use connect_webflow first.", code="WEBFLOW_NOT_CONNECTED")
    site_id = conn.get("site_id", "")
    o = await wec.update_order(ctx, conn["token"], site_id, params.order_id, params.shipping_provider, params.shipping_tracking, params.shipping_tracking_url)
    return ActionResult.success(_to_order(o)), summary="Order updated."


@chat.function(
    "fulfill_order",
    "Mark an Ecommerce order as fulfilled (shipped), optionally emailing the customer.",
    action_type="write", chain_callable=True, data_model=OrderActionResult,
    event="webflow-connector.fulfill_order",
    effects=["webflow.order.fulfilled"],
)
async def fulfill_order(ctx, params: FulfillOrderParams) -> ActionResult:
    conn = await _resolve_connection(ctx, params.connection_id)
    if not conn:
        return ActionResult.error("No Webflow site connected. Use connect_webflow first.", code="WEBFLOW_NOT_CONNECTED")
    site_id = conn.get("site_id", "")
    await wec.fulfill_order(ctx, conn["token"], site_id, params.order_id, params.send_customer_notification)
    return ActionResult.success(OrderActionResult(order_id=params.order_id, status="fulfilled", title="Order marked fulfilled")), summary="Fulfill order done."


@chat.function(
    "unfulfill_order",
    "Revert an Ecommerce order back to unfulfilled.",
    action_type="write", chain_callable=True, data_model=OrderActionResult,
    event="webflow-connector.unfulfill_order",
    effects=["webflow.order.unfulfilled"],
)
async def unfulfill_order(ctx, params: UnfulfillOrderParams) -> ActionResult:
    conn = await _resolve_connection(ctx, params.connection_id)
    if not conn:
        return ActionResult.error("No Webflow site connected. Use connect_webflow first.", code="WEBFLOW_NOT_CONNECTED")
    site_id = conn.get("site_id", "")
    await wec.unfulfill_order(ctx, conn["token"], site_id, params.order_id)
    return ActionResult.success(OrderActionResult(order_id=params.order_id, status="unfulfilled", title="Order marked unfulfilled")), summary="Unfulfill order done."


@chat.function(
    "refund_order",
    "Refund an Ecommerce order through Webflow's own payment processor. Cannot be undone.",
    action_type="write", chain_callable=True, data_model=OrderActionResult,
    event="webflow-connector.refund_order",
    effects=["webflow.order.refunded"],
)
async def refund_order(ctx, params: RefundOrderParams) -> ActionResult:
    conn = await _resolve_connection(ctx, params.connection_id)
    if not conn:
        return ActionResult.error("No Webflow site connected. Use connect_webflow first.", code="WEBFLOW_NOT_CONNECTED")
    site_id = conn.get("site_id", "")
    await wec.refund_order(ctx, conn["token"], site_id, params.order_id)
    return ActionResult.success(OrderActionResult(order_id=params.order_id, status="refunded", title="Order refunded")), summary="Refund order done."
