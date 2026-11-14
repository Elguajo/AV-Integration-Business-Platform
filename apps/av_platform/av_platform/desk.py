"""Desk integration (ADR-004): the role screens are Vue apps mounted inside Desk pages.

The frontend build (apps/av_platform/frontend) writes hashed files and a Vite manifest to
public/frontend. At login the boot payload gets the current entry and stylesheet paths, so a
Desk page can import them without hard-coding hashes.
"""

import json
import os

import frappe

ASSET_BASE = "/assets/av_platform/frontend/"
ENTRY = "src/desk.ts"
DESK_ROLES = {"System Manager", "AV Sales", "Projects User", "Projects Manager"}
# Where each role starts after login, in priority order (first match wins).
LANDING = (
    ({"AV Sales"}, "desk/av-quotations"),
    ({"Projects User", "Projects Manager", "AV Project Manager"}, "desk/av-my-tasks"),
)


def manifest_path():
    return frappe.get_app_path("av_platform", "public", "frontend", ".vite", "manifest.json")


def desk_assets(path=None):
    """Return {"entry", "css"} for the built role screens, or None when there is no build."""
    path = path or manifest_path()
    if not os.path.exists(path):
        return None
    with open(path, encoding="utf-8") as f:
        chunk = json.load(f).get(ENTRY)
    if not chunk:
        return None
    return {
        "entry": ASSET_BASE + chunk["file"],
        "css": [ASSET_BASE + css for css in chunk.get("css", [])],
    }


def boot_session(bootinfo):
    if frappe.session.user != "Guest":
        bootinfo.av_desk = desk_assets()


def has_app_permission():
    """Show AV Platform on the apps screen only to users of its screens."""
    if frappe.session.user == "Administrator":
        return True
    return bool(DESK_ROLES & set(frappe.get_roles()))


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
