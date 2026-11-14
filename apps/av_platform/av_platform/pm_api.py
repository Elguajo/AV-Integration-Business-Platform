"""Read model and actions for the project work board (Desk page av-work-board, PM-01).

The board only displays data and asks the server to move a card. Every decision is taken
here or by the ERPNext Task controller. Rejections are returned as stable codes; the
frontend owns the human-readable texts (ARC-03).
"""

import json
from datetime import timedelta

import frappe
from frappe.desk.form import assign_to
from frappe.utils import getdate, today

from av_platform.pm_board import (
    can_see_task,
    enabled_stages,
    member_projects,
    sees_all_projects,
)

BOARD_LIMIT = 500
SUBTASK_LIMIT = 100
SUBJECT_MAX_LENGTH = 140  # Task.subject is a Data field.
SOON_DAYS = 2
CLOSED_STATUSES = ("Completed", "Cancelled")
# Assigning other people is a lead's action; anyone who may change a task may take it (research/07 §3.1).
ASSIGN_OTHERS_ROLES = {"System Manager", "Projects Manager", "AV Project Manager"}
TASK_FIELDS = [
    "name", "subject", "project", "status", "priority", "av_stage", "av_block_reason",
    "av_room", "av_system", "exp_start_date", "exp_end_date", "is_milestone", "_assign", "modified",
]


def due_state(end, status, current_day):
    """Deadline emphasis on a card (BRD-1). The server's day decides, not the browser's."""
    if not end or status in CLOSED_STATUSES:
        return None
    end = getdate(end)
    if end < current_day:
        return "overdue"
    if end == current_day:
        return "today"
    if end <= current_day + timedelta(days=SOON_DAYS):
        return "soon"
    return None


def _comment_counts(names):
    counts = {}
    for name in frappe.get_all("Comment", filters={"reference_doctype": "Task",
                                                   "reference_name": ["in", names],
                                                   "comment_type": "Comment"},
                               pluck="reference_name"):
        counts[name] = counts.get(name, 0) + 1
    return counts


def _subtask_counts(names):
    """Only subtasks the user may read: get_list applies the participation rules (TP-02)."""
    counts = {}
    for row in frappe.get_list("Task", filters={"parent_task": ["in", names], "is_template": 0,
                                                "status": ["!=", "Cancelled"]},
                               fields=["parent_task", "status"], limit_page_length=0):
        done, total = counts.get(row.parent_task, (0, 0))
        counts[row.parent_task] = (done + (row.status == "Completed"), total + 1)
    return counts


def _cards(tasks, user_names=None):
    """Board cards with their counters, read in a few batched queries."""
    if not tasks:
        return []
    names = [t.name for t in tasks]
    if user_names is None:
        user_names = _user_names([u for t in tasks for u in json.loads(t.get("_assign") or "[]")])
    comments = _comment_counts(names)
    subtasks = _subtask_counts(names)
    current_day = getdate(today())
    cards = []
    for task in tasks:
        done, total = subtasks.get(task.name, (0, 0))
        cards.append({
            **_card(task, user_names),
            "due_state": due_state(task.get("exp_end_date"), task.status, current_day),
            "comments": comments.get(task.name, 0),
            "subtasks": {"done": done, "total": total} if total else None,
        })
    return cards


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

    members = _project_members(project_names)
    users = [u for t in tasks for u in json.loads(t._assign or "[]")]
    users += [u for people in members.values() for u in people]
    names = _user_names(users + [frappe.session.user])
    return {
        "user": {"name": frappe.session.user, "full_name": names.get(frappe.session.user)},
        "stages": [{"name": s.name, "label": s.label, "is_closed": bool(s.is_closed)}
                   for s in enabled_stages()],
        "projects": [{"name": p.name, "project_name": p.project_name,
                      "members": [{"name": u, "full_name": names.get(u)} for u in members.get(p.name, [])]}
                     for p in projects],
        "tasks": _cards(tasks, names),
        "truncated": truncated,
        "can_move": bool(frappe.has_permission("Task", "write")),
        "can_assign_others": _can_assign_others(),
    }


def _project_members(projects):
    """Enabled members of the given projects, in table order: the people a work may be assigned to."""
    if not projects:
        return {}
    rows = frappe.get_all("Project User", filters={"parenttype": "Project", "parent": ["in", projects]},
                          fields=["parent", "user"], order_by="idx asc")
    enabled = set(frappe.get_all("User", filters={"name": ["in", [r.user for r in rows] or [""]],
                                                  "enabled": 1}, pluck="name"))
    members = {}
    for row in rows:
        if row.user in enabled and row.user not in members.setdefault(row.parent, []):
            members[row.parent].append(row.user)
    return members


def _can_assign_others(user=None):
    user = user or frappe.session.user
    return user == "Administrator" or bool(ASSIGN_OTHERS_ROLES & set(frappe.get_roles(user)))


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
        "tasks": [{**card, "bucket": due_bucket(t.exp_end_date, current_day)}
                  for t, card in zip(tasks, _cards(tasks, user_names), strict=True)],
        "truncated": truncated,
        "can_move": bool(frappe.has_permission("Task", "write")),
    }


def _fresh_card(task):
    return _cards([task])[0]


def _reject(code, task=None):
    return {"ok": False, "code": code, "task": _fresh_card(task) if task else None}


def _accept(task):
    return {"ok": True, "task": _fresh_card(task)}


def _task_for_action(task, lock=False):
    """The task a card action works on. Hidden and missing tasks get the same answer."""
    _require_task_read()
    if not frappe.db.exists("Task", task):
        frappe.throw("This task is not available to you.", frappe.PermissionError)
    doc = frappe.get_doc("Task", task, for_update=lock)
    if not doc.has_permission("read") or not can_see_task(doc):
        frappe.throw("This task is not available to you.", frappe.PermissionError)
    return doc


def _closed_for_changes(doc):
    return doc.is_template or doc.status in ("Cancelled", "Template")


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
    doc = _task_for_action(task, lock=True)
    if not doc.has_permission("write"):
        return _reject("no_permission", doc)

    target = frappe.db.get_value("AV Work Stage", stage, ["name", "enabled", "is_closed"], as_dict=True)
    if not target or not target.enabled:
        return _reject("unknown_stage", doc)
    if _closed_for_changes(doc):
        return _reject("task_closed", doc)
    if doc.av_stage == target.name:
        return _accept(doc)
    if str(doc.modified) != expected_modified:
        return _reject("conflict", doc)
    if target.is_closed:
        if (doc.av_block_reason or "").strip():
            return _reject("blocked", doc)
        if _open_dependencies(doc):
            return _reject("dependencies_open", doc)

    doc.av_stage = target.name
    doc.save()
    return _accept(doc)


@frappe.whitelist(methods=["POST"])
def rename_task(task: str, subject: str, expected_modified: str):
    """Rename a work from its card (BRD-1). A stale card is refused, never overwritten."""
    doc = _task_for_action(task, lock=True)
    if not doc.has_permission("write"):
        return _reject("no_permission", doc)
    if _closed_for_changes(doc):
        return _reject("task_closed", doc)
    subject = " ".join((subject or "").split())
    if not subject or len(subject) > SUBJECT_MAX_LENGTH:
        return _reject("invalid_subject", doc)
    if doc.subject == subject:
        return _accept(doc)
    if str(doc.modified) != expected_modified:
        return _reject("conflict", doc)
    doc.subject = subject
    doc.save()
    return _accept(doc)


def _assignment_check(doc, user):
    """Rejection code for (un)assigning `user`, or None. Taking a work yourself needs only write access."""
    if not doc.has_permission("write"):
        return "no_permission"
    if user != frappe.session.user and not _can_assign_others():
        return "assign_forbidden"
    if _closed_for_changes(doc):
        return "task_closed"
    return None


@frappe.whitelist(methods=["POST"])
def assign_task(task: str, user: str | None = None):
    """Add an assignee (BRD-1). Without `user` the caller takes the work.

    Assignments are ToDo records and do not change Task.modified, so there is no version check;
    a repeated call keeps the single open assignment.
    """
    doc = _task_for_action(task, lock=True)
    user = user or frappe.session.user
    code = _assignment_check(doc, user)
    if code:
        return _reject(code, doc)
    if user in json.loads(doc._assign or "[]"):
        return _accept(doc)
    # Frappe silently shares the document with an assignee who cannot read it; the board only
    # assigns project members who already may read the work.
    member = (doc.project and frappe.db.get_value("User", user, "enabled")
              and user in _project_members([doc.project]).get(doc.project, []))
    if not member or not frappe.has_permission("Task", "read", doc=doc, user=user):
        return _reject("assignee_not_member", doc)
    assign_to._add({"assign_to": [user], "doctype": "Task", "name": doc.name},
                   ignore_permissions=True)
    doc.reload()
    return _accept(doc)


@frappe.whitelist(methods=["POST"])
def unassign_task(task: str, user: str | None = None):
    """Remove an assignee (BRD-1). Without `user` the caller leaves the work."""
    doc = _task_for_action(task, lock=True)
    user = user or frappe.session.user
    code = _assignment_check(doc, user)
    if code:
        return _reject(code, doc)
    if user in json.loads(doc._assign or "[]"):
        assign_to._remove("Task", doc.name, user, ignore_permissions=True)
        doc.reload()
    return _accept(doc)


@frappe.whitelist(methods=["GET"])
def get_subtasks(task: str):
    """Subtasks of a work that the user may read, for the card's expanded list (BRD-1)."""
    doc = _task_for_action(task)
    rows = frappe.get_list("Task", filters={"parent_task": doc.name, "is_template": 0,
                                            "status": ["!=", "Cancelled"]},
                           fields=TASK_FIELDS, order_by="exp_end_date asc, creation asc",
                           limit_page_length=SUBTASK_LIMIT)
    return {"task": doc.name, "tasks": _cards(rows)}
