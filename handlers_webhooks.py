"""Chat functions for Webflow Connector -- Webhooks + Comments domains."""
from __future__ import annotations

from imperal_sdk import ActionResult

import webflow_webhooks_client as wwc
from app import chat
from handlers import _resolve_connection
from schemas_webhooks import (
    WEBFLOW_TRIGGER_TYPES,
    ListWebhooksParams, WebflowWebhook, WebflowWebhookList,
    GetWebhookParams, CreateWebhookParams, DeleteWebhookParams, DeleteResult,
    ListCommentThreadsParams, WebflowCommentThread, WebflowCommentThreadList,
)


def _to_webhook(w: dict) -> WebflowWebhook:
    return WebflowWebhook(
        id=w.get("id", ""), trigger_type=w.get("triggerType", ""), site_id=w.get("siteId", "") or "",
        workspace_id=w.get("workspaceId", "") or "", url=w.get("url", ""),
        filter=w.get("filter", {}) or {}, created_on=w.get("createdOn", ""),
    )


@chat.function(
    "list_webhooks",
    "List webhooks configured on a Webflow site -- which events push notifications to which URL.",
    action_type="read", chain_callable=True, data_model=WebflowWebhookList,
    event="webflow-connector.list_webhooks",
)
async def list_webhooks(ctx, params: ListWebhooksParams) -> ActionResult:
    conn = await _resolve_connection(ctx, params.connection_id)
    if not conn:
        return ActionResult.error("No Webflow site connected. Use connect_webflow first.", code="WEBFLOW_NOT_CONNECTED")
    raw = await wwc.list_webhooks(ctx, conn["token"], params.site_id)
    return ActionResult.ok(WebflowWebhookList(items=[_to_webhook(w) for w in raw]))


@chat.function(
    "get_webhook",
    "Read one webhook's full configuration.",
    action_type="read", chain_callable=True, data_model=WebflowWebhook,
    event="webflow-connector.get_webhook",
)
async def get_webhook(ctx, params: GetWebhookParams) -> ActionResult:
    conn = await _resolve_connection(ctx, params.connection_id)
    if not conn:
        return ActionResult.error("No Webflow site connected. Use connect_webflow first.", code="WEBFLOW_NOT_CONNECTED")
    w = await wwc.get_webhook(ctx, conn["token"], params.webhook_id)
    return ActionResult.ok(_to_webhook(w))


@chat.function(
    "create_webhook",
    f"Create a webhook on a Webflow site: which event triggers it (one of {', '.join(WEBFLOW_TRIGGER_TYPES)}) and which URL receives the POST payload. Use this so Imperal (or any other system) gets notified in real time on form submissions, new orders, CMS changes, or site publishes -- instead of polling.",
    action_type="write", chain_callable=True, data_model=WebflowWebhook,
    event="webflow-connector.create_webhook",
    effects=["webflow.webhook.created"],
)
async def create_webhook(ctx, params: CreateWebhookParams) -> ActionResult:
    conn = await _resolve_connection(ctx, params.connection_id)
    if not conn:
        return ActionResult.error("No Webflow site connected. Use connect_webflow first.", code="WEBFLOW_NOT_CONNECTED")
    if params.trigger_type not in WEBFLOW_TRIGGER_TYPES:
        return ActionResult.error(f"trigger_type must be one of: {', '.join(WEBFLOW_TRIGGER_TYPES)}.", code="WEBFLOW_INVALID_TRIGGER_TYPE")
    w = await wwc.create_webhook(ctx, conn["token"], params.site_id, params.trigger_type, params.url, params.filter)
    return ActionResult.ok(_to_webhook(w), message=f"Webhook created for '{params.trigger_type}'.")


@chat.function(
    "delete_webhook",
    "Permanently remove a webhook. Cannot be undone.",
    action_type="write", chain_callable=True, data_model=DeleteResult,
    event="webflow-connector.delete_webhook",
    effects=["webflow.webhook.deleted"],
)
async def delete_webhook(ctx, params: DeleteWebhookParams) -> ActionResult:
    conn = await _resolve_connection(ctx, params.connection_id)
    if not conn:
        return ActionResult.error("No Webflow site connected. Use connect_webflow first.", code="WEBFLOW_NOT_CONNECTED")
    await wwc.delete_webhook(ctx, conn["token"], params.webhook_id)
    return ActionResult.ok(DeleteResult(id=params.webhook_id), message="Webhook deleted.")


@chat.function(
    "list_comment_threads",
    "List Webflow Editor comment threads left on a site's pages -- feedback/review notes from collaborators.",
    action_type="read", chain_callable=True, data_model=WebflowCommentThreadList,
    event="webflow-connector.list_comment_threads",
)
async def list_comment_threads(ctx, params: ListCommentThreadsParams) -> ActionResult:
    conn = await _resolve_connection(ctx, params.connection_id)
    if not conn:
        return ActionResult.error("No Webflow site connected. Use connect_webflow first.", code="WEBFLOW_NOT_CONNECTED")
    body = await wwc.list_comment_threads(ctx, conn["token"], params.site_id, params.limit, params.offset)
    threads = body.get("comments", []) if isinstance(body, dict) else []
    items = [
        WebflowCommentThread(
            id=t.get("id", ""), page_id=t.get("pageId", "") or "", resolved=bool(t.get("resolved", False)),
            comment_count=len(t.get("replies", []) or []) + 1, created_on=t.get("createdOn", ""),
        )
        for t in threads
    ]
    return ActionResult.ok(WebflowCommentThreadList(items=items))
