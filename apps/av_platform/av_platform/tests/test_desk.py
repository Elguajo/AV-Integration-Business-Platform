import json
import os
import tempfile

import frappe
from frappe.apps import get_default_path
from frappe.tests import IntegrationTestCase
from frappe.website.path_resolver import resolve_redirect
from frappe.website.utils import get_home_page

from av_platform.desk import boot_session, desk_assets, has_app_permission, home_page, set_default_app
from av_platform.www.av import get_context as av_entry

HOME_ROLES = {"AV Director", "System Manager", "AV Project Manager", "Projects Manager"}
PAGES = {
    "av-overview": HOME_ROLES,
    "av-projects": HOME_ROLES | {"Projects User"},
    "av-project": HOME_ROLES | {"Projects User"},
    "av-quotations": {"AV Sales", "System Manager"},
    "av-work-board": {"Projects User", "Projects Manager", "System Manager"},
    "av-my-tasks": {"Projects User", "Projects Manager", "System Manager"},
}


class TestDeskAssets(IntegrationTestCase):
    def test_entry_and_styles_come_from_the_vite_manifest(self):
        with tempfile.TemporaryDirectory() as folder:
            path = os.path.join(folder, "manifest.json")
            with open(path, "w", encoding="utf-8") as f:
                json.dump({"src/desk.ts": {"file": "assets/desk-abc.js", "css": ["assets/desk-def.css"]}}, f)
            self.assertEqual(desk_assets(path), {
                "entry": "/assets/av_platform/frontend/assets/desk-abc.js",
                "css": ["/assets/av_platform/frontend/assets/desk-def.css"],
            })

    def test_missing_build_gives_no_assets(self):
        with tempfile.TemporaryDirectory() as folder:
            self.assertIsNone(desk_assets(os.path.join(folder, "manifest.json")))

    def test_committed_build_is_found_at_boot(self):
        bootinfo = frappe._dict()
        boot_session(bootinfo)
        self.assertTrue(bootinfo.av_desk["entry"].startswith("/assets/av_platform/frontend/assets/desk-"))


class TestDeskShell(IntegrationTestCase):
    def tearDown(self):
        frappe.set_user("Administrator")
        super().tearDown()

    def test_pages_are_limited_to_their_roles(self):
        for page, roles in PAGES.items():
            granted = set(frappe.get_all("Has Role", filters={"parent": page, "parenttype": "Page"},
                                         pluck="role"))
            self.assertEqual(granted, roles, page)

    def test_rail_and_sidebars_are_installed(self):
        self.assertTrue(frappe.db.exists("Sidebar", "AV Sales"))
        self.assertTrue(frappe.db.exists("Sidebar", "AV Projects"))
        self.assertTrue(frappe.db.exists("Sidebar", "AV Overview"))
        dock = frappe.get_all("Dock", filters={"app": "av_platform", "standard": 1}, pluck="name")
        self.assertEqual(len(dock), 1)
        targets = frappe.get_all("Dock Item", filters={"parent": dock[0]}, pluck="link_to")
        self.assertEqual(set(targets), {"AV Overview", "AV Sales", "AV Projects"})

    def test_menus_lead_with_av_screens_and_keep_desk_lists_as_reference(self):
        # UI-03: the AV screens come first; raw Desk lists sit in the collapsed «Справочники» group.
        projects = frappe.get_doc("Sidebar", "AV Projects").items
        self.assertEqual([(i.link_type, i.link_to) for i in projects[:3]],
                         [("Page", "av-projects"), ("Page", "av-work-board"), ("Page", "av-my-tasks")])
        section = next(i for i in projects if i.type == "Section Break")
        self.assertEqual(section.label, "Справочники")
        self.assertTrue(all(i.child for i in projects[projects.index(section) + 1:]))
        sales = frappe.get_doc("Sidebar", "AV Sales").items
        self.assertEqual((sales[0].link_type, sales[0].link_to), ("Page", "av-quotations"))
        home = frappe.get_all("Dock Item", filters={"link_to": "AV Overview"}, pluck="title")
        self.assertEqual(home, ["Главная"])

    def test_apps_screen_needs_a_role_of_the_screens(self):
        user = "av-desk-no-role@av-prototype.invalid"
        if not frappe.db.exists("User", user):
            frappe.get_doc({"doctype": "User", "email": user, "first_name": "No Role",
                            "send_welcome_email": 0}).insert(ignore_permissions=True)
        frappe.set_user(user)
        self.assertFalse(has_app_permission())
        frappe.set_user("Administrator")
        self.assertTrue(has_app_permission())

    def test_old_links_open_in_desk(self):
        cases = {
            "av/sales/SAL-QTN-0001": "/desk/av-quotations/SAL-QTN-0001",
            "av/sales": "/desk/av-quotations",
            "av/board": "/desk/av-work-board",
            "av/my-tasks": "/desk/av-my-tasks",
        }
        for path, target in cases.items():
            frappe.cache.hdel("website_redirects", path)
            with self.assertRaises(frappe.Redirect, msg=path) as raised:
                resolve_redirect(path)
            self.assertEqual(raised.exception.http_status_code, 302, path)
            self.assertEqual(frappe.flags.redirect_location, target, path)


class TestStartPage(IntegrationTestCase):
    SALES = "av-desk-sales@av-prototype.invalid"
    PM = "av-desk-pm@av-prototype.invalid"
    BOTH = "av-desk-both@av-prototype.invalid"
    NONE = "av-desk-none@av-prototype.invalid"
    DIRECTOR = "av-desk-director@av-prototype.invalid"
    INSTALLER = "av-desk-installer@av-prototype.invalid"

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        frappe.set_user("Administrator")
        for email, roles in {
            cls.SALES: ["Sales User", "AV Sales"],
            cls.PM: ["Projects User", "AV Project Manager"],
            cls.BOTH: ["Projects User", "AV Sales"],
            # A field user without the PM role keeps the list of works.
            cls.INSTALLER: ["Projects User"],
            # The director's overview wins over the other screens of the same person.
            cls.DIRECTOR: ["AV Director", "AV Sales"],
            # A desk user outside AV Platform keeps Frappe's own start page.
            cls.NONE: ["Accounts User"],
        }.items():
            if not frappe.db.exists("User", email):
                frappe.get_doc({"doctype": "User", "email": email, "first_name": email.split("@")[0],
                                "send_welcome_email": 0,
                                "roles": [{"role": r} for r in roles]}).insert(ignore_permissions=True)

    def tearDown(self):
        frappe.set_user("Administrator")
        frappe.local.flags.home_page = None
        frappe.local.system_settings = None
        super().tearDown()

    def test_each_role_has_its_start_page(self):
        self.assertEqual(home_page(self.SALES), "desk/av-quotations")
        self.assertEqual(home_page(self.PM), "desk/av-overview")
        self.assertEqual(home_page(self.INSTALLER), "desk/av-my-tasks")
        self.assertEqual(home_page(self.BOTH), "desk/av-quotations")
        self.assertEqual(home_page(self.DIRECTOR), "desk/av-overview")
        self.assertIsNone(home_page(self.NONE))

    def test_login_lands_on_the_role_start_page(self):
        # get_home_page is what the login response sends a desk user to.
        for user, expected in {self.SALES: "desk/av-quotations", self.PM: "desk/av-overview",
                               self.INSTALLER: "desk/av-my-tasks"}.items():
            frappe.set_user(user)
            frappe.local.flags.home_page = None
            self.assertEqual(get_home_page(), expected, user)
        # Without an AV role Frappe keeps its own choice (it depends on the session's user type).
        frappe.set_user(self.NONE)
        frappe.local.flags.home_page = None
        self.assertNotIn("av-", get_home_page())

    def test_av_entry_redirects_by_role(self):
        for user, expected in {self.SALES: "/desk/av-quotations", self.PM: "/desk/av-overview",
                               self.NONE: "/desk", "Guest": "/login?redirect-to=/av"}.items():
            frappe.set_user(user)
            with self.assertRaises(frappe.Redirect, msg=user):
                av_entry(frappe._dict())
            self.assertEqual(frappe.flags.redirect_location, expected, user)

    def test_av_platform_is_the_default_app(self):
        self.assertEqual(frappe.db.get_single_value("System Settings", "default_app"), "av_platform")
        frappe.set_user(self.PM)
        frappe.local.system_settings = None
        self.assertEqual(get_default_path(), "/av")

    def test_default_app_chosen_by_an_administrator_is_kept(self):
        frappe.db.set_single_value("System Settings", "default_app", "erpnext")
        frappe.clear_document_cache("System Settings", "System Settings")
        try:
            set_default_app()
            self.assertEqual(frappe.db.get_single_value("System Settings", "default_app"), "erpnext")
        finally:
            frappe.db.set_single_value("System Settings", "default_app", "av_platform")
            frappe.clear_document_cache("System Settings", "System Settings")
