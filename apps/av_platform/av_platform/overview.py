"""Home, project register and project card (DIR-01, UI-03; MVP-SPEC §3, §11.1, §14 OVW-01–OVW-04).

Read-only screens: the sales funnel apart from the projects in execution, the register of projects
and the card of one project. The server decides every stage, status and reason; the pages render
them. Data is read with get_list, so the same permission rules apply as in Desk lists, reports and
search: a PM sees the projects they take part in, the director sees all of them. Money comes from
AV Handover and is shown only to users who may read it. Unknown values stay None (shown as
«нет данных»), never zero. Reasons are stable codes; the frontend owns the texts (ARC-03).
"""

import json
from datetime import timedelta

import frappe
from frappe.permissions import add_permission, update_permission_property
from frappe.utils import flt, getdate, today

from av_platform.pm_api import due_bucket, due_state, get_my_tasks
from av_platform.pm_board import enabled_stages
from av_platform.sales_api import QUOTATION_FIELDS, with_stages

DIRECTOR_ROLE = "AV Director"
# The funnel is the director's (DIR-01); the home page also serves project managers (UI-03).
FUNNEL_ROLES = {DIRECTOR_ROLE, "System Manager"}
HOME_ROLES = FUNNEL_ROLES | {"AV Project Manager", "Projects Manager"}
# The register and the card show only projects the user may read, so field users get them too.
PROJECT_ROLES = HOME_ROLES | {"Projects User"}
# Read-only access to standard documents that the overview opens. AV Handover grants it in its JSON.
READ_DOCTYPES = ("Project", "Task", "Quotation")

LIST_LIMIT = 500
MY_TASKS_SHOWN = 6
CARD_TASK_LIMIT = 500
CARD_LIST_LIMIT = 50
EXPIRING_DAYS = 30
MILESTONE_SOON_DAYS = 7
CLOSED = ("Completed", "Cancelled")

FUNNEL_STAGES = ("draft", "issued", "handover", "returned", "accepted")
STAGE_GROUP = {
    "draft": "draft",
    "issued": "issued",
    "handover_draft": "handover",
    "handover_pending": "handover",
    "handover_unknown": "handover",
    "returned": "returned",
    "accepted": "accepted",
}
OPEN_DEAL_GROUPS = ("issued", "returned")

# Status precedence (OVW-03): a confirmed problem outranks a risk, a risk outranks the unknown.
STATUS_BY_REASON = {
    "blocked": "problem",
    "overdue": "problem",
    "undated": "risk",
    "unassigned": "risk",
    # An explanation, not a deviation: a milestone due soon keeps a project on plan.
    "milestone_soon": "on_plan",
    "no_works": "unknown",
    "no_dates": "unknown",
    "all_done": "unknown",
}
STATUS_ORDER = ("problem", "risk", "unknown", "on_plan")


def ensure_setup():
    """Idempotent: the role and its read-only rules (after install and every migrate)."""
    if not frappe.db.exists("Role", DIRECTOR_ROLE):
        frappe.get_doc({"doctype": "Role", "role_name": DIRECTOR_ROLE, "desk_access": 1}).insert(
            ignore_permissions=True)
    for doctype in READ_DOCTYPES:
        # The first custom rule copies the standard ERPNext rules of the DocType (Frappe behaviour,
        # same as the Role Permission Manager); existing roles keep exactly what they had.
        if not frappe.db.exists("Custom DocPerm", {"parent": doctype, "role": DIRECTOR_ROLE,
                                                   "permlevel": 0, "if_owner": 0}):
            add_permission(doctype, DIRECTOR_ROLE, 0, "read")
        update_permission_property(doctype, DIRECTOR_ROLE, 0, "report", 1)


def _has_role(roles, user=None):
    user = user or frappe.session.user
    return user == "Administrator" or bool(roles & set(frappe.get_roles(user)))


def can_view(user=None):
    """Home page of the shell (/av/home)."""
    return _has_role(HOME_ROLES, user)


def can_view_funnel(user=None):
    return _has_role(FUNNEL_ROLES, user)


def _require(roles):
    if not _has_role(roles):
        frappe.throw("This page is not available to you.", frappe.PermissionError)


def money_visible():
    """Accepted sums come from AV Handover; without read access they are hidden, not unknown."""
    return bool(frappe.has_permission("AV Handover", "read"))


def _user_names(users):
    users = sorted({u for u in users if u})
    if not users:
        return {}
    return dict(frappe.get_all("User", filters={"name": ["in", users]},
                               fields=["name", "full_name"], as_list=True))


def _person(user, names):
    return {"name": user, "full_name": names.get(user) or user} if user else None


def _totals(rows):
    """Sums per currency. Amounts in different currencies are never added together."""
    totals = {}
    for row in rows:
        if row.grand_total is None or not row.currency:
            continue
        totals[row.currency] = totals.get(row.currency, 0) + flt(row.grand_total)
    return [{"currency": c, "amount": a} for c, a in sorted(totals.items())]


def deal_alert(group, valid_till, current_day):
    if group not in OPEN_DEAL_GROUPS or not valid_till:
        return None
    valid_till = getdate(valid_till)
    if valid_till < current_day:
        return "expired"
    if valid_till <= current_day + timedelta(days=EXPIRING_DAYS):
        return "expiring"
    return None


def _funnel(current_day):
    quotes = frappe.get_list(
        "Quotation", fields=QUOTATION_FIELDS,
        filters={"quotation_to": "Customer", "docstatus": ["!=", 2]},
        order_by="modified desc", limit_page_length=LIST_LIMIT + 1,
    )
    truncated = len(quotes) > LIST_LIMIT
    rows = [r for r in with_stages(quotes[:LIST_LIMIT]) if r["stage"] in STAGE_GROUP]
    # A draft of a customer that already has an issued version is a new version in work,
    # not another deal: it stays out of the counts and sums (versions.py, prototype rule H).
    issued_keys = {(r["party_name"], r["company"]) for r in rows if r["stage"] != "draft"}
    deals, revisions = [], 0
    for row in rows:
        if row["stage"] == "draft" and (row["party_name"], row["company"]) in issued_keys:
            revisions += 1
            continue
        group = STAGE_GROUP[row["stage"]]
        handover = row.get("handover") or {}
        deals.append(frappe._dict({
            "name": row["name"], "title": row["title"], "customer": row["customer_name"] or row["party_name"],
            "group": group, "stage": row["stage"], "grand_total": row["grand_total"],
            "currency": row["currency"], "valid_till": row["valid_till"], "owner": row["owner"],
            "project": handover.get("project"),
            "alert": deal_alert(group, row["valid_till"], current_day),
        }))
    names = _user_names([d.owner for d in deals])
    stages = [{"stage": s, "count": sum(1 for d in deals if d.group == s),
               "totals": _totals([d for d in deals if d.group == s])} for s in FUNNEL_STAGES]
    attention = [d for d in deals if d.alert or d.group == "returned"]
    attention.sort(key=lambda d: (d.valid_till is None, getdate(d.valid_till) if d.valid_till else None))
    return {
        "stages": stages,
        "open_totals": _totals([d for d in deals if d.group in ("issued", "handover", "returned")]),
        "attention": [{**d, "owner": _person(d.owner, names)} for d in attention],
        "revisions": revisions,
        "truncated": truncated,
    }


def _assignees(task):
    return json.loads(task._assign or "[]")


def _end(task):
    return getdate(task.exp_end_date) if task.exp_end_date else None


def project_reasons(tasks, current_day):
    """Every reason at once (OVW-03), with counts. `tasks` are the project's non-cancelled tasks."""
    works = [t for t in tasks if not t.is_group]
    open_tasks = [t for t in tasks if t.status not in CLOSED]
    open_works = [t for t in works if t.status not in CLOSED]
    reasons = []

    def add(code, items):
        if items:
            reasons.append({"code": code, "count": len(items)})

    add("blocked", [t for t in open_tasks if t.av_block_reason])
    add("overdue", [t for t in open_tasks if _end(t) and _end(t) < current_day])
    soon = current_day + timedelta(days=MILESTONE_SOON_DAYS)
    add("milestone_soon", [t for t in open_tasks if t.is_milestone and _end(t)
                           and current_day <= _end(t) <= soon])
    if not works:
        reasons.append({"code": "no_works", "count": 0})
    elif not open_works:
        reasons.append({"code": "all_done", "count": len(works)})
    elif not any(_end(t) for t in open_works):
        reasons.append({"code": "no_dates", "count": len(open_works)})
    else:
        add("undated", [t for t in open_works if not _end(t)])
    add("unassigned", [t for t in open_works if not _assignees(t)])
    return reasons


def project_status(reasons):
    found = {STATUS_BY_REASON[r["code"]] for r in reasons}
    return next((s for s in STATUS_ORDER if s in found), "on_plan")


def _obstacle(open_tasks, current_day):
    """The main obstacle: a blocked work first, then the most overdue one."""
    def by_end(task):
        return (_end(task) is None, _end(task) or current_day)

    blocked = sorted((t for t in open_tasks if t.av_block_reason), key=by_end)
    if blocked:
        return "blocked", blocked[0]
    overdue = sorted((t for t in open_tasks if _end(t) and _end(t) < current_day), key=by_end)
    if overdue:
        return "overdue", overdue[0]
    return None, None


def _task_ref(task, names, current_day):
    return {
        "name": task.name, "subject": task.subject, "end": task.exp_end_date,
        "due": due_state(task.exp_end_date, task.status, current_day),
        "assignees": [_person(u, names) for u in _assignees(task)],
    }


PROJECT_FIELDS = ["name", "project_name", "customer", "status", "expected_start_date", "expected_end_date"]


def _project_tasks(names, limit=0):
    return frappe.get_list(
        "Task", filters={"project": ["in", names or [""]], "is_template": 0,
                         "status": ["!=", "Cancelled"]},
        fields=["name", "subject", "project", "status", "is_group", "is_milestone",
                "av_block_reason", "av_stage", "exp_end_date", "_assign"],
        order_by="exp_end_date asc", limit_page_length=limit,
    )


def _handovers(names):
    """Accepted handovers the user may read; none when AV Handover is closed to the user."""
    if not money_visible():
        return []
    return frappe.get_list(
        "AV Handover", filters={"project": ["in", names or [""]], "docstatus": 1},
        fields=["name", "project", "project_manager", "accepted_value", "currency", "quotation",
                "reviewed_on"],
        limit_page_length=0,
    )


def _teams(names):
    """Members (Project.users) of projects that already passed the get_list permission check."""
    rows = frappe.get_all("Project User", filters={"parenttype": "Project", "parent": ["in", names or [""]]},
                          fields=["parent", "user"], order_by="idx asc")
    teams = {}
    for row in rows:
        teams.setdefault(row.parent, []).append(row.user)
    return teams


def _project_rows(projects, current_day, tasks=None):
    """Rows of readable projects and the data they were built from."""
    names = [p.name for p in projects]
    tasks = _project_tasks(names) if tasks is None else tasks
    handovers = _handovers(names)
    teams = _teams(names)
    by_project = {}
    for task in tasks:
        by_project.setdefault(task.project, []).append(task)
    basis = {h.project: h for h in handovers}
    users = ([u for t in tasks for u in _assignees(t)] + [h.project_manager for h in handovers]
             + [u for team in teams.values() for u in team])
    people = _user_names(users)
    me = frappe.session.user

    rows = []
    for project in projects:
        project_tasks = by_project.get(project.name, [])
        works = [t for t in project_tasks if not t.is_group]
        open_tasks = [t for t in project_tasks if t.status not in CLOSED]
        milestones = sorted((t for t in open_tasks if t.is_milestone and _end(t)), key=_end)
        kind, obstacle = _obstacle(open_tasks, current_day)
        reasons = project_reasons(project_tasks, current_day)
        handover = basis.get(project.name)
        team = teams.get(project.name, [])
        rows.append({
            "name": project.name,
            "project_name": project.project_name,
            "customer": project.customer,
            "expected_end": project.expected_end_date,
            "pm": _person(handover.project_manager, people) if handover else None,
            "team": [_person(u, people) for u in team],
            "mine": me in team or bool(handover and handover.project_manager == me),
            "basis": ({"amount": handover.accepted_value, "currency": handover.currency,
                       "quotation": handover.quotation} if handover else None),
            "works": {"done": sum(1 for t in works if t.status == "Completed"), "total": len(works)},
            "next_milestone": _task_ref(milestones[0], people, current_day) if milestones else None,
            "obstacle": ({**_task_ref(obstacle, people, current_day), "kind": kind,
                          "reason": obstacle.av_block_reason} if obstacle else None),
            "status": project_status(reasons),
            "reasons": reasons,
        })
    return rows, by_project, people, basis


def _projects(current_day):
    projects = frappe.get_list(
        "Project", filters={"status": "Open"}, fields=PROJECT_FIELDS,
        order_by="project_name asc", limit_page_length=LIST_LIMIT + 1,
    )
    truncated = len(projects) > LIST_LIMIT
    rows = _project_rows(projects[:LIST_LIMIT], current_day)[0]
    order = {s: i for i, s in enumerate(STATUS_ORDER)}
    rows.sort(key=lambda r: (order[r["status"]], r["project_name"] or r["name"]))
    return {"rows": rows, "truncated": truncated}


def _status_counts(rows):
    return {s: sum(1 for r in rows if r["status"] == s) for s in STATUS_ORDER}


def _my_tasks():
    """The user's open works by due bucket, the same list as «Мои задачи» (PM-02)."""
    try:
        result = get_my_tasks("mine")
    except frappe.PermissionError:
        return None
    tasks = result["tasks"]
    names = {p["name"]: p["project_name"] for p in result["projects"]}
    buckets = ("overdue", "today", "week", "later", "no_date")
    return {
        "counts": {b: sum(1 for t in tasks if t["bucket"] == b) for b in buckets},
        "items": [{"name": t["name"], "subject": t["subject"], "project": t["project"],
                   "project_name": names.get(t["project"]), "end": t["end"], "bucket": t["bucket"],
                   "block_reason": t["block_reason"]}
                  for t in tasks if t["bucket"] in ("overdue", "today", "week")][:MY_TASKS_SHOWN],
        "truncated": result["truncated"],
    }


@frappe.whitelist(methods=["GET"])
def get_overview():
    """Home page: the user's works, the funnel (director only) and the projects in execution."""
    _require(HOME_ROLES)
    current_day = getdate(today())
    projects = _projects(current_day)
    return {
        "today": str(current_day),
        "user": {"name": frappe.session.user,
                 "full_name": _user_names([frappe.session.user]).get(frappe.session.user)},
        "funnel": _funnel(current_day) if can_view_funnel() else None,
        "my_tasks": _my_tasks(),
        "projects": projects,
        "status_counts": _status_counts(projects["rows"]),
        "money_visible": money_visible(),
    }


@frappe.whitelist(methods=["GET"])
def get_projects():
    """Register of the open projects the user may read (UI-03)."""
    _require(PROJECT_ROLES)
    current_day = getdate(today())
    projects = _projects(current_day)
    return {
        "today": str(current_day),
        "projects": projects,
        "status_counts": _status_counts(projects["rows"]),
        "money_visible": money_visible(),
    }


def _readable_project(project):
    """The project, or the same refusal whether it is missing or closed to the user."""
    found = frappe.get_list("Project", filters={"name": project}, fields=PROJECT_FIELDS,
                            limit_page_length=1) if project else []
    if not found:
        frappe.throw("This project is not available to you.", frappe.PermissionError)
    return found[0]


def _work(task, people, current_day):
    closed = task.status in CLOSED
    return {
        "name": task.name, "subject": task.subject, "status": task.status, "stage": task.av_stage,
        "end": task.exp_end_date, "due": due_state(task.exp_end_date, task.status, current_day),
        "bucket": None if closed else due_bucket(task.exp_end_date, current_day),
        "is_milestone": bool(task.is_milestone),
        "block_reason": (task.av_block_reason or "").strip() or None,
        "assignees": [_person(u, people) for u in _assignees(task)],
    }


@frappe.whitelist(methods=["GET"])
def get_project(project: str):
    """Card of one project (UI-03): header, every obstacle, works by stage, milestones, files."""
    _require(PROJECT_ROLES)
    current_day = getdate(today())
    doc = _readable_project(project)
    # The display limit must not hide blockers or alter the project's summary.
    tasks = _project_tasks([doc.name])
    rows, by_project, people, basis = _project_rows([doc], current_day, tasks)
    works = [t for t in by_project.get(doc.name, []) if not t.is_group]
    truncated = len(works) > CARD_TASK_LIMIT
    open_works = [t for t in works if t.status not in CLOSED]

    def by_end(task):
        return (_end(task) is None, _end(task) or current_day)

    obstacles = sorted((t for t in open_works
                        if t.av_block_reason or (_end(t) and _end(t) < current_day)), key=by_end)
    milestones = sorted((t for t in open_works if t.is_milestone and _end(t)), key=_end)
    mine = sorted((t for t in open_works if frappe.session.user in _assignees(t)), key=by_end)
    handover = basis.get(doc.name)
    files = frappe.get_list("File", filters={"attached_to_doctype": "Project", "attached_to_name": doc.name},
                            fields=["name", "file_name", "file_url", "is_private", "creation"],
                            order_by="creation desc", limit_page_length=CARD_LIST_LIMIT)
    return {
        "today": str(current_day),
        "project": {**rows[0], "project_status": doc.status, "expected_start": doc.expected_start_date,
                    "handover": ({"name": handover.name, "reviewed_on": handover.reviewed_on}
                                 if handover else None)},
        "stages": [{"name": s.name, "label": s.label, "is_closed": bool(s.is_closed)}
                   for s in enabled_stages()],
        "works": [_work(t, people, current_day) for t in works[:CARD_TASK_LIMIT]],
        "works_truncated": truncated,
        "obstacles": [{**_work(t, people, current_day),
                       "kind": "blocked" if t.av_block_reason else "overdue"} for t in obstacles],
        "milestones": [_work(t, people, current_day) for t in milestones[:5]],
        "my_works": [_work(t, people, current_day) for t in mine[:CARD_LIST_LIMIT]],
        "files": [{"name": f.name, "file_name": f.file_name, "file_url": f.file_url,
                   "is_private": bool(f.is_private), "creation": str(f.creation)} for f in files],
        "money_visible": money_visible(),
    }
