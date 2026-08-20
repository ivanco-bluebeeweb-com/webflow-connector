"""Pydantic params models + SDL entity contracts for Webflow Connector's
Ecommerce domain -- Products (with SKUs/variants), Orders, and Inventory.
Only meaningful on sites with Webflow Ecommerce enabled. Confirmed against
developers.webflow.com/data/reference/ecommerce/* during Discovery
2026-08-20.
"""
from __future__ import annotations

from pydantic import BaseModel, Field
from imperal_sdk import sdl

from schemas import DeleteResult  # noqa: F401 -- re-exported for handlers_ecommerce.py


# ──────────────────────────────────────────────────────────────────────────
# Products / SKUs
# ──────────────────────────────────────────────────────────────────────────


class ListProductsParams(BaseModel):
    connection_id: str = Field("", description="Connection id from list_connections. Omit if only one is connected.")
    site_id: str = Field(..., description="Site id from list_sites.")
    limit: int = Field(100, ge=1, le=100, description="Max products to return (1-100).")
    offset: int = Field(0, ge=0, description="Pagination offset.")


class WebflowSku(sdl.Entity):
    id: str
    sku_values: dict = {}
    price_amount: int = 0
    price_currency: str = ""
    sku_name: str = ""


class WebflowProduct(sdl.Entity):
    id: str
    site_id: str = ""
    name: str = ""
    slug: str = ""
    description: str = ""
    is_visible: bool = True
    skus: list[WebflowSku] = []


class WebflowProductList(sdl.Entity):
    title: str = "Products"
    items: list[WebflowProduct] = []


class GetProductParams(BaseModel):
    connection_id: str = Field("", description="Connection id from list_connections. Omit if only one is connected.")
    product_id: str = Field(..., description="Product id from list_products.")


class CreateProductParams(BaseModel):
    connection_id: str = Field("", description="Connection id from list_connections. Omit if only one is connected.")
    site_id: str = Field(..., description="Site id from list_sites.")
    name: str = Field(..., description="Product name.")
    description: str = Field("", description="Product description.")
    price_amount: int = Field(..., description="Price in the site's smallest currency unit (e.g. cents for USD).")
    price_currency: str = Field("USD", description="3-letter ISO currency code.")
    sku_name: str = Field("", description="Name of the default SKU/variant. Defaults to the product name if omitted.")
    is_visible: bool = Field(True, description="Whether the product is visible/purchasable on the live site.")


class UpdateProductParams(BaseModel):
    connection_id: str = Field("", description="Connection id from list_connections. Omit if only one is connected.")
    product_id: str = Field(..., description="Product id from list_products.")
    name: str = Field("", description="New product name. Omit to leave unchanged.")
    description: str = Field("", description="New description. Omit to leave unchanged.")
    is_visible: bool | None = Field(None, description="New visibility. Omit to leave unchanged.")


class UpdateSkuParams(BaseModel):
    connection_id: str = Field("", description="Connection id from list_connections. Omit if only one is connected.")
    product_id: str = Field(..., description="Product id from list_products.")
    sku_id: str = Field(..., description="SKU id from the product's skus list.")
    price_amount: int | None = Field(None, description="New price in the smallest currency unit. Omit to leave unchanged.")
    sku_values: dict = Field(default_factory=dict, description="Variant option values to change (e.g. {'color': 'blue'}). Omit fields to leave unchanged.")


class DeleteProductParams(BaseModel):
    connection_id: str = Field("", description="Connection id from list_connections. Omit if only one is connected.")
    product_id: str = Field(..., description="Product id from list_products.")


# ──────────────────────────────────────────────────────────────────────────
# Inventory
# ──────────────────────────────────────────────────────────────────────────


class GetInventoryParams(BaseModel):
    connection_id: str = Field("", description="Connection id from list_connections. Omit if only one is connected.")
    site_id: str = Field(..., description="Site id from list_sites.")
    sku_id: str = Field(..., description="SKU id to check inventory for.")


class WebflowInventory(sdl.Entity):
    sku_id: str
    quantity: int = 0
    inventory_type: str = ""  # "infinite" | "finite"


class UpdateInventoryParams(BaseModel):
    connection_id: str = Field("", description="Connection id from list_connections. Omit if only one is connected.")
    site_id: str = Field(..., description="Site id from list_sites.")
    sku_id: str = Field(..., description="SKU id to update inventory for.")
    quantity: int = Field(..., description="New stock quantity.")
    inventory_type: str = Field("finite", description="'finite' (tracked quantity) or 'infinite' (never runs out).")


# ──────────────────────────────────────────────────────────────────────────
# Orders
# ──────────────────────────────────────────────────────────────────────────


class ListOrdersParams(BaseModel):
    connection_id: str = Field("", description="Connection id from list_connections. Omit if only one is connected.")
    site_id: str = Field(..., description="Site id from list_sites.")
    status: str = Field("", description="Filter by order status: pending, unfulfilled, fulfilled, disputed, dispute-lost, refunded. Omit for all.")
    limit: int = Field(50, ge=1, le=100, description="Max orders to return (1-100).")
    offset: int = Field(0, ge=0, description="Pagination offset.")


class WebflowOrder(sdl.Entity):
    id: str
    site_id: str = ""
    status: str = ""
    customer_email: str = ""
    order_total_amount: int = 0
    order_total_currency: str = ""
    created_on: str = ""
    fulfilled_on: str = ""


class WebflowOrderList(sdl.Entity):
    title: str = "Orders"
    items: list[WebflowOrder] = []


class GetOrderParams(BaseModel):
    connection_id: str = Field("", description="Connection id from list_connections. Omit if only one is connected.")
    order_id: str = Field(..., description="Order id from list_orders.")


class UpdateOrderParams(BaseModel):
    connection_id: str = Field("", description="Connection id from list_connections. Omit if only one is connected.")
    order_id: str = Field(..., description="Order id from list_orders.")
    shipping_provider: str = Field("", description="Shipping carrier name. Omit to leave unchanged.")
    shipping_tracking: str = Field("", description="Tracking number/URL. Omit to leave unchanged.")
    shipping_tracking_url: str = Field("", description="Tracking page URL. Omit to leave unchanged.")


class FulfillOrderParams(BaseModel):
    connection_id: str = Field("", description="Connection id from list_connections. Omit if only one is connected.")
    order_id: str = Field(..., description="Order id from list_orders.")
    send_customer_notification: bool = Field(True, description="Whether Webflow emails the customer that their order shipped.")


class UnfulfillOrderParams(BaseModel):
    connection_id: str = Field("", description="Connection id from list_connections. Omit if only one is connected.")
    order_id: str = Field(..., description="Order id from list_orders.")


class RefundOrderParams(BaseModel):
    connection_id: str = Field("", description="Connection id from list_connections. Omit if only one is connected.")
    order_id: str = Field(..., description="Order id from list_orders.")


class OrderActionResult(sdl.Entity):
    order_id: str
    status: str = ""
    title: str = "Order updated"
