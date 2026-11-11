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
