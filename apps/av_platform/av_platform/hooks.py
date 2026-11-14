app_name = "av_platform"
app_title = "AV Platform Prototype"
app_publisher = "AV Platform"
app_description = "Sales to PM technical proof using standard ERPNext documents"
app_email = ""
app_license = "Proprietary"
required_apps = ["erpnext"]
before_install = "av_platform.install.before_install"
after_install = "av_platform.pm_board.ensure_setup"
after_migrate = "av_platform.pm_board.ensure_setup"

doc_events = {
    "Task": {"before_validate": "av_platform.pm_board.sync_task_stage"},
}

# Role workspaces are a Vue app served by www/av.py; deep links reload the same page.
website_route_rules = [
    {"from_route": "/av/<path:app_path>", "to_route": "av"},
]

permission_query_conditions = {
    "AV Handover": "av_platform.permissions.handover_query",
    # TP-02: Frappe's File list ignores the AV Handover row conditions above.
    "File": "av_platform.permissions.file_query",
}
has_permission = {
    "AV Handover": "av_platform.permissions.handover_permission",
}
