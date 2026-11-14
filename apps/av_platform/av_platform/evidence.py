"""CLI-only backup and comparison evidence for the isolated prototype."""

import hashlib
from pathlib import Path

import frappe

from av_platform.demo import _guard

CANARY_NAME = "av-prototype-restore-canary.txt"
CANARY_CONTENT = "SYNTHETIC AV PROTOTYPE RESTORE CANARY\n"


def manifest():
    _guard()
    handovers = frappe.get_all("AV Handover", fields=[
        "name", "docstatus", "quotation", "project", "project_manager", "snapshot_json",
        "snapshot_sha256", "review_status", "reviewed_by", "reviewed_on", "accepted_value",
    ], order_by="name")
    projects = []
    quotations = []
    for row in handovers:
        quotations.append(frappe.get_doc("Quotation", row.quotation).as_dict())
        if row.project:
            projects.append(frappe.get_doc("Project", row.project).as_dict())
    files = []
    for name in frappe.get_all("File", filters={"file_name": CANARY_NAME}, pluck="name"):
        doc = frappe.get_doc("File", name)
        content = doc.get_content()
        if isinstance(content, str):
            content = content.encode("utf-8")
        files.append({"name": doc.name, "file_url": doc.file_url, "is_private": doc.is_private,
                      "sha256": hashlib.sha256(content).hexdigest()})
    return {"handovers": handovers, "quotations": quotations, "projects": projects, "files": files}


def backup():
    _guard()
    from frappe.utils.backups import new_backup

    if not frappe.db.exists("File", {"file_name": CANARY_NAME}):
        frappe.get_doc({"doctype": "File", "file_name": CANARY_NAME,
                        "is_private": 1, "content": CANARY_CONTENT}).insert()
    frappe.db.commit()  # CLI-only snapshot: backup must see the persisted canary.
    before = manifest()
    archive = new_backup(ignore_files=False, force=True)
    return {"manifest": before, "database": str(Path(archive.backup_path_db).resolve()),
            "public_files": str(Path(archive.backup_path_files).resolve()),
            "private_files": str(Path(archive.backup_path_private_files).resolve()),
            "config": str(Path(archive.backup_path_conf).resolve())}


ACCESS_ATTACHMENT = "av-tp02-synthetic-attachment.txt"
ACCESS_USERS = {
    "AV_OTHER_PM_PASSWORD": ("other-pm@av-prototype.invalid", "Other PM",
                             ["Projects User", "AV Project Manager"]),
    "AV_OTHER_SALES_PASSWORD": ("other-sales@av-prototype.invalid", "Other Sales",
                                ["Sales User", "AV Sales"]),
}


def access_setup():
    """Prepare the TP-02 read-path check: two unrelated users and a private attachment.

    Passwords come from the environment and are reset on every run; they are never stored.
    """
    import os

    from frappe.utils.password import update_password

    _guard()
    for variable, (email, first_name, roles) in ACCESS_USERS.items():
        password = os.environ.get(variable)
        if not password:
            frappe.throw(f"{variable} is required.")
        if not frappe.db.exists("User", email):
            frappe.get_doc({"doctype": "User", "email": email, "first_name": first_name,
                            "send_welcome_email": 0, "user_type": "System User",
                            "roles": [{"role": role} for role in roles]}).insert()
        update_password(email, password)
    seed_quote = frappe.db.get_value("Quotation", {"title": "AV-PROTOTYPE-T1-Q2"})
    handover = frappe.get_doc("AV Handover", {"quotation": seed_quote})
    file_name = frappe.db.get_value("File", {"attached_to_doctype": "AV Handover",
                                             "attached_to_name": handover.name,
                                             "file_name": ACCESS_ATTACHMENT})
    if not file_name:
        file_name = frappe.get_doc({
            "doctype": "File", "file_name": ACCESS_ATTACHMENT, "is_private": 1,
            "attached_to_doctype": "AV Handover", "attached_to_name": handover.name,
            "content": "SYNTHETIC TP-02 ATTACHMENT\n",
        }).insert().name
    frappe.db.commit()  # The HTTP check reads through separate web requests.
    return {"handover": handover.name, "snapshot_sha256": handover.snapshot_sha256,
            "project_name": handover.project_name, "quotation": seed_quote,
            "file": file_name,
            "file_url": frappe.db.get_value("File", file_name, "file_url"),
            "owner": handover.owner, "project_manager": handover.project_manager}
