import frappe


def handover_query(user=None):
    user = user or frappe.session.user
    if user == "Administrator":
        return ""
    escaped = frappe.db.escape(user)
    return f"(`tabAV Handover`.`owner` = {escaped} OR `tabAV Handover`.`project_manager` = {escaped})"


def handover_permission(doc, user=None, permission_type=None):
    """Deny-only hook: Frappe treats any falsy result (including None) as a denial.

    Returning True never grants access; standard DocType role permissions are still
    evaluated afterwards (frappe.permissions.has_controller_permissions).
    """
    user = user or frappe.session.user
    if user == "Administrator":
        return True
    if doc.is_new():
        return True  # Standard DocType role permissions still apply.
    return user in (doc.owner, doc.project_manager)
