import os
from datetime import date
from unittest.mock import patch

import frappe
from frappe.desk.form import assign_to
from frappe.tests import IntegrationTestCase
from frappe.utils import add_days, getdate, today

from av_platform.av_sales.doctype.av_handover.av_handover import review_handover
from av_platform.demo import seed
from av_platform.overview import (
    DIRECTOR_ROLE,
    _totals,
    deal_alert,
    get_overview,
    get_project,
    get_projects,
    project_reasons,
    project_status,
)
from av_platform.pm_api import move_task, rename_task

DAY = date(2026, 11, 11)


def task(name, status="Open", end=None, blocked=None, assignees=("pm@x",), group=0, milestone=0):
    return frappe._dict(name=name, subject=name, status=status, is_group=group, is_milestone=milestone,
                        av_block_reason=blocked, exp_end_date=end,
                        _assign=frappe.as_json(list(assignees)))


def codes(reasons):
    return {r["code"]: r["count"] for r in reasons}


class TestProjectStatus(IntegrationTestCase):
    def test_blocked_and_overdue_are_a_problem_with_every_reason(self):
        reasons = project_reasons([
            task("Mount", end="2026-11-20", blocked="No delivery date"),
            task("Wiring", end="2026-11-01"),
            task("Labels", end=None, assignees=()),
        ], DAY)
        self.assertEqual(codes(reasons), {"blocked": 1, "overdue": 1, "undated": 1, "unassigned": 1})
        self.assertEqual(project_status(reasons), "problem")

    def test_missing_plan_is_unknown_not_green(self):
        self.assertEqual(codes(project_reasons([], DAY)), {"no_works": 0})
        self.assertEqual(project_status(project_reasons([], DAY)), "unknown")
        undated = project_reasons([task("Survey"), task("Design")], DAY)
        self.assertEqual(codes(undated), {"no_dates": 2})
        self.assertEqual(project_status(undated), "unknown")

    def test_incomplete_data_is_a_risk(self):
        reasons = project_reasons([task("Survey", end="2026-11-12"), task("Design", assignees=())], DAY)
        self.assertEqual(codes(reasons), {"undated": 1, "unassigned": 1})
        self.assertEqual(project_status(reasons), "risk")

    def test_completed_works_do_not_prove_acceptance(self):
        reasons = project_reasons([task("Survey", status="Completed", end="2026-11-01")], DAY)
        self.assertEqual(codes(reasons), {"all_done": 1})
        self.assertEqual(project_status(reasons), "unknown")

    def test_on_plan_explains_a_close_milestone(self):
        reasons = project_reasons([
            task("Install", end="2026-11-14"),
            task("Handover milestone", end="2026-11-15", milestone=1),
            task("Old", status="Completed", end="2026-11-01"),
        ], DAY)
        self.assertEqual(codes(reasons), {"milestone_soon": 1})
        self.assertEqual(project_status(reasons), "on_plan")
        self.assertEqual(project_status(project_reasons([task("Install", end="2026-11-30")], DAY)),
                         "on_plan")

    def test_group_tasks_are_not_works(self):
        reasons = project_reasons([task("Displays", group=1, end="2026-11-30")], DAY)
        self.assertEqual(codes(reasons), {"no_works": 0})

    def test_deal_alerts_follow_validity_of_open_deals(self):
        self.assertEqual(deal_alert("issued", "2026-11-10", DAY), "expired")
        self.assertEqual(deal_alert("returned", "2026-12-11", DAY), "expiring")
        self.assertIsNone(deal_alert("issued", "2026-12-12", DAY))
        self.assertIsNone(deal_alert("accepted", "2026-11-10", DAY))
        self.assertIsNone(deal_alert("issued", None, DAY))

    def test_currencies_are_never_added_together(self):
        rows = [frappe._dict(grand_total=100, currency="USD"), frappe._dict(grand_total=50, currency="UZS"),
                frappe._dict(grand_total=10, currency="USD"), frappe._dict(grand_total=None, currency="USD")]
        self.assertEqual(_totals(rows), [{"currency": "USD", "amount": 110}, {"currency": "UZS", "amount": 50}])


class TestOverviewAPI(IntegrationTestCase):
    DIRECTOR = "av-overview-director@av-prototype.invalid"
    INSTALLER = "av-overview-installer@av-prototype.invalid"

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        frappe.set_user("Administrator")
        with patch.dict(os.environ, {"AV_SALES_PASSWORD": "Synthetic-Tests-Only-382!",
                                     "AV_PM_PASSWORD": "Synthetic-Tests-Only-741!"}):
            cls.demo = seed()
        if not frappe.db.exists("User", cls.DIRECTOR):
            frappe.get_doc({"doctype": "User", "email": cls.DIRECTOR, "first_name": "Director",
                            "send_welcome_email": 0,
                            "roles": [{"role": DIRECTOR_ROLE}]}).insert(ignore_permissions=True)
        if not frappe.db.exists("User", cls.INSTALLER):
            frappe.get_doc({"doctype": "User", "email": cls.INSTALLER, "first_name": "Installer",
                            "send_welcome_email": 0,
                            "roles": [{"role": "Projects User"}]}).insert(ignore_permissions=True)

    def setUp(self):
        super().setUp()
        frappe.set_user("Administrator")
        frappe.db.savepoint("av_overview_case")

    def tearDown(self):
        frappe.set_user("Administrator")
        frappe.db.rollback(save_point="av_overview_case")
        super().tearDown()

    def _project(self, name, users=()):
        return frappe.get_doc({
            "doctype": "Project", "project_name": f"{name} {frappe.generate_hash(length=6)}",
            "company": "AV Prototype", "status": "Open", "users": [{"user": u} for u in users],
        }).insert().name

    def _task(self, project, subject, assignee=None, **values):
        name = frappe.get_doc({"doctype": "Task", "subject": subject, "project": project,
                               **values}).insert().name
        if assignee:
            assign_to.add({"assign_to": [assignee], "doctype": "Task", "name": name})
        return name

    def _quotation(self, customer, valid_till, submit=True, rate=1000):
        quote = frappe.get_doc({
            "doctype": "Quotation", "quotation_to": "Customer", "party_name": customer,
            "company": "AV Prototype", "currency": "USD", "conversion_rate": 1,
            "selling_price_list": "AV Prototype USD", "price_list_currency": "USD",
            "plc_conversion_rate": 1, "transaction_date": add_days(valid_till, -40),
            "valid_till": valid_till, "order_type": "Sales", "ignore_pricing_rule": 1,
            "items": [{"item_code": "AVP-SERVICES", "qty": 1, "rate": rate}],
        }).insert()
        if submit:
            quote.submit()
        return quote.name

    def _customer(self):
        return frappe.get_doc({"doctype": "Customer", "customer_name": "Overview test " + frappe.generate_hash(length=6),
                               "customer_type": "Company", "customer_group": "Commercial",
                               "territory": "Uzbekistan"}).insert().name

    def _row(self, result, project):
        return next(r for r in result["projects"]["rows"] if r["name"] == project)

    def _handover_project(self):
        """The project of the demo handover, accepted by its PM inside this test's savepoint."""
        frappe.set_user(self.demo["pm_user"])
        review_handover(self.demo["handover"], "accept")
        frappe.set_user("Administrator")
        return frappe.db.get_value("AV Handover", self.demo["handover"], "project")

    def test_home_is_for_director_and_pm_and_only_the_director_sees_the_funnel(self):
        for user in (self.demo["sales_user"], self.INSTALLER):
            frappe.set_user(user)
            with self.assertRaises(frappe.PermissionError, msg=user):
                get_overview()
        frappe.set_user(self.demo["pm_user"])
        home = get_overview()
        self.assertIsNone(home["funnel"])
        self.assertIsNotNone(home["my_tasks"])
        self.assertTrue(home["money_visible"])
        frappe.set_user(self.DIRECTOR)
        self.assertIsNotNone(get_overview()["funnel"])

    def test_register_lists_only_readable_projects_and_marks_mine(self):
        pm = self.demo["pm_user"]
        member = self._project("Register member", users=[pm])
        hidden = self._project("Register hidden")
        frappe.set_user(pm)
        rows = {r["name"]: r for r in get_projects()["projects"]["rows"]}
        self.assertIn(member, rows)
        self.assertTrue(rows[member]["mine"])
        self.assertEqual([m["name"] for m in rows[member]["team"]], [pm])
        self.assertNotIn(hidden, rows)
        frappe.set_user(self.DIRECTOR)
        rows = {r["name"]: r for r in get_projects()["projects"]["rows"]}
        self.assertIn(hidden, rows)
        self.assertFalse(rows[member]["mine"])

    def test_money_is_hidden_from_users_who_cannot_read_the_handover(self):
        project = self._handover_project()
        doc = frappe.get_doc("Project", project)
        doc.append("users", {"user": self.INSTALLER})
        doc.save()
        frappe.set_user(self.INSTALLER)
        register = get_projects()
        self.assertFalse(register["money_visible"])
        self.assertIsNone(self._row(register, project)["basis"])
        card = get_project(project)
        self.assertFalse(card["money_visible"])
        self.assertIsNone(card["project"]["basis"])
        self.assertIsNone(card["project"]["handover"])
        frappe.set_user(self.demo["pm_user"])
        basis = self._row(get_projects(), project)["basis"]
        self.assertEqual(basis["amount"], self.demo["accepted_value"])

    def test_project_card_refuses_hidden_and_missing_projects_alike(self):
        hidden = self._project("Card hidden")
        accepted = self._handover_project()
        frappe.set_user(self.demo["pm_user"])
        for name in (hidden, "PROJ-DOES-NOT-EXIST", ""):
            with self.assertRaises(frappe.PermissionError, msg=name):
                get_project(name)
        # Sales handed the project over but has no screen for it.
        frappe.set_user(self.demo["sales_user"])
        with self.assertRaises(frappe.PermissionError):
            get_project(accepted)

    def test_project_card_lists_every_obstacle_milestone_and_my_works(self):
        pm = self.demo["pm_user"]
        now = getdate(today())
        project = self._project("Card details", users=[pm])
        blocked = self._task(project, "Speakers", assignee=pm, exp_end_date=add_days(now, 5),
                             av_block_reason="No delivery date")
        overdue = self._task(project, "Cabling", assignee=self.DIRECTOR, exp_end_date=add_days(now, -2))
        milestone = self._task(project, "Handover to client", assignee=pm, is_milestone=1,
                               exp_end_date=add_days(now, 20))
        done = self._task(project, "Survey", assignee=pm, exp_end_date=add_days(now, -9))
        frappe.db.set_value("Task", done, "status", "Completed")
        frappe.set_user(pm)
        card = get_project(project)
        self.assertEqual(card["project"]["status"], "problem")
        self.assertEqual([(o["name"], o["kind"]) for o in card["obstacles"]],
                         [(overdue, "overdue"), (blocked, "blocked")])
        self.assertEqual([m["name"] for m in card["milestones"]], [milestone])
        self.assertEqual({w["name"] for w in card["my_works"]}, {blocked, milestone})
        self.assertEqual(len(card["works"]), 4)
        self.assertEqual(card["project"]["works"], {"done": 1, "total": 4})
        self.assertIsNone(next(w for w in card["works"] if w["name"] == done)["bucket"])

    def test_project_card_summarizes_works_beyond_the_display_limit(self):
        pm = self.demo["pm_user"]
        now = getdate(today())
        project = self._project("Card beyond display limit", users=[pm])
        completed = []
        for index in range(2):
            name = self._task(project, f"Completed work {index}", assignee=pm,
                              exp_end_date=add_days(now, index + 1))
            frappe.db.set_value("Task", name, "status", "Completed")
            completed.append(name)
        late = self._task(project, "Blocked acceptance milestone", assignee=pm,
                          exp_end_date=add_days(now, 3), is_milestone=1,
                          av_block_reason="Client access is not confirmed")
        frappe.set_user(pm)
        # A smaller cap exercises the production query and summary without hundreds of inserts.
        with patch("av_platform.overview.CARD_TASK_LIMIT", 2):
            card = get_project(project)
        self.assertTrue(card["works_truncated"])
        self.assertEqual([w["name"] for w in card["works"]], completed)
        self.assertEqual(card["project"]["works"], {"done": 2, "total": 3})
        self.assertEqual(card["project"]["status"], "problem")
        self.assertEqual(codes(card["project"]["reasons"]), {"blocked": 1, "milestone_soon": 1})
        self.assertEqual(card["project"]["obstacle"]["name"], late)
        self.assertEqual(card["project"]["next_milestone"]["name"], late)
        self.assertEqual([o["name"] for o in card["obstacles"]], [late])
        self.assertEqual([m["name"] for m in card["milestones"]], [late])
        self.assertEqual([w["name"] for w in card["my_works"]], [late])
        row = self._row(get_projects(), project)
        for field in ("works", "status", "reasons", "obstacle", "next_milestone"):
            self.assertEqual(card["project"][field], row[field], field)

    def test_project_dashboard_counts_every_work_stage_milestone_and_person(self):
        pm = self.demo["pm_user"]
        idle = self.INSTALLER
        now = getdate(today())
        project = self._project("Card dashboard", users=[pm, idle])
        later = self._task(project, "Commissioning", assignee=pm, is_milestone=1,
                           exp_end_date=add_days(now, 30))
        passed = self._task(project, "Site survey", assignee=pm, is_milestone=1,
                            exp_end_date=add_days(now, -10))
        frappe.db.set_value("Task", passed, "status", "Completed")
        self._task(project, "Undated milestone", is_milestone=1)
        self._task(project, "Rack wiring", assignee=self.DIRECTOR, exp_end_date=add_days(now, 4))
        self._task(project, "Group", is_group=1)
        frappe.set_user(pm)
        with patch("av_platform.overview.CARD_TASK_LIMIT", 1):
            board = get_project(project)["dashboard"]
        stages = frappe.get_all("Task", filters={"project": project, "is_group": 0}, pluck="av_stage")
        self.assertEqual(sum(row["count"] for row in board["by_stage"]), 4)
        self.assertEqual({row["stage"] for row in board["by_stage"]}, {s or None for s in stages})
        self.assertEqual(board["milestones"], {"done": 1, "total": 3})
        self.assertEqual([d["name"] for d in board["key_dates"]], [passed, later])
        self.assertEqual(board["undated_milestones"], 1)
        load = {p["name"]: (p["open"], p["member"]) for p in board["people"]}
        # The completed milestone no longer loads the PM; a holder of an open work counts as a person.
        self.assertEqual(load, {pm: (1, True), self.DIRECTOR: (1, False), idle: (0, True)})

    def test_project_card_groups_do_not_use_the_works_display_limit(self):
        pm = self.demo["pm_user"]
        now = getdate(today())
        project = self._project("Card groups and display limit", users=[pm])
        self._task(project, "Work group", is_group=1, exp_end_date=add_days(now, 1))
        works = [self._task(project, f"Work {index}", assignee=pm,
                            exp_end_date=add_days(now, index + 2)) for index in range(2)]
        frappe.set_user(pm)
        with patch("av_platform.overview.CARD_TASK_LIMIT", 2):
            card = get_project(project)
        self.assertEqual([w["name"] for w in card["works"]], works)
        self.assertFalse(card["works_truncated"])
        self.assertEqual(card["project"]["works"], {"done": 0, "total": 2})

    def test_director_reads_everything_and_changes_nothing(self):
        project = self._project("Not a member")
        work = self._task(project, "Rack wiring")
        handover = frappe.get_doc("AV Handover", self.demo["handover"])
        frappe.set_user(self.DIRECTOR)
        self.assertTrue(frappe.has_permission("Project", "read", doc=project))
        self.assertTrue(frappe.has_permission("Task", "read", doc=work))
        self.assertTrue(frappe.has_permission("AV Handover", "read", doc=handover))
        self.assertIn(handover.name, frappe.get_list("AV Handover", pluck="name"))
        for doctype, name in (("Project", project), ("Task", work), ("AV Handover", handover.name),
                              ("Quotation", self.demo["quotations"]["Q2"])):
            self.assertFalse(frappe.has_permission(doctype, "write", doc=name), doctype)
        for doctype in ("Project", "Task", "Quotation", "AV Handover"):
            self.assertFalse(frappe.has_permission(doctype, "create"), doctype)
        doc = frappe.get_doc("Task", work)
        self.assertEqual(move_task(work, "in_progress", str(doc.modified))["code"], "no_permission")
        self.assertEqual(rename_task(work, "Renamed", str(doc.modified))["code"], "no_permission")
        frappe.set_user("Administrator")
        self.assertEqual(frappe.db.get_value("Task", work, "subject"), "Rack wiring")

    def _person_with(self, roles):
        email = "overview-" + frappe.generate_hash(length=8) + "@av-prototype.invalid"
        frappe.get_doc({"doctype": "User", "email": email, "first_name": "Combined",
                        "send_welcome_email": 0, "roles": [{"role": r} for r in roles]}).insert()
        return email

    def test_director_role_adds_no_write_to_other_roles(self):
        # Projects User may change tasks of member projects only; the director role must not lift that.
        lead = self._person_with([DIRECTOR_ROLE, "Projects User"])
        seller = self._person_with([DIRECTOR_ROLE, "AV Sales", "Sales User"])
        own = self._project("Member project", users=[lead])
        own_work = self._task(own, "Own work")
        foreign_work = self._task(self._project("Foreign project"), "Foreign work")
        frappe.set_user(lead)
        self.assertTrue(frappe.has_permission("Task", "read", doc=foreign_work))
        self.assertFalse(frappe.has_permission("Task", "write", doc=foreign_work))
        doc = frappe.get_doc("Task", foreign_work)
        self.assertEqual(move_task(foreign_work, "in_progress", str(doc.modified))["code"], "no_permission")
        self.assertTrue(frappe.has_permission("Task", "write", doc=own_work))
        # AV Sales may change its own handovers only, also together with the director role.
        handover = self.demo["handover"]
        frappe.set_user(seller)
        self.assertTrue(frappe.has_permission("AV Handover", "read", doc=handover))
        for ptype in ("write", "submit", "cancel", "delete"):
            self.assertFalse(frappe.has_permission("AV Handover", ptype, doc=handover), ptype)

    def test_other_roles_keep_their_limits(self):
        # The director's rules must not widen what a PM or Sales sees (TP-02).
        project = self._project("Hidden from PM")
        frappe.set_user(self.demo["pm_user"])
        self.assertNotIn(project, frappe.get_list("Project", pluck="name", limit_page_length=0))
        frappe.set_user(self.demo["sales_user"])
        self.assertFalse(frappe.has_permission("Project", "read", doc=project))

    def test_project_row_shows_obstacle_milestone_and_counts(self):
        pm = self.demo["pm_user"]
        now = getdate(today())
        project = self._project("Overview row", users=[pm])
        self._task(project, "Speakers", assignee=pm, exp_end_date=add_days(now, 6),
                   av_block_reason="No delivery date")
        self._task(project, "Cable schedule", assignee=pm, exp_end_date=add_days(now, -3),
                   exp_start_date=add_days(now, -9))
        self._task(project, "Site handover", assignee=pm, exp_end_date=add_days(now, 3), is_milestone=1)
        self._task(project, "Survey", assignee=pm, exp_end_date=add_days(now, -10),
                   exp_start_date=add_days(now, -12), status="Completed")
        frappe.set_user(self.DIRECTOR)
        row = self._row(get_overview(), project)
        self.assertEqual(row["status"], "problem")
        self.assertEqual(codes(row["reasons"]), {"blocked": 1, "overdue": 1, "milestone_soon": 1})
        self.assertEqual(row["obstacle"]["kind"], "blocked")
        self.assertEqual(row["obstacle"]["subject"], "Speakers")
        self.assertEqual(row["obstacle"]["reason"], "No delivery date")
        self.assertEqual([p["name"] for p in row["obstacle"]["assignees"]], [pm])
        self.assertEqual(row["next_milestone"]["subject"], "Site handover")
        self.assertEqual(row["works"], {"done": 1, "total": 4})
        # Without an accepted handover the PM and the basis are unknown, not empty values.
        self.assertIsNone(row["pm"])
        self.assertIsNone(row["basis"])

    def test_problem_projects_come_first(self):
        calm = self._project("A calm project")
        self._task(calm, "Install", assignee=self.demo["pm_user"], exp_end_date=add_days(today(), 20))
        late = self._project("Z late project")
        self._task(late, "Install", assignee=self.demo["pm_user"], exp_end_date=add_days(today(), -1),
                   exp_start_date=add_days(today(), -5))
        frappe.set_user(self.DIRECTOR)
        result = get_overview()
        order = [r["name"] for r in result["projects"]["rows"]]
        self.assertLess(order.index(late), order.index(calm))
        self.assertEqual(self._row(result, calm)["status"], "on_plan")
        self.assertGreaterEqual(result["status_counts"]["problem"], 1)

    def _pending_handover(self, pm, submit=True):
        """A handover of a fresh customer's only quotation, created by Sales for `pm`."""
        quote = self._quotation(self._customer(), add_days(today(), 30))
        frappe.set_user(self.demo["sales_user"])
        try:
            doc = frappe.get_doc({
                "doctype": "AV Handover", "quotation": quote,
                "project_name": "Decision " + frappe.generate_hash(length=6), "project_manager": pm,
                "customer_approval_reference": "SYNTHETIC: overview decision test.",
            }).insert()
            if submit:
                doc.submit()
        finally:
            frappe.set_user("Administrator")
        return doc.name

    def test_home_lists_only_packages_waiting_for_the_users_decision(self):
        pm = self._person_with(["AV Project Manager", "Projects User"])
        other_pm = self._person_with(["AV Project Manager", "Projects User"])
        waiting = self._pending_handover(pm)
        draft = self._pending_handover(pm, submit=False)
        foreign = self._pending_handover(other_pm)
        frappe.set_user(pm)
        decisions = get_overview()["decisions"]
        self.assertEqual([i["name"] for i in decisions["items"]], [waiting])
        self.assertEqual(decisions["total"], 1)
        self.assertNotIn(draft, [i["name"] for i in decisions["items"]])
        self.assertNotIn(foreign, [i["name"] for i in decisions["items"]])
        item = decisions["items"][0]
        doc = frappe.get_doc("AV Handover", waiting)
        self.assertEqual(item["quotation"], doc.quotation)
        self.assertEqual(item["customer"], frappe.db.get_value("Customer", doc.customer, "customer_name"))
        self.assertEqual(item["value"], {"amount": doc.accepted_value, "currency": doc.currency})
        self.assertEqual(item["submitted_by"]["name"], self.demo["sales_user"])
        self.assertIsNotNone(item["submitted_on"])
        # A decided package no longer waits.
        review_handover(waiting, "return", "SYNTHETIC: correct the scope.")
        self.assertEqual(get_overview()["decisions"], {"items": [], "total": 0})
        # The other PM's package is listed for that PM only.
        frappe.set_user(other_pm)
        self.assertEqual([i["name"] for i in get_overview()["decisions"]["items"]], [foreign])

    def test_users_who_do_not_decide_on_handovers_get_no_section(self):
        self._pending_handover(self.demo["pm_user"])
        manager = self._person_with(["Projects Manager", "Projects User"])
        # The director reads every handover but is not the assigned PM and does not decide.
        frappe.set_user(self.DIRECTOR)
        self.assertIsNone(get_overview()["decisions"])
        # A Projects Manager reaches the home page but cannot review handovers.
        frappe.set_user(manager)
        self.assertIsNone(get_overview()["decisions"])

    def test_decision_total_does_not_depend_on_the_display_limit(self):
        pm = self._person_with(["AV Project Manager", "Projects User"])
        first = self._pending_handover(pm)
        self._pending_handover(pm)
        self._pending_handover(pm)
        frappe.set_user(pm)
        with patch("av_platform.overview.DECISIONS_SHOWN", 2):
            decisions = get_overview()["decisions"]
        self.assertEqual(decisions["total"], 3)
        self.assertEqual(len(decisions["items"]), 2)
        # The package that has waited longest comes first.
        self.assertEqual(decisions["items"][0]["name"], first)

    def test_funnel_counts_current_versions_and_flags_expired_deals(self):
        customer = frappe.db.get_value("Quotation", self.demo["quotations"]["Q2"], "party_name")
        revision = self._quotation(customer, add_days(today(), 30), submit=False)
        expired = self._quotation(self._customer(), add_days(today(), -1))
        frappe.set_user(self.DIRECTOR)
        funnel = get_overview()["funnel"]
        stages = {s["stage"]: s for s in funnel["stages"]}
        attention = {d["name"]: d for d in funnel["attention"]}
        # Q1 is an older version of the same deal and Q2 waits for the PM: one deal, not two.
        self.assertGreaterEqual(stages["handover"]["count"], 1)
        self.assertGreaterEqual(funnel["revisions"], 1)
        listed = {d["name"] for d in funnel["attention"]}
        self.assertNotIn(self.demo["quotations"]["Q1"], listed)
        self.assertNotIn(revision, listed)
        self.assertEqual(attention[expired]["alert"], "expired")
        self.assertEqual(attention[expired]["group"], "issued")
        for stage in funnel["stages"]:
            self.assertEqual(len({t["currency"] for t in stage["totals"]}), len(stage["totals"]))
