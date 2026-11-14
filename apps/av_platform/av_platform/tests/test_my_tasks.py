import os
from datetime import date
from unittest.mock import patch

import frappe
from frappe.desk.form import assign_to
from frappe.tests import IntegrationTestCase
from frappe.utils import add_days, getdate, today

from av_platform.demo import seed
from av_platform.pm_api import due_bucket, get_my_tasks, move_task


class TestDueBucket(IntegrationTestCase):
    def test_groups_follow_the_server_day(self):
        wednesday = date(2026, 11, 11)
        self.assertEqual(due_bucket(None, wednesday), "no_date")
        self.assertEqual(due_bucket("2026-11-10", wednesday), "overdue")
        self.assertEqual(due_bucket("2026-11-11", wednesday), "today")
        self.assertEqual(due_bucket("2026-11-15", wednesday), "week")
        self.assertEqual(due_bucket("2026-11-16", wednesday), "later")

    def test_week_ends_on_sunday(self):
        sunday = date(2026, 11, 15)
        self.assertEqual(due_bucket("2026-11-16", sunday), "later")


class TestMyTasksAPI(IntegrationTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        frappe.set_user("Administrator")
        with patch.dict(os.environ, {"AV_SALES_PASSWORD": "Synthetic-Tests-Only-382!",
                                     "AV_PM_PASSWORD": "Synthetic-Tests-Only-741!"}):
            cls.demo = seed()

    def setUp(self):
        super().setUp()
        frappe.set_user("Administrator")
        frappe.db.savepoint("av_my_tasks_case")
        self.pm = self.demo["pm_user"]
        self.project = self._project([self.pm])

    def tearDown(self):
        frappe.set_user("Administrator")
        frappe.db.rollback(save_point="av_my_tasks_case")
        super().tearDown()

    def _project(self, users):
        return frappe.get_doc({
            "doctype": "Project", "project_name": "My tasks test " + frappe.generate_hash(length=8),
            "company": "AV Prototype", "status": "Open", "users": [{"user": u} for u in users],
        }).insert().name

    def _task(self, subject, project=None, assignee=None, **values):
        name = frappe.get_doc({"doctype": "Task", "subject": subject,
                               "project": project or self.project, **values}).insert().name
        if assignee:
            assign_to.add({"assign_to": [assignee], "doctype": "Task", "name": name})
        return name

    def _user(self, roles=("Projects User",)):
        email = "worker-" + frappe.generate_hash(length=8) + "@av-prototype.invalid"
        frappe.get_doc({"doctype": "User", "email": email, "first_name": "Installer",
                        "send_welcome_email": 0, "roles": [{"role": r} for r in roles]}).insert()
        return email

    def _by_name(self, result):
        return {t["name"]: t for t in result["tasks"]}

    def test_mine_groups_assigned_open_works_by_due_date(self):
        now = getdate(today())
        overdue = self._task("Rack wiring", assignee=self.pm, exp_end_date=add_days(now, -2),
                             exp_start_date=add_days(now, -5))
        due_today = self._task("Display mounts", assignee=self.pm, exp_end_date=now)
        later = self._task("Commissioning", assignee=self.pm, exp_end_date=add_days(now, 30))
        undated = self._task("Label cables", assignee=self.pm)
        not_mine = self._task("Someone else's work")

        frappe.set_user(self.pm)
        result = get_my_tasks("mine")
        tasks = self._by_name(result)
        self.assertEqual(result["today"], str(now))
        self.assertEqual(tasks[overdue]["bucket"], "overdue")
        self.assertTrue(tasks[overdue]["is_overdue"])
        self.assertEqual(tasks[due_today]["bucket"], "today")
        self.assertEqual(tasks[later]["bucket"], "later")
        self.assertEqual(tasks[undated]["bucket"], "no_date")
        self.assertNotIn(not_mine, tasks)
        self.assertEqual(tasks[due_today]["stage"], "planned")
        self.assertIn({"name": self.project, "project_name": frappe.db.get_value(
            "Project", self.project, "project_name")}, result["projects"])

    def test_dated_works_come_before_undated(self):
        now = getdate(today())
        undated = self._task("No date yet", assignee=self.pm)
        dated = self._task("Has a date", assignee=self.pm, exp_end_date=add_days(now, 3))
        frappe.set_user(self.pm)
        order = [t["name"] for t in get_my_tasks("mine")["tasks"]]
        self.assertLess(order.index(dated), order.index(undated))

    def test_completed_cancelled_and_unassigned_works_are_left_out(self):
        done = self._task("Finished", assignee=self.pm)
        cancelled = self._task("Dropped", assignee=self.pm)
        removed = self._task("Reassigned away", assignee=self.pm)
        frappe.db.set_value("Task", cancelled, "status", "Cancelled")
        assign_to.remove("Task", removed, self.pm)
        frappe.set_user(self.pm)
        self.assertTrue(move_task(done, "done", str(frappe.db.get_value("Task", done, "modified")))["ok"])

        tasks = self._by_name(get_my_tasks("mine"))
        self.assertNotIn(done, tasks)
        self.assertNotIn(cancelled, tasks)
        self.assertNotIn(removed, tasks)

    def test_work_assigned_outside_member_projects_is_still_mine(self):
        foreign_project = self._project([])
        foreign = self._task("Help on another site", project=foreign_project, assignee=self.pm)
        frappe.set_user(self.pm)
        self.assertIn(foreign, self._by_name(get_my_tasks("mine")))

    def test_delegated_lists_works_the_user_assigned_to_others(self):
        installer = self._user()
        frappe.set_user(self.pm)
        delegated = self._task("Pull speaker cable", assignee=installer)
        own = self._task("PM's own check", assignee=self.pm)

        tasks = self._by_name(get_my_tasks("delegated"))
        self.assertIn(delegated, tasks)
        self.assertNotIn(own, tasks)
        self.assertEqual([a["name"] for a in tasks[delegated]["assignees"]], [installer])
        self.assertNotIn(delegated, self._by_name(get_my_tasks("mine")))

    def test_delegated_hides_works_of_projects_the_user_left(self):
        installer = self._user()
        frappe.set_user(self.pm)
        task = self._task("Left behind", assignee=installer)
        frappe.set_user("Administrator")
        project = frappe.get_doc("Project", self.project)
        project.users = []
        project.save()

        frappe.set_user(self.pm)
        self.assertNotIn(task, self._by_name(get_my_tasks("delegated")))

    def test_unknown_view_is_rejected(self):
        frappe.set_user(self.pm)
        with self.assertRaises(frappe.ValidationError):
            get_my_tasks("everyone")

    def test_role_without_task_access_is_refused(self):
        frappe.set_user(self.demo["sales_user"])
        with self.assertRaises(frappe.PermissionError):
            get_my_tasks("mine")
