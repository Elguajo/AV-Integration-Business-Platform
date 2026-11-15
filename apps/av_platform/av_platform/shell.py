"""The AV Platform shell (ADR-006): the role screens are one Vue app served on /av.

Desk stays the back office (ERPNext, reference data, document forms, administration). This
module decides which screens of the shell a user sees and where they land after login. The
screens only show what the server allows; every API checks its own permissions (ADR-001).
"""

import html
import re

import frappe

HOME_ROLES = {"AV Director", "System Manager", "AV Project Manager", "Projects Manager"}
WORK_ROLES = {"Projects User", "Projects Manager", "System Manager"}
# Screens of the shell in menu order: (key, route under /av, roles that see it).
VIEWS = (
    ("home", "home", HOME_ROLES),
    ("my-tasks", "my-tasks", WORK_ROLES),
    ("projects", "projects", HOME_ROLES | {"Projects User"}),
    ("board", "board", WORK_ROLES),
    ("sales", "sales", {"AV Sales", "System Manager"}),
)
APP_ROLES = {role for _key, _route, roles in VIEWS for role in roles} | {"AV Administrator", "AV Moderator"}
# Where each role starts after login, in priority order (first match wins).
LANDING = (
    ({"AV Director"}, "av/home"),
    ({"AV Sales"}, "av/sales"),
    ({"Projects Manager", "AV Project Manager"}, "av/home"),
    ({"Projects User"}, "av/my-tasks"),
    # ADM-01: a moderator without a work role starts in the staff list of Desk.
    ({"AV Moderator"}, "desk/user"),
)


def visible_views(user=None):
    """Keys of the shell screens this user may open, in menu order."""
    user = user or frappe.session.user
    if user == "Guest":
        return []
    roles = set(frappe.get_roles(user))
    return [key for key, _route, needed in VIEWS if roles & needed]


def boot(user=None):
    """Data the shell needs before its first request (rendered into the /av page)."""
    user = user or frappe.session.user
    info = frappe.db.get_value("User", user, ["full_name", "user_image", "user_type"], as_dict=True)
    return {
        "user": user,
        "full_name": info.full_name or user,
        "image": info.user_image,
        "views": visible_views(user),
        "landing": home_page(user),
        # Desk is open to system users only; website users have no back office.
        "desk": info.user_type == "System User",
        "create": create_options(user, info.user_type == "System User"),
    }


# Global header (UI-05): search, the «+» menu and notifications, as in D-Tools Cloud (research/12
# §6.2в). Every answer goes through Frappe's permission layer (has_permission, get_list), so the
# header shows nothing the user could not open elsewhere.

# Documents the «+» menu may open in Desk. Project is left out on purpose: a project appears only
# from an accepted Sales handover (PRJ-01), even for administrators who may create one in Desk.
CREATE_DOCTYPES = ("Quotation", "Customer", "Task")
# Global search: (doctype, fields matched besides name, title field, subtitle field, filters).
SEARCH_SOURCES = (
    ("Project", ("project_name", "customer"), "project_name", "customer", {}),
    # Works (Task) of the board; templates are not works of a project.
    ("Task", ("subject",), "subject", "project", {"is_template": 0}),
    ("Quotation", ("customer_name", "title"), "customer_name", "title", {}),
    ("Customer", ("customer_name",), "customer_name", "customer_group", {}),
)
# Subtitles that are links shown by the linked record's title: doctype -> (linked doctype, title).
SEARCH_SUBTITLE_TITLES = {"Task": ("Project", "project_name")}
SEARCH_LIMIT = 5
SEARCH_MIN, SEARCH_MAX = 2, 140
NOTIFICATIONS_LIMIT = 20
# Records with their own screen in the shell: doctype -> shell screen that shows them.
SHELL_RECORDS = {"Project": "projects", "Quotation": "sales"}
# Records shown in a side panel of a shell screen: doctype -> (screen, query parameter). A work
# opens on the board as /av/board?task=<name> (the frontend's TASK_QUERY).
SHELL_PANELS = {"Task": ("board", "task")}
# Notification lines in Russian, built from the log's structured fields (type, document, sender).
# The product word for Task is «работа». Nouns are (accusative, dative); other doctypes go without.
NOTIFICATION_NOUNS = {
    "Task": ("работу", "работе"),
    "Project": ("проект", "проекту"),
    "Quotation": ("предложение", "предложению"),
    "Customer": ("клиента", "клиенту"),
}
NOTIFICATION_LINES = {
    "Assignment": "{who} назначил(а) вам {acc}«{title}»",
    "Unassignment": "{who} снял(а) ваше назначение на {acc}«{title}»",
    "Mention": "{who} упомянул(а) вас в комментарии к {dat}«{title}»",
    "Share": "{who} открыл(а) вам доступ к {dat}«{title}»",
}
# Frappe logs both a new assignment and its removal with type "Assignment"
# (frappe/desk/form/assign_to.py, notify_assignment); only the message tells them apart. The
# removal is recognised by the literal parts of Frappe's own message, in English and translated.
ASSIGNMENT_REMOVED = "Your assignment on {0} {1} has been removed by {2}"
# Every Frappe producer wraps the record title in this tag (notification_log.get_title_html).
TITLE_TAG = re.compile(r'<b class="subject-title">(.*?)</b>', re.DOTALL)


def desk_url(doctype, name=None):
    slug = doctype.lower().replace(" ", "-")
    return f"/desk/{slug}/{frappe.utils.quote(name) if name else 'new'}"


def record_url(doctype, name, views, desk):
    """Where a record opens: its shell screen if the user has it, else Desk, else nowhere."""
    view = SHELL_RECORDS.get(doctype)
    if view in views:
        return f"/av/{view}/{frappe.utils.quote(name)}"
    view, param = SHELL_PANELS.get(doctype, (None, None))
    if view in views:
        return f"/av/{view}?{param}={frappe.utils.quote(name)}"
    return desk_url(doctype, name) if desk else None


def create_options(user, desk):
    """New documents this user may start from the header; they open in Desk."""
    if not desk:
        return []
    return [
        {"doctype": doctype, "href": desk_url(doctype)}
        for doctype in CREATE_DOCTYPES
        if frappe.has_permission(doctype, "create", user=user)
    ]


def _is_desk_user(user):
    return frappe.db.get_value("User", user, "user_type") == "System User"


@frappe.whitelist(methods=["GET"])
def search(text: str):
    """Records whose name or title contains the text, a few per document type."""
    text = (text or "").strip()[:SEARCH_MAX]
    if len(text) < SEARCH_MIN:
        return []
    user = frappe.session.user
    views, desk = visible_views(user), _is_desk_user(user)
    # The text is matched literally: its own % and _ are not wildcards.
    like = "%{}%".format(text.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_"))
    results = []
    for doctype, fields, title_field, subtitle_field, filters in SEARCH_SOURCES:
        if not frappe.has_permission(doctype, "read", user=user):
            continue
        rows = frappe.get_list(
            doctype,
            fields=list(dict.fromkeys(["name", title_field, subtitle_field, *fields])),
            filters=filters,
            or_filters=[[field, "like", like] for field in ("name", *fields)],
            order_by="modified desc",
            limit=SEARCH_LIMIT,
        )
        subtitles = _linked_titles(doctype, {row.get(subtitle_field) for row in rows}, user)
        for row in rows:
            href = record_url(doctype, row.name, views, desk)
            if not href:
                continue
            title = row.get(title_field) or row.name
            subtitle = subtitles.get(row.get(subtitle_field), row.get(subtitle_field))
            results.append({
                "doctype": doctype,
                "name": row.name,
                "title": title,
                "subtitle": subtitle if subtitle and subtitle != title else None,
                "href": href,
            })
    return results


def _linked_titles(doctype, names, user):
    """Titles of the records a subtitle links to, only those the user may read; others keep the id."""
    link = SEARCH_SUBTITLE_TITLES.get(doctype)
    names = [name for name in names if name]
    if not link or not names or not frappe.has_permission(link[0], "read", user=user):
        return {}
    linked_doctype, title_field = link
    rows = frappe.get_list(linked_doctype, filters={"name": ("in", names)},
                           fields=["name", title_field], limit=len(names))
    return {row.name: row.get(title_field) for row in rows if row.get(title_field)}


def notification_line(row):
    """A Russian line for a Notification Log from its structured fields; Frappe's own subject
    (as plain text) for types without a line here (Alert, custom types) or with fields missing."""
    original = frappe.utils.strip_html_tags(row.subject or "").strip()
    line_type = row.type
    if line_type == "Assignment" and _is_assignment_removed(original):
        line_type = "Unassignment"
    template = NOTIFICATION_LINES.get(line_type)
    if not (template and row.from_user and row.document_type and row.document_name):
        return original
    found = TITLE_TAG.search(row.subject or "")
    title = html.unescape(frappe.utils.strip_html_tags(found.group(1))).strip() if found else ""
    acc, dat = NOTIFICATION_NOUNS.get(row.document_type, ("", ""))
    return template.format(
        who=frappe.utils.get_fullname(row.from_user),
        acc=f"{acc} " if acc else "",
        dat=f"{dat} " if dat else "",
        title=title or row.document_name,
    )


def _is_assignment_removed(text):
    for message in {ASSIGNMENT_REMOVED, frappe._(ASSIGNMENT_REMOVED)}:
        parts = [part.strip() for part in re.split(r"\{\d+\}", message) if part.strip()]
        if parts and all(part in text for part in parts):
            return True
    return False


@frappe.whitelist(methods=["GET"])
def get_notifications():
    """The user's own notifications from Frappe's Notification Log, newest first.

    Filtered by recipient for everyone, Administrator included: Frappe lets Administrator read
    every log, but the bell shows only what was addressed to the person. Frappe stores subjects as
    HTML in the language of the moment (often English); the header gets a Russian plain-text line
    (notification_line).
    """
    user = frappe.session.user
    views, desk = visible_views(user), _is_desk_user(user)
    rows = frappe.get_list(
        "Notification Log",
        filters={"for_user": user},
        fields=["name", "subject", "type", "document_type", "document_name", "from_user", "read", "creation"],
        order_by="creation desc",
        limit=NOTIFICATIONS_LIMIT,
    )
    items = []
    for row in rows:
        href = None
        if row.document_type and row.document_name:
            href = record_url(row.document_type, row.document_name, views, desk)
        items.append({
            "name": row.name,
            "subject": notification_line(row),
            "type": row.type,
            "from_user": frappe.utils.get_fullname(row.from_user) if row.from_user else None,
            "read": bool(row.read),
            "creation": row.creation,
            "href": href,
        })
    unread = frappe.db.count("Notification Log", {"for_user": user, "read": 0})
    return {"items": items, "unread": unread}


def has_app_permission():
    """Show AV Platform on the apps screen only to users of its screens."""
    if frappe.session.user == "Administrator":
        return True
    return bool(APP_ROLES & set(frappe.get_roles()))


def home_page(user=None):
    """Start page of AV Platform for this user, or None to let Frappe decide.

    Used by the `get_website_user_home_page` hook: Frappe 16 reads it for every user in
    `get_home_page`, which picks where a desk user lands after login. `default_app` alone does
    not change that redirect for desk users.
    """
    roles = set(frappe.get_roles(user or frappe.session.user))
    for needed, path in LANDING:
        if roles & needed:
            return path
    return None


def set_default_app():
    """Make AV Platform the site's default app unless an administrator already chose one."""
    if frappe.db.get_single_value("System Settings", "default_app"):
        return
    frappe.db.set_single_value("System Settings", "default_app", "av_platform")
    frappe.clear_document_cache("System Settings", "System Settings")
