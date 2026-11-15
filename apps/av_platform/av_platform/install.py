import frappe

from av_platform import overview, user_admin
from av_platform.shell import set_default_app
from av_platform.pm_board import ensure_setup


def before_install():
    if not frappe.conf.get("av_prototype"):
        frappe.throw("Install only on an isolated site configured with av_prototype = 1.")
    for role in ("AV Sales", "AV Project Manager"):
        if not frappe.db.exists("Role", role):
            frappe.get_doc({"doctype": "Role", "role_name": role, "desk_access": 1}).insert()


def after_install():
    ensure_setup()
    overview.ensure_setup()
    user_admin.ensure_setup()
    set_default_app()
