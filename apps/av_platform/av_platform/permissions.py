import frappe


def handover_query(user=None):
    user = user or frappe.session.user
    if user == "Administrator":
        return ""
    escaped = frappe.db.escape(user)
    return f"(`tabAV Handover`.`owner` = {escaped} OR `tabAV Handover`.`project_manager` = {escaped})"


def file_query(user=None):
    """Frappe lists attachments of every document of a role-readable DocType.

    Narrow AV Handover attachments to the handovers the user may read. Frappe joins
    this condition with its own File conditions, so it only ever removes rows.
    """
    user = user or frappe.session.user
    if user == "Administrator":
        return ""
    escaped = frappe.db.escape(user)
    return (
        "ifnull(`tabFile`.`attached_to_doctype`, '') != 'AV Handover' "
        "OR `tabFile`.`attached_to_name` IN (SELECT `name` FROM `tabAV Handover` "
        f"WHERE `owner` = {escaped} OR `project_manager` = {escaped})"
    )


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
