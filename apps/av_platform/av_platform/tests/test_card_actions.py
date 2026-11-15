import os
from datetime import timedelta
from unittest.mock import patch

import frappe
from frappe.tests import IntegrationTestCase
from frappe.utils import getdate, today

from av_platform.demo import seed
from av_platform.pm_api import (
    SUBJECT_MAX_LENGTH,
    assign_task,
    due_state,
    get_board,
    get_subtasks,
    get_task_detail,
    plain_text,
    rename_task,
    unassign_task,
)


class TestBoardCardActions(IntegrationTestCase):
    """BRD-1: actions and details on a board card."""

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
        frappe.db.savepoint("av_card_actions_case")
        self.pm = self.demo["pm_user"]
        self.worker = self._user(("Projects User",))
        self.outsider = self._user(("Projects User",))
        self.project = self._project([self.pm, self.worker])
        self.task = self._task(self.project, "Mount displays")

    def tearDown(self):
        frappe.set_user("Administrator")
        frappe.db.rollback(save_point="av_card_actions_case")
        super().tearDown()

    def _user(self, roles):
        email = "card-" + frappe.generate_hash(length=8) + "@av-prototype.invalid"
        frappe.get_doc({"doctype": "User", "email": email, "first_name": "Card test",
                        "send_welcome_email": 0, "roles": [{"role": r} for r in roles]}).insert()
        return email

    def _project(self, users):
        return frappe.get_doc({
            "doctype": "Project", "project_name": "Card test " + frappe.generate_hash(length=8),
            "company": "AV Prototype", "status": "Open", "users": [{"user": u} for u in users],
        }).insert().name

    def _task(self, project, subject, **values):
        return frappe.get_doc({"doctype": "Task", "subject": subject, "project": project,
                               **values}).insert().name

    def _todo(self, task, user):
        frappe.get_doc({"doctype": "ToDo", "allocated_to": user, "reference_type": "Task",
                        "reference_name": task, "status": "Open",
                        "description": "Synthetic assignment"}).insert(ignore_permissions=True)

    def _modified(self, task):
        return str(frappe.db.get_value("Task", task, "modified"))

    def _open_assignees(self, task):
        return frappe.get_all("ToDo", filters={"reference_type": "Task", "reference_name": task,
                                               "status": "Open"}, pluck="allocated_to")

    def _card(self, task):
        return next(t for t in get_board(self.project)["tasks"] if t["name"] == task)

    # Card details

    def test_due_state_uses_server_day(self):
        day = getdate("2026-11-14")
        self.assertEqual(due_state("2026-11-13", "Open", day), "overdue")
        self.assertEqual(due_state("2026-11-14 18:00:00", "Working", day), "today")
        self.assertEqual(due_state("2026-11-16", "Open", day), "soon")
        self.assertIsNone(due_state("2026-11-17", "Open", day))
        self.assertIsNone(due_state("2026-11-01", "Completed", day))
        self.assertIsNone(due_state(None, "Open", day))

    def test_card_shows_due_state_comments_and_subtasks(self):
        frappe.db.set_value("Task", self.task, "exp_end_date", today())
        frappe.get_doc("Task", self.task).add_comment("Comment", "Cable route agreed")
        frappe.get_doc("Task", self.task).add_comment("Info", "System note is not a comment")
        frappe.db.set_value("Task", self.task, "is_group", 1)
        done =self._task(self.project, "Bracket A", parent_task=self.task)
        self._task(self.project, "Bracket B", parent_task=self.task)
        cancelled = self._task(self.project, "Bracket C", parent_task=self.task)
        frappe.db.set_value("Task", done, "status", "Completed")
        frappe.db.set_value("Task", cancelled, "status", "Cancelled")

        frappe.set_user(self.pm)
        card = self._card(self.task)
        self.assertEqual(card["due_state"], "today")
        self.assertEqual(card["comments"], 1)
        self.assertEqual(card["subtasks"], {"done": 1, "total": 2})
        self.assertIsNone(self._card(done)["subtasks"])

    def test_subtasks_hide_works_the_user_cannot_read(self):
        # The outsider is not a project member and sees only the works assigned to them.
        frappe.db.set_value("Task", self.task, "is_group", 1)
        visible = self._task(self.project, "Visible step", parent_task=self.task)
        hidden = self._task(self.project, "Hidden step", parent_task=self.task)
        for task in (self.task, visible):
            self._todo(task, self.outsider)

        frappe.set_user(self.outsider)
        card = next(t for t in get_board()["tasks"] if t["name"] == self.task)
        self.assertEqual(card["subtasks"], {"done": 0, "total": 1})
        names = [t["name"] for t in get_subtasks(self.task)["tasks"]]
        self.assertEqual(names, [visible])
        self.assertNotIn(hidden, names)

    def test_subtasks_of_hidden_task_are_refused(self):
        hidden = self._task(self._project([]), "Hidden parent")
        frappe.set_user(self.worker)
        with self.assertRaises(frappe.PermissionError):
            get_subtasks(hidden)

    def test_board_lists_project_members_and_assign_right(self):
        frappe.set_user(self.worker)
        board = get_board(self.project)
        project = next(p for p in board["projects"] if p["name"] == self.project)
        self.assertEqual([m["name"] for m in project["members"]], [self.pm, self.worker])
        self.assertFalse(board["can_assign_others"])
        frappe.set_user(self.pm)
        self.assertTrue(get_board(self.project)["can_assign_others"])

    # Rename

    def test_rename_trims_and_saves(self):
        frappe.set_user(self.worker)
        result = rename_task(self.task, "  Mount   displays, room 2 ", self._modified(self.task))
        self.assertTrue(result["ok"])
        self.assertEqual(result["task"]["subject"], "Mount displays, room 2")
        self.assertEqual(frappe.db.get_value("Task", self.task, "subject"), "Mount displays, room 2")

    def test_rename_rejects_empty_or_long_subject(self):
        frappe.set_user(self.worker)
        for subject in ("   ", "x" * (SUBJECT_MAX_LENGTH + 1)):
            result = rename_task(self.task, subject, self._modified(self.task))
            self.assertEqual(result["code"], "invalid_subject")
        self.assertEqual(frappe.db.get_value("Task", self.task, "subject"), "Mount displays")

    def test_rename_of_stale_card_is_a_conflict(self):
        stale = self._modified(self.task)
        frappe.db.set_value("Task", self.task, "description", "Changed elsewhere")
        frappe.set_user(self.worker)
        result = rename_task(self.task, "New name", stale)
        self.assertEqual(result["code"], "conflict")
        self.assertEqual(result["task"]["subject"], "Mount displays")

    def test_rename_cancelled_task_is_refused(self):
        frappe.db.set_value("Task", self.task, "status", "Cancelled")
        frappe.set_user(self.pm)
        self.assertEqual(rename_task(self.task, "New", self._modified(self.task))["code"], "task_closed")

    def test_outsider_cannot_rename_or_assign(self):
        frappe.set_user(self.outsider)
        with self.assertRaises(frappe.PermissionError):
            rename_task(self.task, "New", self._modified(self.task))
        with self.assertRaises(frappe.PermissionError):
            assign_task(self.task)

    # Take and assign

    def test_worker_takes_task_once(self):
        frappe.set_user(self.worker)
        first = assign_task(self.task)
        second = assign_task(self.task)
        self.assertTrue(first["ok"] and second["ok"])
        self.assertEqual([a["name"] for a in second["task"]["assignees"]], [self.worker])
        self.assertEqual(self._open_assignees(self.task), [self.worker])

    def test_worker_cannot_assign_or_unassign_others(self):
        frappe.set_user(self.worker)
        self.assertEqual(assign_task(self.task, self.pm)["code"], "assign_forbidden")
        frappe.set_user(self.pm)
        assign_task(self.task)
        frappe.set_user(self.worker)
        self.assertEqual(unassign_task(self.task, self.pm)["code"], "assign_forbidden")
        self.assertEqual(self._open_assignees(self.task), [self.pm])

    def test_lead_assigns_project_member(self):
        frappe.set_user(self.pm)
        result = assign_task(self.task, self.worker)
        self.assertTrue(result["ok"])
        self.assertEqual(self._open_assignees(self.task), [self.worker])
        frappe.set_user(self.worker)
        self.assertTrue(unassign_task(self.task)["ok"])
        self.assertEqual(self._open_assignees(self.task), [])

    def test_non_member_cannot_be_assigned_or_get_shared_access(self):
        frappe.set_user(self.pm)
        result = assign_task(self.task, self.outsider)
        self.assertEqual(result["code"], "assignee_not_member")
        self.assertEqual(self._open_assignees(self.task), [])
        self.assertFalse(frappe.db.exists("DocShare", {"share_doctype": "Task", "share_name": self.task,
                                                       "user": self.outsider}))

    def test_assignment_keeps_task_version(self):
        before = self._modified(self.task)
        frappe.set_user(self.worker)
        assign_task(self.task)
        self.assertEqual(self._modified(self.task), before)

    def test_seeded_board_shows_card_details(self):
        frappe.set_user(self.pm)
        board = get_board(self.demo["board_project"])
        cards = {t["subject"]: t for t in board["tasks"]}
        self.assertEqual(cards["Монтаж дисплеев"]["subtasks"]["total"], 3)
        self.assertGreaterEqual(cards["Схема видеотракта"]["comments"], 1)
        project = next(p for p in board["projects"] if p["name"] == self.demo["board_project"])
        self.assertIn("installer@av-prototype.invalid", [m["name"] for m in project["members"]])

    def test_soon_is_two_days(self):
        frappe.db.set_value("Task", self.task, "exp_end_date", getdate(today()) + timedelta(days=2))
        frappe.set_user(self.pm)
        self.assertEqual(self._card(self.task)["due_state"], "soon")

    # Task side panel (BRD-2)

    def test_plain_text_drops_markup_and_keeps_lines(self):
        self.assertEqual(plain_text("<div><p>Route <b>cable</b></p><p>A &amp; B&nbsp;</p></div>"),
                         "Route cable\nA & B")
        self.assertEqual(plain_text("<script>alert(1)</script>"), "alert(1)")
        self.assertIsNone(plain_text("<p><br></p>"))
        self.assertIsNone(plain_text(None))

    def test_task_detail_returns_card_description_comments_and_subtasks(self):
        frappe.db.set_value("Task", self.task, {"description": "<p>Route <b>cable</b></p>",
                                                "is_group": 1})
        doc = frappe.get_doc("Task", self.task)
        doc.add_comment("Comment", "<p>Cable route agreed</p>")
        doc.add_comment("Info", "System note is not a comment")
        step = self._task(self.project, "Bracket A", parent_task=self.task)

        frappe.set_user(self.pm)
        detail = get_task_detail(self.task)
        self.assertEqual(detail["task"]["name"], self.task)
        self.assertEqual(detail["task"]["subject"], "Mount displays")
        self.assertEqual(detail["description"], "Route cable")
        self.assertEqual([c["text"] for c in detail["comments"]], ["Cable route agreed"])
        self.assertFalse(detail["comments_truncated"])
        self.assertEqual([t["name"] for t in detail["subtasks"]], [step])
        self.assertTrue(detail["project_readable"])
        self.assertEqual(detail["project_name"],
                         frappe.db.get_value("Project", self.project, "project_name"))
        self.assertEqual([m["name"] for m in detail["members"]], [self.pm, self.worker])
        self.assertTrue(detail["can_move"])
        self.assertTrue(detail["can_assign_others"])
        self.assertTrue(detail["stages"])

    def test_task_detail_shows_unknown_as_none(self):
        frappe.set_user(self.worker)
        detail = get_task_detail(self.task)
        self.assertIsNone(detail["description"])
        self.assertIsNone(detail["task"]["start"])
        self.assertIsNone(detail["task"]["end"])
        self.assertIsNone(detail["task"]["subtasks"])
        self.assertEqual(detail["comments"], [])
        self.assertFalse(detail["can_assign_others"])

    def test_task_detail_is_refused_without_read_permission(self):
        hidden = self._task(self._project([]), "Hidden work")
        frappe.set_user(self.outsider)
        with self.assertRaises(frappe.PermissionError):
            get_task_detail(self.task)
        frappe.set_user(self.worker)
        with self.assertRaises(frappe.PermissionError):
            get_task_detail(hidden)
        # A missing work gets the same answer as a hidden one.
        with self.assertRaises(frappe.PermissionError):
            get_task_detail("TASK-DOES-NOT-EXIST")

    def test_assignee_outside_project_reads_task_but_not_project(self):
        self._todo(self.task, self.outsider)
        frappe.set_user(self.outsider)
        detail = get_task_detail(self.task)
        self.assertEqual(detail["task"]["name"], self.task)
        self.assertFalse(detail["project_readable"])
        self.assertIsNone(detail["project_name"])
        self.assertEqual(detail["members"], [])
