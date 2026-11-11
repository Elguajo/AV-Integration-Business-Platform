import frappe


def before_install():
    if not frappe.conf.get("av_prototype"):
        frappe.throw("Install only on an isolated site configured with av_prototype = 1.")
    for role in ("AV Sales", "AV Project Manager"):
        if not frappe.db.exists("Role", role):
            frappe.get_doc({"doctype": "Role", "role_name": role, "desk_access": 1}).insert()
