import frappe
from frappe.apps import get_default_path
from frappe.tests import IntegrationTestCase
from frappe.website.path_resolver import PathResolver, get_website_rules, resolve_redirect
from frappe.website.utils import get_home_page
from werkzeug.routing import Map, Rule

from av_platform.shell import boot, has_app_permission, home_page, set_default_app, visible_views
from av_platform.www.av import get_context as av_entry


class ShellUsers(IntegrationTestCase):
    SALES = "av-shell-sales@av-prototype.invalid"
    PM = "av-shell-pm@av-prototype.invalid"
    BOTH = "av-shell-both@av-prototype.invalid"
    NONE = "av-shell-none@av-prototype.invalid"
    DIRECTOR = "av-shell-director@av-prototype.invalid"
    INSTALLER = "av-shell-installer@av-prototype.invalid"
    MODERATOR = "av-shell-moderator@av-prototype.invalid"

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
            # The director's home page wins over the other screens of the same person.
            cls.DIRECTOR: ["AV Director", "AV Sales"],
            # A desk user outside AV Platform keeps Frappe's own start page.
            cls.NONE: ["Accounts User"],
            # ADM-01: a moderator has no screen in the shell and works in the Desk user list.
            cls.MODERATOR: ["AV Moderator"],
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


class TestShellScreens(ShellUsers):
    def test_menu_shows_the_screens_of_the_roles(self):
        self.assertEqual(visible_views(self.SALES), ["sales"])
        self.assertEqual(visible_views(self.PM), ["home", "my-tasks", "projects", "board"])
        self.assertEqual(visible_views(self.INSTALLER), ["my-tasks", "projects", "board"])
        self.assertEqual(visible_views(self.BOTH), ["my-tasks", "projects", "board", "sales"])
        self.assertEqual(visible_views(self.DIRECTOR), ["home", "projects", "sales"])
        self.assertEqual(visible_views(self.NONE), [])
        self.assertEqual(visible_views(self.MODERATOR), [])
        self.assertEqual(visible_views("Guest"), [])
        self.assertEqual(visible_views("Administrator"), ["home", "my-tasks", "projects", "board", "sales"])

    def test_boot_carries_menu_start_page_and_desk_access(self):
        data = boot(self.PM)
        self.assertEqual(data["user"], self.PM)
        self.assertEqual(data["views"], ["home", "my-tasks", "projects", "board"])
        self.assertEqual(data["landing"], "av/home")
        self.assertTrue(data["desk"])

    def test_apps_screen_needs_a_role_of_the_screens(self):
        frappe.set_user(self.NONE)
        self.assertFalse(has_app_permission())
        frappe.set_user(self.MODERATOR)
        self.assertTrue(has_app_permission())
        frappe.set_user("Administrator")
        self.assertTrue(has_app_permission())

    def test_desk_no_longer_carries_av_pages_menus_or_rail(self):
        # ADR-006: migrate removes the Desk entities whose files were deleted.
        for page in ("av-overview", "av-projects", "av-project", "av-quotations", "av-work-board",
                     "av-my-tasks"):
            self.assertFalse(frappe.db.exists("Page", page), page)
        for sidebar in ("AV Sales", "AV Projects", "AV Overview"):
            self.assertFalse(frappe.db.exists("Sidebar", sidebar), sidebar)
        self.assertFalse(frappe.get_all("Dock", filters={"app": "av_platform", "standard": 1}))

    def test_every_shell_address_is_served_by_the_av_page(self):
        # /av itself is the www page; deeper addresses reach it through the route rule. Frappe
        # matches route rules only against a live request, so the rule map is matched here.
        endpoint, _renderer = PathResolver("av").resolve()
        self.assertEqual(endpoint, "av")
        urls = Map([Rule(r["from_route"], endpoint=r["to_route"]) for r in get_website_rules()]).bind("localhost")
        for path in ("av/home", "av/projects/PROJ-0001", "av/sales/SAL-QTN-0001", "av/unknown"):
            self.assertEqual(urls.match("/" + path)[0], "av", path)

    def test_old_redirects_to_desk_are_gone(self):
        for path in ("av/sales", "av/board", "av/my-tasks"):
            frappe.cache.hdel("website_redirects", path)
            resolve_redirect(path)  # no frappe.Redirect: the shell serves these addresses


class TestStartPage(ShellUsers):
    def test_each_role_has_its_start_page(self):
        self.assertEqual(home_page(self.SALES), "av/sales")
        self.assertEqual(home_page(self.PM), "av/home")
        self.assertEqual(home_page(self.INSTALLER), "av/my-tasks")
        self.assertEqual(home_page(self.BOTH), "av/sales")
        self.assertEqual(home_page(self.DIRECTOR), "av/home")
        self.assertEqual(home_page(self.MODERATOR), "desk/user")
        self.assertIsNone(home_page(self.NONE))

    def test_login_lands_on_the_role_start_page(self):
        # get_home_page is what the login response sends a desk user to.
        for user, expected in {self.SALES: "av/sales", self.PM: "av/home",
                               self.INSTALLER: "av/my-tasks"}.items():
            frappe.set_user(user)
            frappe.local.flags.home_page = None
            self.assertEqual(get_home_page(), expected, user)
        # Without an AV role Frappe keeps its own choice (it depends on the session's user type).
        frappe.set_user(self.NONE)
        frappe.local.flags.home_page = None
        self.assertNotIn("av/", get_home_page())

    def test_shell_page_renders_for_users_of_its_screens(self):
        frappe.set_user(self.SALES)
        context = frappe._dict()
        av_entry(context)
        self.assertEqual(context.boot["av_boot"]["views"], ["sales"])
        self.assertTrue(context.boot["csrf_token"])

    def test_shell_page_sends_others_away(self):
        for user, expected in {self.NONE: "/desk", self.MODERATOR: "/desk/user"}.items():
            frappe.set_user(user)
            with self.assertRaises(frappe.Redirect, msg=user):
                av_entry(frappe._dict())
            self.assertEqual(frappe.flags.redirect_location, expected, user)
        frappe.set_user("Guest")
        with self.assertRaises(frappe.Redirect):
            av_entry(frappe._dict())
        self.assertTrue(frappe.flags.redirect_location.startswith("/login?redirect-to="))

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
