"""TP-02: tasks and projects are open to their participants only, in every channel."""

import os
from unittest.mock import patch

import frappe
from frappe.desk.form import assign_to
from frappe.desk.search import search_link
from frappe.tests import IntegrationTestCase

from av_platform.demo import seed
from av_platform.pm_board import can_see_task


class TestProjectAccess(IntegrationTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        frappe.set_user("Administrator")
        cls.company = "AV Prototype"
        if not frappe.db.exists("Company", cls.company):
            with patch.dict(os.environ, {"AV_SALES_PASSWORD": "Synthetic-Tests-Only-382!",
                                         "AV_PM_PASSWORD": "Synthetic-Tests-Only-741!"}):
                seed()

    def setUp(self):
        super().setUp()
        frappe.set_user("Administrator")
        frappe.db.savepoint("av_project_access_case")
        self.member = self._user("Projects User", "AV Project Manager")
        self.outsider = self._user("Projects User", "AV Project Manager")
        self.assignee = self._user("Projects User")
        # ERPNext grants Task access to Projects User; Projects Manager adds every project.
        self.manager = self._user("Projects User", "Projects Manager")
        self.sales = self._user("Sales User", "AV Sales")
        self.project = self._project([self.member])
        self.task = self._task(self.project, "Rack wiring")
        self.other_task = self._task(self.project, "Speaker install")
        assign_to.add({"assign_to": [self.assignee], "doctype": "Task", "name": self.other_task})

    def tearDown(self):
        frappe.set_user("Administrator")
        frappe.db.rollback(save_point="av_project_access_case")
        super().tearDown()

    def _user(self, *roles):
        email = "access-" + frappe.generate_hash(length=8) + "@av-prototype.invalid"
        frappe.get_doc({"doctype": "User", "email": email, "first_name": "Access test",
                        "send_welcome_email": 0, "roles": [{"role": r} for r in roles]}).insert()
        return email

    def _project(self, users):
        return frappe.get_doc({
            "doctype": "Project", "project_name": "Access test " + frappe.generate_hash(length=8),
            "company": self.company, "status": "Open", "users": [{"user": u} for u in users],
        }).insert().name

    def _task(self, project, subject):
        return frappe.get_doc({"doctype": "Task", "subject": subject, "project": project}).insert().name

    def _lists(self, user):
        frappe.set_user(user)
        return self._names("Project"), self._names("Task")

    def _names(self, doctype):
        try:
            return set(frappe.get_list(doctype, pluck="name", limit_page_length=0))
        except frappe.PermissionError:  # The role has no access to the DocType at all.
            return set()

    def test_member_sees_project_and_its_tasks(self):
        projects, tasks = self._lists(self.member)
        self.assertIn(self.project, projects)
        self.assertTrue({self.task, self.other_task} <= tasks)
        self.assertTrue(frappe.has_permission("Task", "write", doc=self.task))

    def test_outsider_sees_nothing_in_list_form_api_or_search(self):
        projects, tasks = self._lists(self.outsider)
        self.assertNotIn(self.project, projects)
        self.assertFalse({self.task, self.other_task} & tasks)
        self.assertFalse(frappe.has_permission("Project", "read", doc=self.project))
        self.assertFalse(frappe.has_permission("Task", "read", doc=self.task))
        with self.assertRaises(frappe.PermissionError):
            frappe.client.get("Task", self.task)
        with self.assertRaises(frappe.PermissionError):
            frappe.client.get("Project", self.project)
        found = {row["value"] for row in search_link("Project", self.project.split("-")[0])}
        self.assertNotIn(self.project, found)
        # Report views and list counters go through the same permission query.
        self.assertEqual(frappe.client.get_count("Task", {"project": self.project}), 0)

    def test_desk_user_without_project_role_cannot_read_projects(self):
        # ERPNext gives the Desk User role read access to every project.
        projects, _ = self._lists(self.sales)
        self.assertNotIn(self.project, projects)
        self.assertFalse(frappe.has_permission("Project", "read", doc=self.project))

    def test_assignee_sees_assigned_task_only(self):
        projects, tasks = self._lists(self.assignee)
        self.assertIn(self.other_task, tasks)
        self.assertNotIn(self.task, tasks)
        self.assertNotIn(self.project, projects)
        self.assertTrue(can_see_task(frappe.get_doc("Task", self.other_task)))

    def test_projects_manager_sees_everything(self):
        projects, tasks = self._lists(self.manager)
        self.assertIn(self.project, projects)
        self.assertTrue({self.task, self.other_task} <= tasks)

    def test_outsider_cannot_create_task_in_foreign_project(self):
        frappe.set_user(self.outsider)
        with self.assertRaises(frappe.PermissionError):
            frappe.get_doc({"doctype": "Task", "subject": "Injected", "project": self.project}).insert()

    def test_task_cannot_be_moved_into_foreign_project(self):
        frappe.set_user("Administrator")
        foreign = self._project([self.outsider])
        frappe.set_user(self.member)
        doc = frappe.get_doc("Task", self.task)
        doc.project = foreign
        with self.assertRaises(frappe.PermissionError):
            doc.save()

    def test_outsider_cannot_add_self_to_project(self):
        # Same path as PUT /api/resource/Project: the sent document lists the sender as a member.
        doc = frappe.get_doc("Project", self.project)
        frappe.set_user(self.outsider)
        doc.append("users", {"user": self.outsider})
        with self.assertRaises(frappe.PermissionError):
            doc.save()
        self.assertNotIn(self.outsider, frappe.get_all("Project User", filters={"parent": self.project},
                                                        pluck="user"))

    def test_own_task_without_project_stays_visible_to_its_author(self):
        frappe.set_user(self.outsider)
        own = frappe.get_doc({"doctype": "Task", "subject": "Personal check"}).insert().name
        _, tasks = self._lists(self.outsider)
        self.assertIn(own, tasks)
        _, member_tasks = self._lists(self.member)
        self.assertNotIn(own, member_tasks)

    def test_attachments_of_foreign_tasks_are_not_listed(self):
        frappe.set_user("Administrator")
        file = frappe.get_doc({"doctype": "File", "file_name": "wiring.txt", "is_private": 1,
                               "content": b"SYNTHETIC wiring", "attached_to_doctype": "Task",
                               "attached_to_name": self.task}).insert().name
        frappe.set_user(self.outsider)
        self.assertNotIn(file, frappe.get_list("File", pluck="name", limit_page_length=0))
        frappe.set_user(self.member)
        self.assertIn(file, frappe.get_list("File", pluck="name", limit_page_length=0))
