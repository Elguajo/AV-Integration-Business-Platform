"""TP-03 concurrency and rollback check for the Sales -> PM handover (PROTOTYPE-BRIEF §4.1).

Runs inside the backend container. Connection A is this process (frappe.connect, its own
MariaDB session). Every other caller is a separate PM login through nginx -> gunicorn, so each
HTTP request runs in its own worker thread with its own database connection.

Each scenario uses a fresh synthetic quotation and handover of a dedicated TP-03 customer and
commits them; handovers and projects of other customers must stay unchanged. Prints a table
without secrets and exits non-zero on FAIL.
"""

import json
import os
import sys
import threading
import time
from unittest.mock import patch
from urllib.parse import quote

import frappe
from frappe.utils import add_days, today

from access_check import Client

SITE = "av.localhost"
SITES = "/home/frappe/frappe-bench/sites"
SALES = "sales@av-prototype.invalid"
PM = "pm@av-prototype.invalid"
COMPANY = "AV Prototype"
CUSTOMER = "Synthetic TP-03 Customer"
PARALLEL = 4
RACE_ROUNDS = 10
BLOCK_SECONDS = 3
METHOD = "/api/method/av_platform.av_platform.doctype.av_handover.av_handover.review_handover"
INJECTED = "TP-03 injected failure after Project insert"


def connect():
    os.chdir(SITES)
    frappe.init(site=SITE, sites_path=SITES)
    frappe.connect()
    frappe.set_user("Administrator")


def ensure_customer():
    from av_platform.demo import _guard

    _guard()
    if not frappe.db.exists("Customer", CUSTOMER):
        frappe.get_doc({"doctype": "Customer", "customer_name": CUSTOMER, "customer_type": "Company",
                        "customer_group": "Commercial", "territory": "Uzbekistan"}).insert()
    frappe.db.commit()  # CLI-only evidence: HTTP connections must see committed setup.


def new_handover(run, label):
    """A newer quotation of the TP-03 customer supersedes only earlier, already decided runs."""
    frappe.set_user("Administrator")
    marker = f"AV-TP03-{run}-{label}"
    quote = frappe.get_doc({
        "doctype": "Quotation", "title": marker, "quotation_to": "Customer",
        "party_name": CUSTOMER, "company": COMPANY, "currency": "USD", "conversion_rate": 1,
        "selling_price_list": "AV Prototype USD", "price_list_currency": "USD",
        "plc_conversion_rate": 1, "transaction_date": today(), "valid_till": add_days(today(), 30),
        "order_type": "Sales", "ignore_pricing_rule": 1,
        "items": [{"item_code": "AVP-M", "qty": 4, "rate": 2000},
                  {"item_code": "AVP-SERVICES", "qty": 1, "rate": 8000}],
        "terms": f"SYNTHETIC ONLY. {marker}. TP-03 concurrency and rollback check.",
    }).insert()
    quote.submit()
    frappe.set_user(SALES)
    try:
        handover = frappe.get_doc({
            "doctype": "AV Handover", "quotation": quote.name,
            "project_name": f"AV TP-03 {run} {label}", "project_manager": PM,
            "customer_approval_reference": f"SYNTHETIC: {marker} accepted.",
        }).insert()
        handover.submit()
    finally:
        frappe.set_user("Administrator")
    frappe.db.commit()
    return {"name": handover.name, "project_name": handover.project_name}


def state(handover):
    """Committed state as a fresh transaction of connection A sees it."""
    frappe.db.rollback()
    row = frappe.db.get_value("AV Handover", handover["name"], ["review_status", "project"],
                              as_dict=True)
    projects = frappe.get_all("Project", filters={"project_name": handover["project_name"]},
                              pluck="name")
    return row.review_status, row.project, projects


def others():
    frappe.db.rollback()
    handovers = [row for row in frappe.get_all(
        "AV Handover", fields=["name", "customer", "review_status", "project", "modified"],
        order_by="name") if row.customer != CUSTOMER]
    projects = [row for row in frappe.get_all(
        "Project", fields=["name", "customer", "status", "modified"], order_by="name")
        if row.customer != CUSTOMER]
    return json.dumps({"handovers": handovers, "projects": projects}, default=str, sort_keys=True)


def accept(client, name):
    started = time.monotonic()
    status, body = client.request("POST", METHOD, {"name": name, "decision": "accept"})
    try:
        payload = json.loads(body)
    except ValueError:
        payload = {}
    message = payload.get("message") if isinstance(payload.get("message"), dict) else {}
    detail = (payload.get("exception") or "").strip().splitlines()[-1:]
    return {"http": status, "status": message.get("status"), "project": message.get("project"),
            "error": " ".join([payload.get("exc_type") or ""] + detail).strip() or None,
            "seconds": round(time.monotonic() - started, 2)}


class Call(threading.Thread):
    def __init__(self, client, name, barrier=None):
        super().__init__(daemon=True)
        self.client, self.name, self.barrier, self.result = client, name, barrier, None

    def run(self):
        if self.barrier:
            self.barrier.wait()
        self.result = accept(self.client, self.name)


def short(result):
    return f"HTTP {result['http']} {result['status'] or result['error']} {result['seconds']}s"


def review_with_injected_failure(name):
    """Connection A fails after inserting the Project; its transaction stays open."""
    from av_platform.av_platform.doctype.av_handover.av_handover import (
        AVHandover,
        review_handover,
    )

    attempted = {}

    def fail(doc):
        attempted["project"] = doc.project
        raise frappe.ValidationError(INJECTED)

    frappe.set_user(PM)
    with patch.object(AVHandover, "before_update_after_submit", autospec=True, side_effect=fail):
        try:
            review_handover(name, "accept")
        except frappe.ValidationError as error:
            if INJECTED not in str(error):
                raise
    return attempted.get("project")


def race(run, password):
    """Smoke test over the real web stack; C5 is the deterministic form of this race.

    The losers fail only when their transaction snapshot predates the winner's commit, which
    happened mostly on a freshly started backend, so a passing C1 alone proves little.
    """
    failed = []
    for round_number in range(1, RACE_ROUNDS + 1):
        handover = new_handover(run, f"C1-{round_number}")
        clients = [Client(PM, password) for _ in range(PARALLEL)]
        barrier = threading.Barrier(PARALLEL)
        calls = [Call(client, handover["name"], barrier) for client in clients]
        for call in calls:
            call.start()
        for call in calls:
            call.join()
        review, project, projects = state(handover)
        results = [call.result for call in calls]
        if not (review == "Accepted" and projects == [project]
                and all(r["http"] == 200 and r["project"] == project for r in results)):
            failed.append(f"round {round_number}: {len(projects)} project, handover {review}, "
                          + ", ".join(short(r) for r in results))
    observed = "; ".join(failed) if failed else (
        f"{RACE_ROUNDS} rounds: one Project each, all {PARALLEL} callers HTTP 200 Accepted")
    return ("C1", f"{PARALLEL} simultaneous PM accepts over separate logins, {RACE_ROUNDS} rounds",
            "one Project; every caller gets the same accepted pair", observed, not failed)


def blocked_then_commit(run, password):
    from av_platform.av_platform.doctype.av_handover.av_handover import review_handover

    handover = new_handover(run, "C2")
    client = Client(PM, password)
    frappe.set_user(PM)
    first = review_handover(handover["name"], "accept")  # Row lock held, nothing committed.
    call = Call(client, handover["name"])
    call.start()
    call.join(BLOCK_SECONDS)
    waited = call.is_alive()
    frappe.db.commit()
    call.join()
    frappe.set_user("Administrator")
    review, project, projects = state(handover)
    result = call.result
    passed = (waited and review == "Accepted" and projects == [project] == [first["project"]]
              and result["http"] == 200 and result["project"] == project)
    observed = (f"B waited {'yes' if waited else 'no'}; {len(projects)} project; handover {review}; "
                f"B: {short(result)}")
    return ("C2", "A accepts and holds the lock; B (HTTP) accepts; A commits",
            "B waits, then returns A's project; one Project", observed, passed)


def blocked_then_rollback(run, password):
    handover = new_handover(run, "C3")
    client = Client(PM, password)
    attempted = review_with_injected_failure(handover["name"])
    call = Call(client, handover["name"])
    call.start()
    call.join(BLOCK_SECONDS)
    waited = call.is_alive()
    frappe.db.rollback()  # What Frappe's request handler does after an exception.
    call.join()
    frappe.set_user("Administrator")
    review, project, projects = state(handover)
    result = call.result
    passed = (bool(attempted) and waited and review == "Accepted" and projects == [project]
              and result["http"] == 200 and result["project"] == project)
    observed = (f"A inserted {attempted or 'nothing'} then failed; B waited "
                f"{'yes' if waited else 'no'}; {len(projects)} project; handover {review}; "
                f"B: {short(result)}")
    return ("C3", "A fails after Project insert while B (HTTP) waits; A rolls back",
            "B creates the only Project; no trace of A's attempt", observed, passed)


def failure_then_retry(run, password):
    handover = new_handover(run, "C4")
    attempted = review_with_injected_failure(handover["name"])
    frappe.db.rollback()
    frappe.set_user("Administrator")
    after_failure = state(handover)
    leftover = bool(attempted and frappe.db.exists("Project", attempted)
                    and frappe.db.get_value("Project", attempted, "project_name")
                    == handover["project_name"])
    client = Client(PM, password)
    status, body = client.request("GET", f"/api/resource/{quote('AV Handover')}/{handover['name']}")
    seen = json.loads(body).get("data", {}) if status == 200 else {}
    result = accept(client, handover["name"])
    review, project, projects = state(handover)
    passed = (bool(attempted) and after_failure == ("Pending", None, []) and not leftover
              and seen.get("review_status") == "Pending" and not seen.get("project")
              and result["http"] == 200 and review == "Accepted" and projects == [project]
              and result["project"] == project)
    observed = (f"after failure: {after_failure[0]}, {len(after_failure[2])} project, "
                f"HTTP read {seen.get('review_status')}; retry {short(result)}; "
                f"{len(projects)} project; handover {review}")
    return ("C4", "A fails after Project insert and rolls back; PM retries over HTTP",
            "no Project and Pending after failure; retry accepts once", observed, passed)


def _second_connection(name, out, ready):
    """Connection B in its own thread: take a read snapshot, then accept behind A's lock."""
    from av_platform.av_platform.doctype.av_handover.av_handover import review_handover

    frappe.init(site=SITE, sites_path=SITES)
    frappe.connect()
    frappe.set_user(PM)
    try:
        frappe.db.sql("select count(*) from `tabProject`")  # The snapshot starts with this read.
        ready.set()
        out["result"] = review_handover(name, "accept")
    except Exception as error:
        out["error"] = f"{type(error).__name__}: {error}"
    finally:
        ready.set()
        frappe.db.rollback()
        frappe.destroy()


def stale_snapshot(run, password):
    from av_platform.av_platform.doctype.av_handover.av_handover import review_handover

    handover = new_handover(run, "C5")
    frappe.set_user(PM)
    first = review_handover(handover["name"], "accept")  # Row lock held, nothing committed.
    out, ready = {}, threading.Event()
    thread = threading.Thread(target=_second_connection, args=(handover["name"], out, ready),
                              daemon=True)
    thread.start()
    ready.wait()
    thread.join(BLOCK_SECONDS)
    waited = thread.is_alive()
    frappe.db.commit()
    thread.join()
    frappe.set_user("Administrator")
    review, project, projects = state(handover)
    result = out.get("result") or {}
    passed = (waited and review == "Accepted" and projects == [project] == [first["project"]]
              and result.get("status") == "Accepted" and result.get("project") == project)
    observed = (f"B waited {'yes' if waited else 'no'}; {len(projects)} project; handover {review}; "
                f"B: {result.get('status') or out.get('error')}")
    return ("C5", "B reads (snapshot) before A commits its accept, then accepts behind A's lock",
            "B returns A's project; one Project", observed, passed)


def batch_keeps_writes(run, password):
    """Several reviews in one transaction: a refused review must not discard an earlier accept."""
    from av_platform.av_platform.doctype.av_handover.av_handover import review_handover

    done = new_handover(run, "C6-done")
    frappe.set_user(PM)
    review_handover(done["name"], "accept")
    frappe.db.commit()
    refused_one = new_handover(run, "C6-return")
    accepted = new_handover(run, "C6-accept")
    frappe.set_user(PM)
    first = review_handover(accepted["name"], "accept")
    try:
        review_handover(refused_one["name"], "return", "")  # Rolls back to its savepoint.
        refused = False
    except frappe.ValidationError:
        refused = True
    repeat = review_handover(done["name"], "accept")
    frappe.db.commit()
    frappe.set_user("Administrator")
    review, project, projects = state(accepted)
    passed = (refused and repeat["status"] == "Accepted" and review == "Accepted"
              and projects == [project] == [first["project"]])
    observed = (f"return without note refused: {'yes' if refused else 'no'}; earlier accept after "
                f"commit: {review}, {len(projects)} project")
    return ("C6", "One transaction: accept, refused return, repeated accept; commit",
            "the earlier accept and its Project persist", observed, passed)


def main():
    password = os.environ["AV_PM_PASSWORD"]
    connect()
    try:
        ensure_customer()
        run = frappe.generate_hash(length=6)
        print(f"TP-03 run {run}; Frappe {frappe.__version__}; customer {CUSTOMER}")
        before = others()
        rows = [scenario(run, password) for scenario in
                (race, blocked_then_commit, blocked_then_rollback, failure_then_retry,
                 stale_snapshot, batch_keeps_writes)]
        untouched = others() == before
        rows.append(("C7", "Records of other customers", "unchanged by C1-C6",
                     "unchanged" if untouched else "CHANGED", untouched))
    finally:
        frappe.destroy()
    print("| ID | Scenario | Expected | Observed | Result |")
    print("|---|---|---|---|---|")
    failures = 0
    for scenario_id, scenario, expected, observed, passed in rows:
        failures += not passed
        print(f"| {scenario_id} | {scenario} | {expected} | {observed} | "
              f"{'PASS' if passed else 'FAIL'} |")
    print(f"Failures: {failures}")
    sys.exit(1 if failures else 0)


if __name__ == "__main__":
    main()
