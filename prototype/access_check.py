"""TP-02 read-path check through the real web stack (nginx -> gunicorn).

Runs inside the backend container. Targets: the seed AV Handover (visible to its author and the
assigned PM) and the board project with one of its tasks (visible to project members). Every
other user must not see them through any read path; allowed users are positive controls.
Read-only apart from access_setup (two synthetic users with fresh random passwords and three
synthetic attachments). Prints a table without secrets and exits non-zero on FAIL.
"""

import http.cookiejar
import json
import os
import re
import secrets
import subprocess
import sys
import urllib.error
import urllib.parse
import urllib.request

BASE = "http://frontend:8080"
SITE = "av.localhost"


def setup():
    env = dict(os.environ)
    passwords = {}
    for variable in ("AV_OTHER_PM_PASSWORD", "AV_OTHER_SALES_PASSWORD"):
        passwords[variable] = env[variable] = secrets.token_hex(24)
    output = subprocess.run(
        ["bench", "--site", SITE, "execute", "av_platform.evidence.access_setup"],
        check=True, text=True, stdout=subprocess.PIPE, env=env,
    ).stdout
    return json.loads(output.strip().splitlines()[-1]), passwords


class Client:
    def __init__(self, user, password):
        self.opener = urllib.request.build_opener(
            urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()))
        self.csrf = ""
        status, _ = self.request("POST", "/api/method/login", {"usr": user, "pwd": password})
        if status != 200:
            raise SystemExit(f"Login failed for {user}: HTTP {status}")
        _, page = self.request("GET", "/desk")
        match = re.search(r'csrf_token\s*=\s*"([^"]+)"', page)
        self.csrf = match.group(1) if match else ""

    def request(self, method, path, params=None):
        data = None
        url = BASE + path
        if params and method == "GET":
            url += "?" + urllib.parse.urlencode(params)
        elif params:
            data = urllib.parse.urlencode(params).encode()
        req = urllib.request.Request(url, data=data, method=method)
        req.add_header("Accept", "application/json")
        if self.csrf:
            req.add_header("X-Frappe-CSRF-Token", self.csrf)
        try:
            with self.opener.open(req, timeout=60) as response:
                return response.status, response.read().decode("utf-8", "replace")
        except urllib.error.HTTPError as error:
            return error.code, error.read().decode("utf-8", "replace")


def targets(facts):
    def escaped(text):
        return json.dumps(text)[1:-1]

    return [
        {"doctype": "AV Handover", "name": facts["handover"],
         "allowed": {facts["owner"], facts["project_manager"]},
         "fields": ["name", "snapshot_sha256", "project_name"],
         "markers": [facts["snapshot_sha256"], facts["project_name"], "SYNTHETIC TP-02 ATTACHMENT"],
         "file": facts["file"], "file_url": facts["file_url"],
         "search": ["AV-HO", facts["project_name"][:9]]},
        {"doctype": "Project", "name": facts["board_project"],
         "allowed": set(facts["board_members"]),
         "fields": ["name", "project_name"],
         "markers": [facts["board_project_name"], "SYNTHETIC TP-02 PROJECT ATTACHMENT"],
         "file": facts["project_file"], "file_url": facts["project_file_url"],
         "search": ["PROJ", "Board"]},
        {"doctype": "Task", "name": facts["task"],
         "allowed": set(facts["board_members"]),
         "fields": ["name", "subject", "project"],
         "markers": [facts["task_subject"], escaped(facts["task_subject"]),
                     "SYNTHETIC TP-02 TASK ATTACHMENT"],
         "file": facts["task_file"], "file_url": facts["task_file_url"],
         "search": ["TASK", facts["task_subject"][:6]]},
    ]


def probes(target):
    doctype, name = target["doctype"], target["name"]
    q = urllib.parse.quote
    fields = json.dumps(target["fields"])
    by_name = json.dumps([[doctype, "name", "=", name]])
    search_a, search_b = target["search"]
    return [
        ("REST v1 document", "GET", f"/api/resource/{q(doctype)}/{name}", None),
        ("REST v2 document", "GET", f"/api/v2/document/{q(doctype)}/{name}", None),
        ("REST v1 list", "GET", f"/api/resource/{q(doctype)}", {"fields": fields}),
        ("REST v2 list", "GET", f"/api/v2/document/{q(doctype)}", {"fields": fields}),
        ("frappe.client.get", "GET", "/api/method/frappe.client.get",
         {"doctype": doctype, "name": name}),
        ("frappe.client.get_value", "GET", "/api/method/frappe.client.get_value",
         {"doctype": doctype, "filters": json.dumps({"name": name}),
          "fieldname": json.dumps(target["fields"][1:])}),
        ("frappe.client.get_list", "GET", "/api/method/frappe.client.get_list",
         {"doctype": doctype, "fields": fields}),
        ("Desk form load", "GET", "/api/method/frappe.desk.form.load.getdoc",
         {"doctype": doctype, "name": name}),
        ("Desk docinfo (versions/comments/files)", "GET",
         "/api/method/frappe.desk.form.load.get_docinfo", {"doctype": doctype, "name": name}),
        ("List/report view", "POST", "/api/method/frappe.desk.reportview.get",
         {"doctype": doctype, "fields": fields, "filters": "[]"}),
        ("Report export CSV", "POST", "/api/method/frappe.desk.reportview.export_query",
         {"doctype": doctype, "file_format_type": "CSV", "fields": fields, "filters": "[]",
          "title": "tp02"}),
        ("Group-by sidebar", "POST", "/api/method/frappe.desk.listview.get_group_by_count",
         {"doctype": doctype, "current_filters": "[]", "field": "owner"}),
        ("Link search", "GET", "/api/method/frappe.desk.search.search_link",
         {"doctype": doctype, "txt": search_a}),
        ("Link search by title", "GET", "/api/method/frappe.desk.search.search_link",
         {"doctype": doctype, "txt": search_b}),
        ("Global search", "GET", "/api/method/frappe.utils.global_search.search",
         {"text": search_b}),
        ("Count", "GET", "/api/method/frappe.client.get_count",
         {"doctype": doctype, "filters": json.dumps({"name": name})}),
        ("Print view", "GET", "/printview", {"doctype": doctype, "name": name}),
        ("Version history", "GET", "/api/resource/Version",
         {"filters": json.dumps([["ref_doctype", "=", doctype], ["docname", "=", name]]),
          "fields": json.dumps(["name", "docname", "data"])}),
        ("Attachment File record", "GET", f"/api/resource/File/{target['file']}", None),
        ("Attachment private URL", "GET", target["file_url"], None),
        ("Attachment list by doc", "GET", "/api/resource/File",
         {"filters": json.dumps([["attached_to_name", "=", name]]),
          "fields": json.dumps(["name", "file_url"])}),
        ("Filtered list by name", "GET", f"/api/resource/{q(doctype)}",
         {"filters": by_name, "fields": fields}),
    ]


def leaked(body, target, label, path, params):
    # An error that repeats a name the caller supplied is not a leak; data fields are.
    supplied = path + json.dumps(params or {})
    markers = list(target["markers"])
    markers += [value for value in (target["name"], target["file"]) if value not in supplied]
    if label == "Count":
        try:
            return json.loads(body).get("message", 0) not in (0, None)
        except ValueError:
            return False
    return any(marker and marker in body for marker in markers)


def main():
    facts, passwords = setup()
    users = [
        ("owner Sales", facts["owner"], os.environ["AV_SALES_PASSWORD"]),
        ("assigned PM", facts["project_manager"], os.environ["AV_PM_PASSWORD"]),
        ("unassigned PM", "other-pm@av-prototype.invalid", passwords["AV_OTHER_PM_PASSWORD"]),
        ("other Sales", "other-sales@av-prototype.invalid", passwords["AV_OTHER_SALES_PASSWORD"]),
    ]
    print(f"Handover {facts['handover']}; quotation {facts['quotation']}; "
          f"board project {facts['board_project']}; task {facts['task']}")
    print("| Document | Path | User | HTTP | Sees it | Result |")
    print("|---|---|---|---|---|---|")
    failures = controls_seen = 0
    for label_user, user, password in users:
        client = Client(user, password)
        for target in targets(facts):
            allowed = user in target["allowed"]
            for label, method, path, params in probes(target):
                status, body = client.request(method, path, params)
                seen = leaked(body, target, label, path, params)
                result = "control" if allowed else ("FAIL" if seen else "PASS")
                failures += result == "FAIL"
                controls_seen += allowed and seen
                print(f"| {target['doctype']} | {label} | {label_user} | {status} | "
                      f"{'yes' if seen else 'no'} | {result} |")
    print(f"Unrelated-user failures: {failures}; control reads that returned data: {controls_seen}")
    sys.exit(1 if failures else 0)


if __name__ == "__main__":
    main()
