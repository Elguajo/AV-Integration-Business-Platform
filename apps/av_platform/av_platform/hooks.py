app_name = "av_platform"
app_title = "AV Platform Prototype"
app_publisher = "AV Platform"
app_description = "Sales to PM technical proof using standard ERPNext documents"
app_email = ""
app_license = "Proprietary"
required_apps = ["erpnext"]
before_install = "av_platform.install.before_install"

permission_query_conditions = {
    "AV Handover": "av_platform.permissions.handover_query",
}
has_permission = {
    "AV Handover": "av_platform.permissions.handover_permission",
}
