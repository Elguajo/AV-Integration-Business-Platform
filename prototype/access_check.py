"""TP-02 read-path check for AV Handover through the real web stack (nginx -> gunicorn).

Runs inside the backend container. Unrelated users must not see the seed handover through
any read path; the owner and the assigned PM are positive controls. Read-only apart from
access_setup (two synthetic users with fresh random passwords and one synthetic attachment).
Prints a table without secrets and exits non-zero on FAIL.
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
DOCTYPE = "AV Handover"


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
        _, page = self.request("GET", "/app")
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


def probes(facts):
    name = facts["handover"]
    q = urllib.parse.quote
    fields = json.dumps(["name", "snapshot_sha256", "project_name"])
    by_name = json.dumps([[DOCTYPE, "name", "=", name]])
    return [
        ("REST v1 document", "GET", f"/api/resource/{q(DOCTYPE)}/{name}", None),
        ("REST v2 document", "GET", f"/api/v2/document/{q(DOCTYPE)}/{name}", None),
        ("REST v1 list", "GET", f"/api/resource/{q(DOCTYPE)}", {"fields": fields}),
        ("REST v2 list", "GET", f"/api/v2/document/{q(DOCTYPE)}", {"fields": fields}),
        ("frappe.client.get", "GET", "/api/method/frappe.client.get",
         {"doctype": DOCTYPE, "name": name}),
        ("frappe.client.get_value", "GET", "/api/method/frappe.client.get_value",
         {"doctype": DOCTYPE, "filters": json.dumps({"name": name}),
          "fieldname": json.dumps(["snapshot_sha256", "project_name"])}),
        ("frappe.client.get_list", "GET", "/api/method/frappe.client.get_list",
         {"doctype": DOCTYPE, "fields": fields}),
        ("Desk form load", "GET", "/api/method/frappe.desk.form.load.getdoc",
         {"doctype": DOCTYPE, "name": name}),
        ("Desk docinfo (versions/comments/files)", "GET",
         "/api/method/frappe.desk.form.load.get_docinfo", {"doctype": DOCTYPE, "name": name}),
        ("List/report view", "POST", "/api/method/frappe.desk.reportview.get",
         {"doctype": DOCTYPE, "fields": fields, "filters": "[]"}),
        ("Report export CSV", "POST", "/api/method/frappe.desk.reportview.export_query",
         {"doctype": DOCTYPE, "file_format_type": "CSV", "fields": fields, "filters": "[]",
          "title": "tp02"}),
        ("Group-by sidebar", "POST", "/api/method/frappe.desk.listview.get_group_by_count",
         {"doctype": DOCTYPE, "current_filters": "[]", "field": "owner"}),
        ("Link search", "GET", "/api/method/frappe.desk.search.search_link",
         {"doctype": DOCTYPE, "txt": "AV-HO"}),
        ("Link search by title", "GET", "/api/method/frappe.desk.search.search_link",
         {"doctype": DOCTYPE, "txt": facts["project_name"][:9]}),
        ("Global search", "GET", "/api/method/frappe.utils.global_search.search",
         {"text": facts["project_name"][:9]}),
        ("Count", "GET", "/api/method/frappe.client.get_count", {"doctype": DOCTYPE}),
        ("Print view", "GET", "/printview", {"doctype": DOCTYPE, "name": name}),
        ("Version history", "GET", "/api/resource/Version",
         {"filters": json.dumps([["ref_doctype", "=", DOCTYPE], ["docname", "=", name]]),
          "fields": json.dumps(["name", "docname", "data"])}),
        ("Attachment File record", "GET", f"/api/resource/File/{facts['file']}", None),
        ("Attachment private URL", "GET", facts["file_url"], None),
        ("Attachment list by doc", "GET", "/api/resource/File",
         {"filters": json.dumps([["attached_to_name", "=", name]]),
          "fields": json.dumps(["name", "file_url"])}),
        ("Filtered list by name", "GET", f"/api/resource/{q(DOCTYPE)}",
         {"filters": by_name, "fields": fields}),
    ]


def leaked(body, facts, label, path, params):
    # An error that repeats a name the caller supplied is not a leak; data fields are.
    markers = [facts["snapshot_sha256"], facts["project_name"], "SYNTHETIC TP-02 ATTACHMENT"]
    supplied = path + json.dumps(params or {})
    markers += [value for value in (facts["handover"], facts["file"]) if value not in supplied]
    if label == "Count":
        try:
            return json.loads(body).get("message", 0) not in (0, None)
        except ValueError:
            return False
    return any(marker and marker in body for marker in markers)


def main():
    facts, passwords = setup()
    users = [
        ("owner Sales", facts["owner"], os.environ["AV_SALES_PASSWORD"], "control"),
        ("assigned PM", facts["project_manager"], os.environ["AV_PM_PASSWORD"], "control"),
        ("unassigned PM", "other-pm@av-prototype.invalid",
         passwords["AV_OTHER_PM_PASSWORD"], "deny"),
        ("other Sales", "other-sales@av-prototype.invalid",
         passwords["AV_OTHER_SALES_PASSWORD"], "deny"),
    ]
    print(f"Handover {facts['handover']}; quotation {facts['quotation']}; "
          f"attachment {facts['file']}")
    print("| Path | User | HTTP | Sees handover | Result |")
    print("|---|---|---|---|---|")
    failures = 0
    for label_user, user, password, expectation in users:
        client = Client(user, password)
        for label, method, path, params in probes(facts):
            status, body = client.request(method, path, params)
            seen = leaked(body, facts, label, path, params)
            if expectation == "deny":
                result = "FAIL" if seen else "PASS"
            else:
                result = "control"
            failures += result == "FAIL"
            print(f"| {label} | {label_user} | {status} | {'yes' if seen else 'no'} | {result} |")
    print(f"Unrelated-user failures: {failures}")
    sys.exit(1 if failures else 0)


if __name__ == "__main__":
    main()
