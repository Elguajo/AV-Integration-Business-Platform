"""The AV Platform shell (ADR-006): the role screens are one Vue app served on /av.

Desk stays the back office (ERPNext, reference data, document forms, administration). This
module decides which screens of the shell a user sees and where they land after login. The
screens only show what the server allows; every API checks its own permissions (ADR-001).
"""

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
    }


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
