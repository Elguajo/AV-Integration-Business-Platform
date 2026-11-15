app_name = "av_platform"
app_title = "AV Platform Prototype"
app_publisher = "AV Platform"
app_description = "Sales to PM technical proof using standard ERPNext documents"
app_email = ""
app_license = "Proprietary"
required_apps = ["erpnext"]
before_install = "av_platform.install.before_install"
after_install = "av_platform.install.after_install"
after_migrate = [
    "av_platform.pm_board.ensure_setup",
    "av_platform.overview.ensure_setup",
    "av_platform.user_admin.ensure_setup",
]

# The role screens are one Vue app on /av (ADR-006, av_platform/shell.py); Desk is the back office.
add_to_apps_screen = [
    {
        "name": app_name,
        "title": "AV Platform",
        "route": "/av",
        "has_permission": "av_platform.shell.has_app_permission",
    }
]
website_route_rules = [{"from_route": "/av/<path:app_path>", "to_route": "av"}]
# Start page after login, by role (av_platform.shell.LANDING).
get_website_user_home_page = "av_platform.shell.home_page"

doc_events = {
    "Task": {"before_validate": "av_platform.pm_board.sync_task_stage"},
    # ADM-01: moderators change staff accounts only within their limits (user_admin.py).
    "User": {"before_validate": "av_platform.user_admin.guard_user_change"},
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
