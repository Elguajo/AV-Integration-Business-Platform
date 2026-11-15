"""UI-05: the global header of the shell — search, the «+» menu and notifications — shows only
what the user may open, and never offers to create a project by hand (PRJ-01)."""

import os
from unittest.mock import patch

import frappe
from frappe import _
from frappe.desk.doctype.notification_log.notification_log import get_title_html, mark_all_as_read
from frappe.tests import IntegrationTestCase

from av_platform.demo import seed
from av_platform.shell import create_options, get_notifications, notification_line, search


class TestHeader(IntegrationTestCase):
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
        frappe.db.savepoint("av_header_case")
        self.member = self._user("Projects User", "AV Project Manager")
        self.outsider = self._user("Projects User", "AV Project Manager")
        self.sales = self._user("Sales User", "AV Sales")
        self.word = "Hdr" + frappe.generate_hash(length=8)
        self.project = frappe.get_doc({
            "doctype": "Project", "project_name": f"Header {self.word}", "company": self.company,
            "status": "Open", "users": [{"user": self.member}],
        }).insert().name

    def tearDown(self):
        frappe.set_user("Administrator")
        frappe.db.rollback(save_point="av_header_case")
        super().tearDown()

    def _user(self, *roles):
        email = "header-" + frappe.generate_hash(length=8) + "@av-prototype.invalid"
        frappe.get_doc({"doctype": "User", "email": email, "first_name": "Header test",
                        "send_welcome_email": 0, "roles": [{"role": r} for r in roles]}).insert()
        return email

    def _notify(self, user, subject, kind="Alert", document_type="Project", document_name=None):
        return frappe.get_doc({
            "doctype": "Notification Log", "for_user": user, "from_user": "Administrator",
            "type": kind, "subject": subject,
            "document_type": document_type, "document_name": document_name or self.project,
        }).insert(ignore_permissions=True).name

    def _task(self, subject, **values):
        return frappe.get_doc({"doctype": "Task", "subject": subject, "project": self.project,
                               **values}).insert().name

    def _tasks_found(self, text):
        return [r for r in search(text) if r["doctype"] == "Task"]

    def test_search_finds_works_of_the_user_projects(self):
        task = self._task(f"Монтаж акустики {self.word}")
        frappe.set_user(self.member)
        # The words of the UX review: lower case finds «Монтаж …».
        found = self._tasks_found(f"монтаж акустики {self.word}")
        self.assertEqual([r["name"] for r in found], [task])
        self.assertEqual(found[0]["title"], f"Монтаж акустики {self.word}")
        # The subtitle names the project, not its id.
        self.assertEqual(found[0]["subtitle"], f"Header {self.word}")
        # A user with the board opens the work in its side panel there.
        self.assertEqual(found[0]["href"], f"/av/board?task={frappe.utils.quote(task)}")
        self.assertEqual([r["name"] for r in self._tasks_found(task)], [task])

    def test_search_hides_works_of_other_projects(self):
        self._task(f"Монтаж дисплеев {self.word}")
        frappe.set_user(self.outsider)
        self.assertEqual(self._tasks_found(self.word), [])

    def test_search_shows_no_works_without_task_read_permission(self):
        self._task(f"Монтаж дисплеев {self.word}")
        self.assertFalse(frappe.has_permission("Task", "read", user=self.sales))
        frappe.set_user(self.sales)
        self.assertEqual(self._tasks_found(self.word), [])

    def test_search_skips_task_templates(self):
        frappe.get_doc({"doctype": "Task", "subject": f"Шаблон {self.word}", "is_template": 1}).insert()
        frappe.set_user("Administrator")
        self.assertEqual(self._tasks_found(self.word), [])

    def test_notification_lines_are_russian_and_built_from_fields(self):
        who = frappe.utils.get_fullname("Administrator")
        title = get_title_html("Монтаж акустики")
        cases = {
            # Subjects as Frappe 16 writes them (assign_to.notify_assignment, share, mentions).
            ("Assignment", "Task", _("{0} assigned a new task {1} {2} to you").format(
                frappe.bold(who), frappe.bold("Task"), title)):
                f"{who} назначил(а) вам работу «Монтаж акустики»",
            ("Assignment", "Task", _("Your assignment on {0} {1} has been removed by {2}").format(
                frappe.bold("Task"), title, frappe.bold(who))):
                f"{who} снял(а) ваше назначение на работу «Монтаж акустики»",
            ("Mention", "Project", _("{0} mentioned you in a comment in {1} {2}").format(
                frappe.bold(who), frappe.bold("Project"), title)):
                f"{who} упомянул(а) вас в комментарии к проекту «Монтаж акустики»",
            ("Share", "Quotation", _("{0} shared a document {1} {2} with you").format(
                frappe.bold(who), frappe.bold("Quotation"), title)):
                f"{who} открыл(а) вам доступ к предложению «Монтаж акустики»",
            # A doctype without a Russian noun goes without one.
            ("Assignment", "ToDo", f"<b>{who}</b> assigned a new task <b>ToDo</b> {title} to you"):
                f"{who} назначил(а) вам «Монтаж акустики»",
            # No title in the subject: the record id stands in.
            ("Share", "Task", "Shared"): f"{who} открыл(а) вам доступ к работе «TASK-0001»",
        }
        for (kind, doctype, subject), expected in cases.items():
            row = frappe._dict(type=kind, subject=subject, from_user="Administrator",
                               document_type=doctype, document_name="TASK-0001")
            self.assertEqual(notification_line(row), expected, kind)

    def test_unknown_notification_keeps_frappe_subject_as_text(self):
        for row in (
            frappe._dict(type="Alert", subject="<p>Rule <b>fired</b></p>", from_user="Administrator",
                         document_type="Project", document_name="P"),
            # A known type without a sender cannot say who did it.
            frappe._dict(type="Assignment", subject="<b>Someone</b> did it", from_user=None,
                         document_type="Task", document_name="T"),
        ):
            self.assertEqual(notification_line(row), frappe.utils.strip_html_tags(row.subject).strip())

    def test_bell_shows_the_russian_line(self):
        task = self._task(f"Монтаж дисплеев {self.word}")
        log = self._notify(self.member, _("{0} assigned a new task {1} {2} to you").format(
            frappe.bold("Administrator"), frappe.bold("Task"), get_title_html(f"Монтаж дисплеев {self.word}")),
            kind="Assignment", document_type="Task", document_name=task)
        frappe.set_user(self.member)
        item = next(i for i in get_notifications()["items"] if i["name"] == log)
        self.assertEqual(item["subject"], f"{frappe.utils.get_fullname('Administrator')} назначил(а) вам "
                                          f"работу «Монтаж дисплеев {self.word}»")
        self.assertEqual(item["href"], f"/av/board?task={frappe.utils.quote(task)}")

    def test_search_finds_a_readable_project_and_opens_it_in_the_shell(self):
        frappe.set_user(self.member)
        found = [r for r in search(self.word) if r["name"] == self.project]
        self.assertEqual(len(found), 1)
        self.assertEqual(found[0]["doctype"], "Project")
        self.assertEqual(found[0]["title"], f"Header {self.word}")
        self.assertEqual(found[0]["href"], f"/av/projects/{self.project}")

    def test_search_hides_projects_the_user_cannot_read(self):
        frappe.set_user(self.outsider)
        self.assertNotIn(self.project, {r["name"] for r in search(self.word)})

    def test_search_needs_two_characters_and_matches_literally(self):
        frappe.set_user("Administrator")
        self.assertEqual(search(" a "), [])
        # As wildcards %% and __ would match every record; as text they match none.
        self.assertEqual(search("%%"), [])
        self.assertEqual(search("__"), [])

    def test_search_opens_records_without_a_shell_screen_in_desk(self):
        frappe.set_user("Administrator")
        customer = frappe.get_doc({"doctype": "Customer", "customer_name": f"Client {self.word}",
                                   "customer_type": "Company"}).insert().name
        found = [r for r in search(self.word) if r["doctype"] == "Customer"]
        self.assertEqual([r["href"] for r in found], [f"/desk/customer/{frappe.utils.quote(customer)}"])

    def test_create_menu_never_offers_a_project(self):
        for user in ("Administrator", self.member, self.sales):
            self.assertNotIn("Project", {o["doctype"] for o in create_options(user, True)}, user)
        self.assertIn("Task", {o["doctype"] for o in create_options(self.member, True)})
        sales = {o["doctype"]: o["href"] for o in create_options(self.sales, True)}
        self.assertEqual(sales.get("Quotation"), "/desk/quotation/new")

    def test_create_menu_is_empty_without_desk(self):
        self.assertEqual(create_options(self.member, False), [])

    def test_bell_shows_own_notifications_as_plain_text(self):
        own = self._notify(self.member, "<b>Administrator</b> assigned you a project")
        other = self._notify(self.outsider, "Not for the member")
        frappe.set_user(self.member)
        data = get_notifications()
        names = {item["name"] for item in data["items"]}
        self.assertIn(own, names)
        self.assertNotIn(other, names)
        item = next(i for i in data["items"] if i["name"] == own)
        self.assertEqual(item["subject"], "Administrator assigned you a project")
        self.assertEqual(item["href"], f"/av/projects/{self.project}")
        self.assertFalse(item["read"])
        self.assertEqual(data["unread"], 1)

        mark_all_as_read()
        self.assertEqual(get_notifications()["unread"], 0)

    def test_administrator_bell_shows_only_what_was_sent_to_them(self):
        member_log = self._notify(self.member, "For the member")
        frappe.set_user("Administrator")
        self.assertNotIn(member_log, {item["name"] for item in get_notifications()["items"]})
