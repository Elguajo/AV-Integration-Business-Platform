app_name = "av_platform"
app_title = "AV Platform Prototype"
app_publisher = "AV Platform"
app_description = "Sales to PM technical proof using standard ERPNext documents"
app_email = ""
app_license = "Proprietary"
required_apps = ["erpnext"]
before_install = "av_platform.install.before_install"
after_install = "av_platform.install.after_install"
after_migrate = "av_platform.pm_board.ensure_setup"

# Desk is the product shell (ADR-004): the app has its own rail (dock/), sidebars and Desk
# pages; the role screens are Vue apps mounted in those pages (av_platform/desk.py).
add_to_apps_screen = [
    {
        "name": app_name,
        "title": "AV Platform",
        # /av sends each user to the start page of their role (www/av.py).
        "route": "/av",
        "has_permission": "av_platform.desk.has_app_permission",
    }
]
boot_session = "av_platform.desk.boot_session"
# Start page after login, by role (av_platform.desk.LANDING).
get_website_user_home_page = "av_platform.desk.home_page"

# The role screens used to be a separate site page under /av; old links land in Desk.
# 302 keeps the rule reversible: browsers do not cache it.
website_redirects = [
    {"source": r"/av/sales(/.*)?", "target": r"/desk/av-quotations\1", "redirect_http_status": 302},
    {"source": r"/av/board", "target": "/desk/av-work-board", "redirect_http_status": 302},
    {"source": r"/av/my-tasks", "target": "/desk/av-my-tasks", "redirect_http_status": 302},
]

doc_events = {
    "Task": {"before_validate": "av_platform.pm_board.sync_task_stage"},
}

permission_query_conditions = {
    "AV Handover": "av_platform.permissions.handover_query",
    # TP-02: Frappe's File list ignores the AV Handover row conditions above.
    "File": "av_platform.permissions.file_query",
    # TP-02: tasks and projects only for participants (permissions.py).
    "Project": "av_platform.permissions.project_query",
    "Task": "av_platform.permissions.task_query",
}
has_permission = {
    "AV Handover": "av_platform.permissions.handover_permission",
    "Project": "av_platform.permissions.project_permission",
    "Task": "av_platform.permissions.task_permission",
}
