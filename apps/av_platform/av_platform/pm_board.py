"""Project work board (PM-01, MVP-SPEC §11.1 PLAN-02/03/06): setup, stage sync and visibility.

The board shows standard ERPNext Tasks; there are no per-board copies. The column is the
custom field Task.av_stage (a link to AV Work Stage); the ERPNext status follows the stage.
"""

import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields

# Basic stages (proposal H, PLAN-02). They are data (ARC-02); a company may edit labels and order.
DEFAULT_STAGES = (
    ("planned", "Запланировано", 10, "Open"),
    ("ready", "Готово к работе", 20, "Open"),
    ("in_progress", "В работе", 30, "Working"),
    ("review", "На проверке", 40, "Pending Review"),
    ("done", "Завершено", 50, "Completed"),
)

# Roles that see every project on the board. Everyone else sees the projects where they are
# listed in Project.users and the tasks assigned to them.
ALL_PROJECTS_ROLES = {"System Manager", "Projects Manager"}

TASK_FIELDS = {
    "Task": [
        {"fieldname": "av_board_section", "label": "Board", "fieldtype": "Section Break",
         "insert_after": "description", "collapsible": 1},
        {"fieldname": "av_stage", "label": "Board stage", "fieldtype": "Link",
         "options": "AV Work Stage", "insert_after": "av_board_section", "in_standard_filter": 1},
        {"fieldname": "av_block_reason", "label": "Block reason", "fieldtype": "Small Text",
         "insert_after": "av_stage",
         "description": "Filled while the task cannot progress. A blocked task cannot be closed."},
        {"fieldname": "av_column_break", "fieldtype": "Column Break", "insert_after": "av_block_reason"},
        {"fieldname": "av_room", "label": "Room", "fieldtype": "Data", "insert_after": "av_column_break"},
        {"fieldname": "av_system", "label": "System", "fieldtype": "Data", "insert_after": "av_room"},
    ]
}


def ensure_setup():
    """Idempotent: runs after install and after every migrate."""
    create_custom_fields(TASK_FIELDS, update=True)
    for code, label, sequence, status in DEFAULT_STAGES:
        if not frappe.db.exists("AV Work Stage", code):
            frappe.get_doc({
                "doctype": "AV Work Stage", "code": code, "label": label,
                "sequence": sequence, "task_status": status, "enabled": 1,
            }).insert(ignore_permissions=True)


def enabled_stages():
    return frappe.get_all(
        "AV Work Stage", filters={"enabled": 1},
        fields=["name", "label", "sequence", "task_status", "is_closed"],
        order_by="sequence asc, name asc",
    )


def _first_stage_for_status(status):
    for stage in enabled_stages():
        if stage.task_status == status:
            return stage.name
    return None


def sync_task_stage(doc, method=None):
    """Task.before_validate: keep the board stage and the ERPNext status consistent.

    Runs before the ERPNext controller validation, so ERPNext still enforces its own rules
    (for example, completed dependencies) on the status that the stage sets.
    """
    if doc.is_template or doc.status == "Template":
        return
    before = doc.get_doc_before_save()
    stage_changed = doc.av_stage and (before is None or before.av_stage != doc.av_stage)
    if stage_changed:
        status = frappe.db.get_value("AV Work Stage", doc.av_stage, "task_status")
        if status and doc.status != "Cancelled":
            doc.status = status
        return
    current = frappe.db.get_value("AV Work Stage", doc.av_stage, "task_status") if doc.av_stage else None
    if doc.status == "Cancelled":
        return
    if doc.status == "Overdue":
        # Overdue is set by the ERPNext scheduler and is not a column. When the task is no
        # longer overdue, restore the stage's status instead of letting ERPNext guess one.
        if current and not doc.is_overdue:
            doc.status = current
        return
    # The status changed elsewhere (Desk form, list action, ERPNext automation).
    if current != doc.status:
        doc.av_stage = _first_stage_for_status(doc.status) or doc.av_stage


def sees_all_projects(user=None):
    user = user or frappe.session.user
    return user == "Administrator" or bool(ALL_PROJECTS_ROLES & set(frappe.get_roles(user)))


def member_projects(user=None):
    user = user or frappe.session.user
    return frappe.get_all("Project User", filters={"user": user, "parenttype": "Project"},
                          pluck="parent", distinct=True)


def assigned_tasks(user=None):
    user = user or frappe.session.user
    return frappe.get_all("ToDo", filters={"allocated_to": user, "reference_type": "Task",
                                           "status": ["!=", "Cancelled"]},
                          pluck="reference_name", distinct=True)


def can_see_task(task, user=None):
    """Board visibility on top of the standard Frappe permission checks (never instead of them)."""
    user = user or frappe.session.user
    if sees_all_projects(user):
        return True
    return (task.project and task.project in member_projects(user)) or task.name in assigned_tasks(user)
