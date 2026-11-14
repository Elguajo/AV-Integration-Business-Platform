import os
from unittest.mock import patch

import frappe
from frappe.tests import IntegrationTestCase

from av_platform.demo import BOARD_TASKS, seed
from av_platform.pm_api import get_board, move_task


class TestProjectBoardAPI(IntegrationTestCase):
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
        frappe.db.savepoint("av_pm_api_case")
        self.pm = self.demo["pm_user"]
        self.project = self._project([self.pm])
        self.task = self._task(self.project, "Mount displays")

    def tearDown(self):
        frappe.set_user("Administrator")
        frappe.db.rollback(save_point="av_pm_api_case")
        super().tearDown()

    def _project(self, users):
        return frappe.get_doc({
            "doctype": "Project", "project_name": "PM board test " + frappe.generate_hash(length=8),
            "company": "AV Prototype", "status": "Open", "users": [{"user": u} for u in users],
        }).insert().name

    def _task(self, project, subject, **values):
        return frappe.get_doc({"doctype": "Task", "subject": subject, "project": project,
                               **values}).insert().name

    def _pm_user(self, roles=("Projects User", "AV Project Manager")):
        email = "pm-" + frappe.generate_hash(length=8) + "@av-prototype.invalid"
        frappe.get_doc({"doctype": "User", "email": email, "first_name": "Other PM",
                        "send_welcome_email": 0, "roles": [{"role": r} for r in roles]}).insert()
        return email

    def _move(self, task, stage, expected=None):
        modified = expected or str(frappe.db.get_value("Task", task, "modified"))
        return move_task(task, stage, modified)

    def test_new_task_starts_in_first_stage_for_its_status(self):
        self.assertEqual(frappe.db.get_value("Task", self.task, "av_stage"), "planned")

    def test_board_shows_member_projects_only(self):
        hidden_project = self._project([])
        hidden_task = self._task(hidden_project, "Hidden work")
        frappe.set_user(self.pm)
        board = get_board()
        names = {t["name"] for t in board["tasks"]}
        self.assertIn(self.task, names)
        self.assertNotIn(hidden_task, names)
        self.assertNotIn(hidden_project, {p["name"] for p in board["projects"]})
        self.assertEqual([s["name"] for s in board["stages"]],
                         ["planned", "ready", "in_progress", "review", "done"])
        with self.assertRaises(frappe.PermissionError):
            get_board(hidden_project)

    def test_seeded_board_project_is_visible_to_pm(self):
        frappe.set_user(self.pm)
        board = get_board(self.demo["board_project"])
        # seed() keeps cards that people already moved, so check content, not column coverage.
        self.assertTrue({row[0] for row in BOARD_TASKS} <= {t["subject"] for t in board["tasks"]})
        enabled = {s["name"] for s in board["stages"]}
        self.assertTrue(all(t["stage"] in enabled for t in board["tasks"]))
        self.assertTrue(any(t["block_reason"] for t in board["tasks"]))

    def test_move_changes_stage_and_erpnext_status(self):
        frappe.set_user(self.pm)
        result = self._move(self.task, "in_progress")
        self.assertTrue(result["ok"])
        self.assertEqual(result["task"]["stage"], "in_progress")
        self.assertEqual(frappe.db.get_value("Task", self.task, "status"), "Working")
        self._move(self.task, "review")
        self.assertEqual(frappe.db.get_value("Task", self.task, "status"), "Pending Review")

    def test_repeated_move_is_idempotent(self):
        frappe.set_user(self.pm)
        first = self._move(self.task, "ready")
        stale = first["task"]["modified"]
        again = move_task(self.task, "ready", "an outdated timestamp")
        self.assertTrue(again["ok"])
        self.assertEqual(str(frappe.db.get_value("Task", self.task, "modified")), stale)

    def test_concurrent_change_is_reported_not_overwritten(self):
        frappe.set_user(self.pm)
        result = move_task(self.task, "in_progress", "2000-01-01 00:00:00")
        self.assertEqual(result["code"], "conflict")
        self.assertEqual(frappe.db.get_value("Task", self.task, "av_stage"), "planned")

    def test_blocked_task_cannot_be_closed(self):
        frappe.db.set_value("Task", self.task, "av_block_reason", "Waiting for the rack")
        frappe.set_user(self.pm)
        result = self._move(self.task, "done")
        self.assertFalse(result["ok"])
        self.assertEqual(result["code"], "blocked")
        self.assertEqual(frappe.db.get_value("Task", self.task, "status"), "Open")
        self.assertTrue(self._move(self.task, "in_progress")["ok"])

    def test_open_dependency_prevents_closing(self):
        dependent = self._task(self.project, "Test the video path",
                               depends_on=[{"task": self.task}])
        frappe.set_user(self.pm)
        self.assertEqual(self._move(dependent, "done")["code"], "dependencies_open")
        self.assertTrue(self._move(self.task, "done")["ok"])
        self.assertTrue(self._move(dependent, "done")["ok"])
        self.assertEqual(frappe.db.get_value("Task", dependent, "status"), "Completed")

    def test_unknown_or_disabled_stage_is_rejected(self):
        frappe.set_user(self.pm)
        self.assertEqual(self._move(self.task, "no_such_stage")["code"], "unknown_stage")

    def test_cancelled_task_cannot_be_moved(self):
        frappe.db.set_value("Task", self.task, "status", "Cancelled")
        frappe.set_user(self.pm)
        self.assertEqual(self._move(self.task, "ready")["code"], "task_closed")

    def test_non_member_cannot_read_or_move(self):
        other = self._pm_user()
        frappe.set_user(other)
        self.assertNotIn(self.task, {t["name"] for t in get_board()["tasks"]})
        with self.assertRaises(frappe.PermissionError):
            self._move(self.task, "ready")
        with self.assertRaises(frappe.PermissionError):
            move_task("TASK-DOES-NOT-EXIST", "ready", "x")

    def test_assignee_outside_project_sees_assigned_task(self):
        from frappe.desk.form import assign_to

        other = self._pm_user()
        assign_to.add({"assign_to": [other], "doctype": "Task", "name": self.task})
        frappe.set_user(other)
        cards = {t["name"]: t for t in get_board()["tasks"]}
        self.assertIn(self.task, cards)
        self.assertIn(other, [a["name"] for a in cards[self.task]["assignees"]])
        self.assertTrue(self._move(self.task, "ready")["ok"])

    def test_role_without_task_access_is_refused(self):
        frappe.set_user(self.demo["sales_user"])
        with self.assertRaises(frappe.PermissionError):
            get_board()

    def test_status_changed_in_desk_moves_the_card(self):
        doc = frappe.get_doc("Task", self.task)
        doc.status = "Working"
        doc.save()
        self.assertEqual(frappe.db.get_value("Task", self.task, "av_stage"), "in_progress")

    def test_desk_completion_still_checks_dependencies(self):
        dependent = self._task(self.project, "Commission", depends_on=[{"task": self.task}])
        doc = frappe.get_doc("Task", dependent)
        doc.av_stage = "done"
        with self.assertRaises(frappe.ValidationError):
            doc.save()

    def test_overdue_status_keeps_the_column(self):
        self._move(self.task, "in_progress")
        frappe.db.set_value("Task", self.task, "status", "Overdue", update_modified=False)
        doc = frappe.get_doc("Task", self.task)
        doc.description = "touched"
        doc.save()
        self.assertEqual(frappe.db.get_value("Task", self.task, "av_stage"), "in_progress")
        self.assertEqual(frappe.db.get_value("Task", self.task, "status"), "Working")
