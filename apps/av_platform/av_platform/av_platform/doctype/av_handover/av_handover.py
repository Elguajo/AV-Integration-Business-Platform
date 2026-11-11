import frappe
from frappe.model.document import Document
from frappe.utils import now_datetime

from av_platform.commercial import build_snapshot, serialize_snapshot, snapshot_digest

_REVIEW_CAPABILITY = object()
_REVIEW_FIELDS = ("review_status", "project", "reviewed_by", "reviewed_on", "review_note")


class AVHandover(Document):
    def before_insert(self):
        self.owner = frappe.session.user

    def validate(self):
        if self.is_new() or self.docstatus == 0 or self._action == "submit":
            if self.review_status != "Pending" or any(self.get(f) for f in _REVIEW_FIELDS[1:]):
                frappe.throw("Review fields can only be set by the assigned PM review action.")
            if self.snapshot_json or self.snapshot_sha256:
                frappe.throw("The commercial snapshot is generated on submission, not supplied by a client.")
        if not frappe.db.get_value("User", self.project_manager, "enabled"):
            frappe.throw("Select an enabled project manager.")
        if "AV Project Manager" not in frappe.get_roles(self.project_manager):
            frappe.throw("The assigned user needs the AV Project Manager role.")

    def before_submit(self):
        quote = frappe.get_doc("Quotation", self.quotation, for_update=True)
        quote.check_permission("read")
        try:
            snapshot = build_snapshot(quote.as_dict(), self.customer_approval_reference)
        except ValueError as exc:
            frappe.throw(str(exc))
        self.snapshot_json = serialize_snapshot(snapshot)
        self.snapshot_sha256 = snapshot_digest(self.snapshot_json)
        self.company = quote.company
        self.customer = quote.party_name
        self.currency = quote.currency
        self.accepted_value = quote.grand_total

    def before_update_after_submit(self):
        if self.flags.get("av_review_capability") is not _REVIEW_CAPABILITY:
            frappe.throw("Use the PM review action to update a submitted handover.")
        before = self.get_doc_before_save()
        # Protect the commercial and assignment fields even inside the review operation.
        for field in (
            "quotation", "project_name", "project_manager", "customer_approval_reference",
            "start_authorization_reference", "snapshot_json", "snapshot_sha256",
            "company", "customer", "currency", "accepted_value",
        ):
            if self.get(field) != before.get(field):
                frappe.throw("Submitted commercial data and the PM assignment are immutable.")

    def before_cancel(self):
        frappe.throw("Handover history is retained. Issue a new quotation and handover to correct it.")

    def on_trash(self):
        if self.docstatus != 0:
            frappe.throw("Submitted handover history cannot be deleted.")


@frappe.whitelist(methods=["POST"])
def review_handover(name: str, decision: str, note: str = ""):
    """The source row lock serializes retries and simultaneous PM decisions."""
    if decision not in ("accept", "return"):
        frappe.throw("Choose accept or return.")
    handover = frappe.get_doc("AV Handover", name, for_update=True)
    handover.check_permission("read")
    if frappe.session.user != handover.project_manager:
        frappe.throw("Only the assigned PM can review this handover.", frappe.PermissionError)
    if "AV Project Manager" not in frappe.get_roles():
        frappe.throw("The AV Project Manager role is required.", frappe.PermissionError)
    if handover.docstatus != 1:
        frappe.throw("Submit the handover before review.")
    expected = "Accepted" if decision == "accept" else "Returned"
    if handover.review_status == expected:
        if decision == "accept":
            frappe.get_doc("Project", handover.project).check_permission("read")
        return {"handover": name, "status": expected, "project": handover.project}
    if handover.review_status != "Pending":
        frappe.throw("This handover already has a different decision. Create a corrected version.")
    if snapshot_digest(handover.snapshot_json) != handover.snapshot_sha256:
        frappe.throw("Commercial snapshot checksum mismatch.")
    frappe.db.savepoint("av_handover_review")
    try:
        if decision == "return":
            if not note or not note.strip():
                frappe.throw("Explain what Sales needs to correct.")
        else:
            # No early commit: project and review record share the Frappe transaction.
            project = frappe.get_doc({
                "doctype": "Project", "project_name": handover.project_name,
                "company": handover.company, "customer": handover.customer, "status": "Open",
                "users": [{"user": handover.project_manager}],
            }).insert()  # Standard ERPNext create permission is mandatory.
            handover.project = project.name
        handover.review_status = expected
        handover.reviewed_by = frappe.session.user
        handover.reviewed_on = now_datetime()
        handover.review_note = (note or "").strip()
        handover.flags.av_review_capability = _REVIEW_CAPABILITY
        handover.save(ignore_permissions=True)  # Narrow operation; PM cannot edit the snapshot.
    except Exception:
        frappe.db.rollback(save_point="av_handover_review")
        raise
    return {"handover": name, "status": expected, "project": handover.project}
