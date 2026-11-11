import frappe


def handover_query(user=None):
    user = user or frappe.session.user
    if user == "Administrator":
        return ""
    escaped = frappe.db.escape(user)
    return f"(`tabAV Handover`.`owner` = {escaped} OR `tabAV Handover`.`project_manager` = {escaped})"


def handover_permission(doc, user=None, permission_type=None):
    user = user or frappe.session.user
    if user == "Administrator":
        return None
    if doc.is_new():
        return None  # Standard DocType role permissions still apply.
    if user not in (doc.owner, doc.project_manager):
        return False
    return None
