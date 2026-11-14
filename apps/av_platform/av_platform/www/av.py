"""/av: entry of AV Platform from the apps screen and old links (ADR-004).

Sends each user to the start page of their role; users without one go to Desk.
"""

import frappe

from av_platform.desk import home_page

no_cache = 1


def get_context(context):
    if frappe.session.user == "Guest":
        frappe.local.flags.redirect_location = "/login?redirect-to=/av"
    else:
        frappe.local.flags.redirect_location = "/" + (home_page() or "desk")
    raise frappe.Redirect(302)
