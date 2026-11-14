"""Read model and actions for the project work board (/av/board, PM-01).

The board only displays data and asks the server to move a card. Every decision is taken
here or by the ERPNext Task controller. Rejections are returned as stable codes; the
frontend owns the human-readable texts (ARC-03).
"""

import json
from datetime import timedelta

import frappe
from frappe.utils import getdate, today

from av_platform.pm_board import (
    can_see_task,
    enabled_stages,
    member_projects,
    sees_all_projects,
)

BOARD_LIMIT = 500
TASK_FIELDS = [
    "name", "subject", "project", "status", "priority", "av_stage", "av_block_reason",
    "av_room", "av_system", "exp_start_date", "exp_end_date", "is_milestone", "_assign", "modified",
]


def _card(task, user_names):
    assignees = json.loads(task.get("_assign") or "[]")
    end = task.get("exp_end_date")
    return {
        "name": task.name,
        "subject": task.subject,
        "project": task.project,
        "status": task.status,
        "priority": task.priority,
        "stage": task.av_stage,
        "block_reason": (task.av_block_reason or "").strip() or None,
        "room": task.av_room or None,
        "system": task.av_system or None,
        "start": str(task.exp_start_date) if task.exp_start_date else None,
        "end": str(end) if end else None,
        "is_overdue": bool(end) and task.status not in ("Completed", "Cancelled")
        and getdate(end) < getdate(today()),
        "is_milestone": bool(task.is_milestone),
        "assignees": [{"name": a, "full_name": user_names.get(a)} for a in assignees],
        "modified": str(task.modified),
    }


def _user_names(users):
    users = sorted(set(users))
    if not users:
        return {}
    return dict(frappe.get_all("User", filters={"name": ["in", users]},
                               fields=["name", "full_name"], as_list=True))


def _require_task_read():
    if not frappe.has_permission("Task", "read"):
        frappe.throw("Reading project tasks is not permitted.", frappe.PermissionError)


def _visible_projects():
    filters = {"status": ["!=", "Cancelled"]}
    if not sees_all_projects():
        filters["name"] = ["in", member_projects() or [""]]
    return frappe.get_list("Project", filters=filters, fields=["name", "project_name", "status"],
                           order_by="project_name asc", limit_page_length=0)


@frappe.whitelist(methods=["GET"])
def get_board(project: str | None = None):
    _require_task_read()
    projects = _visible_projects()
    project_names = [p.name for p in projects]
    if project and project not in project_names:
        frappe.throw("This project is not available to you.", frappe.PermissionError)

    filters = {"is_template": 0, "status": ["!=", "Cancelled"]}
    or_filters = None
    if project:
        filters["project"] = project
    elif not sees_all_projects():
        assigned = frappe.get_all("ToDo", filters={"allocated_to": frappe.session.user,
                                                   "reference_type": "Task",
                                                   "status": ["!=", "Cancelled"]},
                                  pluck="reference_name")
        or_filters = {"project": ["in", project_names or [""]], "name": ["in", assigned or [""]]}
    tasks = frappe.get_list("Task", filters=filters, or_filters=or_filters, fields=TASK_FIELDS,
                            order_by="modified desc",
                            limit_page_length=BOARD_LIMIT + 1)
    truncated = len(tasks) > BOARD_LIMIT
    tasks = tasks[:BOARD_LIMIT]

    users = [u for t in tasks for u in json.loads(t._assign or "[]")]
    names = _user_names(users + [frappe.session.user])
    return {
        "user": {"name": frappe.session.user, "full_name": names.get(frappe.session.user)},
        "stages": [{"name": s.name, "label": s.label, "is_closed": bool(s.is_closed)}
                   for s in enabled_stages()],
        "projects": [{"name": p.name, "project_name": p.project_name} for p in projects],
        "tasks": [_card(t, names) for t in tasks],
        "truncated": truncated,
        "can_move": bool(frappe.has_permission("Task", "write")),
    }


MY_TASKS_LIMIT = 300
MY_TASK_VIEWS = ("mine", "delegated")


def due_bucket(end, current_day):
    """Group of a work by its due date (PM-02). The server's day decides, not the browser's.

    The week ends on Sunday: on Sunday "this week" holds nothing beyond today.
    """
    if not end:
        return "no_date"
    end = getdate(end)
    if end < current_day:
        return "overdue"
    if end == current_day:
        return "today"
    if end <= current_day + timedelta(days=6 - current_day.weekday()):
        return "week"
    return "later"


@frappe.whitelist(methods=["GET"])
def get_my_tasks(view: str = "mine"):
    """Open works assigned to the user ("mine") or assigned by the user to others ("delegated").

    An assignment is an open ToDo, as in the ERPNext "Assigned To" field. Completed and
    cancelled works are left out; templates never appear. Visibility follows the board.
    """
    _require_task_read()
    if view not in MY_TASK_VIEWS:
        frappe.throw("Unknown task list.", frappe.ValidationError)
    user = frappe.session.user
    todo_filters = {"reference_type": "Task", "status": "Open"}
    if view == "mine":
        todo_filters["allocated_to"] = user
    else:
        todo_filters.update(assigned_by=user, allocated_to=["!=", user])
    names = frappe.get_all("ToDo", filters=todo_filters, pluck="reference_name", distinct=True)

    tasks = frappe.get_list(
        "Task",
        filters={"name": ["in", names or [""]], "is_template": 0,
                 "status": ["not in", ["Completed", "Cancelled", "Template"]]},
        fields=TASK_FIELDS, order_by="modified desc", limit_page_length=MY_TASKS_LIMIT + 1,
    )
    if not sees_all_projects(user):
        members = set(member_projects(user))
        mine = set(names) if view == "mine" else set()
        tasks = [t for t in tasks if (t.project and t.project in members) or t.name in mine]
    truncated = len(tasks) > MY_TASKS_LIMIT
    tasks = tasks[:MY_TASKS_LIMIT]

    current_day = getdate(today())
    tasks.sort(key=lambda t: (str(t.exp_end_date or "9999-12-31"), t.subject or ""))
    users = [u for t in tasks for u in json.loads(t._assign or "[]")]
    user_names = _user_names(users + [user])
    projects = sorted({t.project for t in tasks if t.project})
    project_names = dict(frappe.get_all("Project", filters={"name": ["in", projects or [""]]},
                                        fields=["name", "project_name"], as_list=True))
    return {
        "user": {"name": user, "full_name": user_names.get(user)},
        "view": view,
        "today": str(current_day),
        "stages": [{"name": s.name, "label": s.label, "is_closed": bool(s.is_closed)}
                   for s in enabled_stages()],
        "projects": [{"name": p, "project_name": project_names.get(p, p)} for p in projects],
        "tasks": [{**_card(t, user_names), "bucket": due_bucket(t.exp_end_date, current_day)}
                  for t in tasks],
        "truncated": truncated,
        "can_move": bool(frappe.has_permission("Task", "write")),
    }


def _reject(code, task=None):
    card = _card(task, _user_names(json.loads(task._assign or "[]"))) if task else None
    return {"ok": False, "code": code, "task": card}


def _open_dependencies(task):
    deps = [row.task for row in task.depends_on]
    if not deps:
        return []
    return frappe.get_all("Task", filters={"name": ["in", deps],
                                           "status": ["not in", ["Completed", "Cancelled"]]},
                          pluck="name")


@frappe.whitelist(methods=["POST"])
def move_task(task: str, stage: str, expected_modified: str):
    """Move a card. The row lock serializes simultaneous moves of the same task."""
    _require_task_read()
    if not frappe.db.exists("Task", task):
        frappe.throw("This task is not available to you.", frappe.PermissionError)
    doc = frappe.get_doc("Task", task, for_update=True)
    # Same answer for a hidden and a missing task: do not reveal which one it is.
    if not doc.has_permission("read") or not can_see_task(doc):
        frappe.throw("This task is not available to you.", frappe.PermissionError)
    if not doc.has_permission("write"):
        return _reject("no_permission", doc)

    target = frappe.db.get_value("AV Work Stage", stage, ["name", "enabled", "is_closed"], as_dict=True)
    if not target or not target.enabled:
        return _reject("unknown_stage", doc)
    if doc.is_template or doc.status in ("Cancelled", "Template"):
        return _reject("task_closed", doc)
    if doc.av_stage == target.name:
        return {"ok": True, "task": _card(doc, _user_names(json.loads(doc._assign or "[]")))}
    if str(doc.modified) != expected_modified:
        return _reject("conflict", doc)
    if target.is_closed:
        if (doc.av_block_reason or "").strip():
            return _reject("blocked", doc)
        if _open_dependencies(doc):
            return _reject("dependencies_open", doc)

    doc.av_stage = target.name
    doc.save()
    return {"ok": True, "task": _card(doc, _user_names(json.loads(doc._assign or "[]")))}
