import frappe

from av_platform.pm_board import assigned_tasks, member_projects, sees_all_projects


def handover_query(user=None):
    user = user or frappe.session.user
    if user == "Administrator":
        return ""
    escaped = frappe.db.escape(user)
    return f"(`tabAV Handover`.`owner` = {escaped} OR `tabAV Handover`.`project_manager` = {escaped})"


def file_query(user=None):
    """Frappe lists attachments of every document of a role-readable DocType.

    Narrow attachments of AV Handover, Task and Project to the documents the user may read.
    Frappe joins this condition with its own File conditions, so it only ever removes rows.
    """
    user = user or frappe.session.user
    if user == "Administrator":
        return ""
    escaped = frappe.db.escape(user)
    readable = {
        "AV Handover": ("SELECT `name` FROM `tabAV Handover` "
                        f"WHERE `owner` = {escaped} OR `project_manager` = {escaped}"),
    }
    if not sees_all_projects(user):
        readable["Task"] = f"SELECT `name` FROM `tabTask` WHERE {task_query(user)}"
        readable["Project"] = f"SELECT `name` FROM `tabProject` WHERE {project_query(user)}"
    restricted = ", ".join(frappe.db.escape(doctype) for doctype in readable)
    allowed = " OR ".join(
        f"(`tabFile`.`attached_to_doctype` = {frappe.db.escape(doctype)} "
        f"AND `tabFile`.`attached_to_name` IN ({query}))"
        for doctype, query in readable.items()
    )
    return f"(ifnull(`tabFile`.`attached_to_doctype`, '') NOT IN ({restricted}) OR {allowed})"


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


# Tasks and projects (TP-02, AGENTS.md rule 3). ERPNext lets every Desk user read all projects and
# every Projects User read and change all tasks. These deny-only rules narrow that to participants:
# members of the project (Project.users), the record's author and, for tasks, the assignees.
# System Manager and Projects Manager keep access to everything (pm_board.ALL_PROJECTS_ROLES).

def _member_projects_sql(escaped):
    return ("SELECT `parent` FROM `tabProject User` "
            f"WHERE `parenttype` = 'Project' AND `user` = {escaped}")


def _assigned_tasks_sql(escaped):
    return ("SELECT `reference_name` FROM `tabToDo` WHERE `reference_type` = 'Task' "
            f"AND `status` != 'Cancelled' AND `allocated_to` = {escaped}")


def project_query(user=None):
    user = user or frappe.session.user
    if sees_all_projects(user):
        return ""
    escaped = frappe.db.escape(user)
    return (f"(`tabProject`.`owner` = {escaped} "
            f"OR `tabProject`.`name` IN ({_member_projects_sql(escaped)}))")


def task_query(user=None):
    user = user or frappe.session.user
    if sees_all_projects(user):
        return ""
    escaped = frappe.db.escape(user)
    return (f"(`tabTask`.`owner` = {escaped} "
            f"OR `tabTask`.`project` IN ({_member_projects_sql(escaped)}) "
            f"OR `tabTask`.`name` IN ({_assigned_tasks_sql(escaped)}))")


def project_permission(doc, user=None, permission_type=None):
    """Deny-only. Decided on the stored record, so a request cannot add its sender to Project.users."""
    user = user or frappe.session.user
    if sees_all_projects(user) or doc.is_new():
        return True
    owner = frappe.db.get_value("Project", doc.name, "owner")
    return owner == user or doc.name in member_projects(user)


def task_permission(doc, user=None, permission_type=None):
    """Deny-only. The stored task decides visibility; a new or moved task must go to a member project."""
    user = user or frappe.session.user
    if sees_all_projects(user):
        return True
    members = member_projects(user)
    if not doc.is_new():
        stored = frappe.db.get_value("Task", doc.name, ["owner", "project"], as_dict=True)
        if not stored:
            return False
        visible = (stored.owner == user or (stored.project and stored.project in members)
                   or doc.name in assigned_tasks(user))
        if not visible:
            return False
        if (doc.project or None) == (stored.project or None):
            return True
    return not doc.project or doc.project in members
