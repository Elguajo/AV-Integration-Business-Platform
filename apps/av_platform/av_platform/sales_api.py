"""Read models and actions for the Sales workspace (/av/sales).

The workspace only displays data and calls Frappe. Every decision (permissions, states,
whether a handover is allowed) is taken here or in the AV Handover controller.
Blockers are returned as stable codes; the frontend owns the human-readable texts (ARC-03).
"""

import frappe
from frappe.utils import flt

from av_platform.versions import current_versions, version_filters

SALES_ROLE = "AV Sales"
PM_ROLE = "AV Project Manager"

QUOTATION_FIELDS = [
    "name", "title", "party_name", "customer_name", "company", "status", "docstatus", "grand_total",
    "currency", "transaction_date", "valid_till", "owner", "creation", "modified",
]
HANDOVER_FIELDS = [
    "name", "quotation", "review_status", "docstatus", "project", "project_manager",
    "reviewed_on", "review_note", "accepted_value", "currency", "creation",
]


def _require_sales():
    if SALES_ROLE not in frappe.get_roles():
        frappe.throw("The AV Sales role is required.", frappe.PermissionError)


def _stage(quote, handover, hidden_handover, superseded=False):
    if quote.docstatus == 0:
        return "draft"
    if quote.docstatus == 2:
        return "cancelled"
    if hidden_handover:
        return "handover_unknown"
    if not handover:
        return "superseded" if superseded else "issued"
    if handover.docstatus == 0:
        return "handover_draft"
    return {"Pending": "handover_pending", "Accepted": "accepted", "Returned": "returned"}.get(
        handover.review_status, "handover_unknown"
    )


def _visible_handovers(quotation_names):
    if not quotation_names:
        return {}
    rows = frappe.get_list(
        "AV Handover", fields=HANDOVER_FIELDS,
        filters={"quotation": ["in", quotation_names], "docstatus": ["!=", 2]},
        limit_page_length=0,
    )
    return {row.quotation: row for row in rows}


def _existing_handover_quotations(quotation_names):
    # Existence only: the user may read the quotation, so knowing it is already
    # handed over is not new information. Details stay behind AV Handover permissions.
    if not quotation_names:
        return set()
    return set(frappe.get_all(
        "AV Handover", filters={"quotation": ["in", quotation_names], "docstatus": ["!=", 2]},
        pluck="quotation",
    ))


def _with_stages(quotes):
    names = [q.name for q in quotes]
    visible = _visible_handovers(names)
    existing = _existing_handover_quotations(names)
    current = current_versions([(q.party_name, q.company) for q in quotes])
    rows = []
    for quote in quotes:
        handover = visible.get(quote.name)
        hidden = quote.name in existing and not handover
        superseded = current.get((quote.party_name, quote.company)) != quote.name
        rows.append({
            **quote,
            "stage": _stage(quote, handover, hidden, superseded),
            "handover": handover,
        })
    return rows


def _user_label(user):
    return frappe.db.get_value("User", user, "full_name") or user


@frappe.whitelist(methods=["GET"])
def get_workspace():
    _require_sales()
    quotes = frappe.get_list(
        "Quotation", fields=QUOTATION_FIELDS,
        filters={"quotation_to": "Customer", "docstatus": ["!=", 2]},
        order_by="modified desc", limit_page_length=200,
    )
    return {
        "user": {"name": frappe.session.user, "full_name": _user_label(frappe.session.user)},
        "quotations": _with_stages(quotes),
    }


def _versions(quote, current):
    rows = frappe.get_list(
        "Quotation", fields=["name", "title", "docstatus", "status", "grand_total", "currency",
                             "transaction_date", "creation"],
        filters={**version_filters(quote.party_name, quote.company), "docstatus": ["!=", 2]},
        order_by="creation asc", limit_page_length=50,
    )
    return [{**row, "version": index + 1, "is_current": row.name == current}
            for index, row in enumerate(rows)]


def _blockers(quote, handover_exists, current):
    blockers = []
    if quote.docstatus != 1:
        blockers.append("not_submitted")
    elif current != quote.name:
        blockers.append("not_current_version")
    if quote.quotation_to != "Customer" or not quote.party_name:
        blockers.append("not_customer")
    if not any(not row.is_alternative for row in quote.items):
        blockers.append("no_main_items")
    if handover_exists:
        blockers.append("handover_exists")
    if not frappe.has_permission("AV Handover", "create") or not frappe.has_permission(
        "AV Handover", "submit"
    ):
        blockers.append("no_permission")
    return blockers


def _pm_options():
    users = frappe.get_all(
        "Has Role", filters={"role": PM_ROLE, "parenttype": "User"}, pluck="parent"
    )
    if not users:
        return []
    return frappe.get_all(
        "User", filters={"name": ["in", users], "enabled": 1, "user_type": "System User"},
        fields=["name", "full_name"], order_by="full_name asc",
    )


@frappe.whitelist(methods=["GET"])
def get_quotation(name: str):
    _require_sales()
    quote = frappe.get_doc("Quotation", name)
    quote.check_permission("read")
    items = [{
        "idx": row.idx, "item_code": row.item_code, "item_name": row.item_name,
        "qty": flt(row.qty), "uom": row.uom, "rate": flt(row.rate), "amount": flt(row.amount),
        "is_alternative": bool(row.is_alternative),
    } for row in quote.items]
    main = [row for row in items if not row["is_alternative"]]
    visible = _visible_handovers([quote.name]).get(quote.name)
    exists = bool(visible) or bool(_existing_handover_quotations([quote.name]))
    if visible:
        visible["project_manager_name"] = _user_label(visible.project_manager)
    current = current_versions([(quote.party_name, quote.company)]).get(
        (quote.party_name, quote.company)
    )
    blockers = _blockers(quote, exists, current)
    return {
        "quotation": {
            "name": quote.name, "title": quote.title, "party_name": quote.party_name,
            "customer_name": quote.customer_name, "status": quote.status,
            "docstatus": quote.docstatus, "currency": quote.currency,
            "transaction_date": quote.transaction_date, "valid_till": quote.valid_till,
            "grand_total": flt(quote.grand_total),
            "total_taxes_and_charges": flt(quote.total_taxes_and_charges),
            "terms": quote.terms,
        },
        "stage": _stage(quote, visible, exists and not visible,
                        quote.docstatus == 1 and current != quote.name),
        "main_items": main,
        "alternatives": [row for row in items if row["is_alternative"]],
        "main_total": sum(row["amount"] for row in main),
        "versions": _versions(quote, current),
        "handover": visible,
        "can_handover": not blockers,
        "blockers": blockers,
        "pm_options": _pm_options() if not blockers else [],
    }


@frappe.whitelist(methods=["POST"])
def create_handover(
    quotation: str, project_manager: str, project_name: str,
    customer_approval_reference: str, start_authorization_reference: str | None = None,
):
    """Create and submit the handover as the current user; all checks stay in AV Handover."""
    _require_sales()
    # Insert and submit are one unit: a failed submit must not leave a draft handover behind.
    frappe.db.savepoint("av_create_handover")
    try:
        doc = frappe.get_doc({
            "doctype": "AV Handover", "quotation": quotation, "project_name": project_name,
            "project_manager": project_manager,
            "customer_approval_reference": customer_approval_reference,
            "start_authorization_reference": start_authorization_reference,
        }).insert()
        doc.submit()
    except Exception:
        frappe.db.rollback(save_point="av_create_handover")
        raise
    return {"handover": doc.name, "review_status": doc.review_status,
            "accepted_value": doc.accepted_value, "currency": doc.currency}
