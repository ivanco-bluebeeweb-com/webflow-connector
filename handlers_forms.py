"""Chat functions for Webflow Connector -- Forms domain (native forms +
submissions)."""
from __future__ import annotations

from imperal_sdk import ActionResult

import webflow_forms_client as wfc
from app import chat
from handlers import _resolve_connection
from schemas_forms import (
    ListFormsParams, WebflowForm, WebflowFormList,
    GetFormParams, ListFormSubmissionsParams, WebflowFormSubmission,
    WebflowFormSubmissionList, GetFormSubmissionParams,
    DeleteFormSubmissionParams, DeleteResult,
)


def _to_form(f: dict) -> WebflowForm:
    return WebflowForm(
        id=f.get("id", ""), display_name=f.get("displayName", ""), site_id=f.get("siteId", ""),
        page_id=f.get("pageId", "") or "", created_on=f.get("createdOn", ""),
        last_updated=f.get("lastUpdated", ""), fields=f.get("fields", {}) or {},
    )


def _to_submission(s: dict) -> WebflowFormSubmission:
    return WebflowFormSubmission(
        id=s.get("id", ""), form_id=s.get("formId", ""), site_id=s.get("siteId", ""),
        submitted_on=s.get("dateSubmitted", "") or s.get("submittedOn", ""),
        form_response=s.get("formResponse", {}) or {},
    )


@chat.function(
    "list_forms",
    "List native Webflow forms on a site (built with the Designer's Form Block).",
    action_type="read", chain_callable=True, data_model=WebflowFormList,
    event="webflow-connector.list_forms",
)
async def list_forms(ctx, params: ListFormsParams) -> ActionResult:
    conn = await _resolve_connection(ctx, params.connection_id)
    if not conn:
        return ActionResult.error("No Webflow site connected. Use connect_webflow first.", code="WEBFLOW_NOT_CONNECTED")
    raw = await wfc.list_forms(ctx, conn["token"], params.site_id)
    return ActionResult.success(WebflowFormList(items=[_to_form(f) for f in raw]), summary="Forms listed.")


@chat.function(
    "get_form",
    "Read one Webflow form's field schema in full.",
    action_type="read", chain_callable=True, data_model=WebflowForm,
    event="webflow-connector.get_form",
)
async def get_form(ctx, params: GetFormParams) -> ActionResult:
    conn = await _resolve_connection(ctx, params.connection_id)
    if not conn:
        return ActionResult.error("No Webflow site connected. Use connect_webflow first.", code="WEBFLOW_NOT_CONNECTED")
    f = await wfc.get_form(ctx, conn["token"], params.form_id)
    return ActionResult.success(_to_form(f), summary="Form retrieved.")


@chat.function(
    "list_form_submissions",
    "List submissions received on one Webflow form -- who submitted what, and when.",
    action_type="read", chain_callable=True, data_model=WebflowFormSubmissionList,
    event="webflow-connector.list_form_submissions",
)
async def list_form_submissions(ctx, params: ListFormSubmissionsParams) -> ActionResult:
    conn = await _resolve_connection(ctx, params.connection_id)
    if not conn:
        return ActionResult.error("No Webflow site connected. Use connect_webflow first.", code="WEBFLOW_NOT_CONNECTED")
    body = await wfc.list_form_submissions(ctx, conn["token"], params.form_id, params.limit, params.offset)
    items = body.get("formSubmissions", []) if isinstance(body, dict) else []
    return ActionResult.success(WebflowFormSubmissionList(items=[_to_submission(s) for s in items]), summary="Form submissions listed.")


@chat.function(
    "get_form_submission",
    "Read one form submission in full.",
    action_type="read", chain_callable=True, data_model=WebflowFormSubmission,
    event="webflow-connector.get_form_submission",
)
async def get_form_submission(ctx, params: GetFormSubmissionParams) -> ActionResult:
    conn = await _resolve_connection(ctx, params.connection_id)
    if not conn:
        return ActionResult.error("No Webflow site connected. Use connect_webflow first.", code="WEBFLOW_NOT_CONNECTED")
    s = await wfc.get_form_submission(ctx, conn["token"], params.submission_id)
    return ActionResult.success(_to_submission(s), summary="Form submission retrieved.")


@chat.function(
    "delete_form_submission",
    "Permanently delete a form submission (e.g. spam). Cannot be undone.",
    action_type="write", chain_callable=True, data_model=DeleteResult,
    event="webflow-connector.delete_form_submission",
    effects=["webflow.form_submission.deleted"],
)
async def delete_form_submission(ctx, params: DeleteFormSubmissionParams) -> ActionResult:
    conn = await _resolve_connection(ctx, params.connection_id)
    if not conn:
        return ActionResult.error("No Webflow site connected. Use connect_webflow first.", code="WEBFLOW_NOT_CONNECTED")
    await wfc.delete_form_submission(ctx, conn["token"], params.submission_id)
    return ActionResult.success(DeleteResult(id=params.submission_id), message="Submission deleted.", summary="Form submission deleted.")
