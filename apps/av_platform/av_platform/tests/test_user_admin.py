"""ADM-01: system administrator and moderator roles, checked in every channel that saves a User."""

import frappe
import frappe.client
from frappe.core.doctype.user.user import change_password
from frappe.tests import IntegrationTestCase

from av_platform.desk import has_app_permission, home_page
from av_platform.user_admin import ADMIN_ROLE, MODERATOR_ROLE, SYSTEM_MANAGER, ensure_setup


class TestUserAdmin(IntegrationTestCase):
    def setUp(self):
        super().setUp()
        frappe.set_user("Administrator")
        frappe.db.savepoint("av_user_admin_case")
        ensure_setup()
        self.moderator = self._user(MODERATOR_ROLE)
        self.other_moderator = self._user(MODERATOR_ROLE)
        self.admin = self._user(ADMIN_ROLE)
        self.system_manager = self._user(SYSTEM_MANAGER)
        self.worker = self._user("Projects User", "AV Project Manager")
        self.accountant = self._user("Accounts User")

    def tearDown(self):
        frappe.set_user("Administrator")
        frappe.db.rollback(save_point="av_user_admin_case")
        super().tearDown()

    def _user(self, *roles):
        email = "adm-" + frappe.generate_hash(length=8) + "@av-prototype.invalid"
        frappe.get_doc({"doctype": "User", "email": email, "first_name": "Admin test",
                        "send_welcome_email": 0, "roles": [{"role": r} for r in roles]}).insert()
        return email

    def _roles(self, user):
        return set(frappe.get_all("Has Role", filters={"parent": user, "parenttype": "User"},
                                  pluck="role"))

    def _as_moderator(self):
        frappe.set_user(self.moderator)

    def _denied(self, action):
        with self.assertRaises(frappe.PermissionError):
            action()

    # --- setup and administrator ---

    def test_setup_is_idempotent_and_keeps_system_manager_rules(self):
        ensure_setup()
        for role in (ADMIN_ROLE, MODERATOR_ROLE):
            self.assertTrue(frappe.db.exists("Role", role))
        rules = frappe.get_all("Custom DocPerm", filters={"parent": "User", "role": MODERATOR_ROLE},
                               fields=["permlevel", "read", "write", "create", "delete", "export",
                                       "import", "share", "impersonate", "print", "email"])
        self.assertEqual(len(rules), 2)
        for rule in rules:
            self.assertEqual((rule.read, rule.write), (1, 1))
            self.assertEqual((rule.delete, rule.export, rule["import"], rule.share, rule.impersonate,
                              rule.print, rule.email), (0,) * 7)
        self.assertEqual({r.permlevel: r.create for r in rules}, {0: 1, 1: 0})
        manager = frappe.get_all("Custom DocPerm", filters={"parent": "User", "role": SYSTEM_MANAGER,
                                                            "permlevel": 0}, fields=["delete"])
        self.assertEqual([r.delete for r in manager], [1])

    def test_administrator_role_carries_system_manager(self):
        self.assertIn(SYSTEM_MANAGER, self._roles(self.admin))
        doc = frappe.get_doc("User", self.worker)
        doc.append("roles", {"role": ADMIN_ROLE})
        doc.save()
        self.assertTrue({ADMIN_ROLE, SYSTEM_MANAGER} <= self._roles(self.worker))
        # System Manager cannot be dropped while the account keeps AV Administrator.
        doc = frappe.get_doc("User", self.admin)
        doc.set("roles", [r for r in doc.roles if r.role != SYSTEM_MANAGER])
        doc.save()
        self.assertIn(SYSTEM_MANAGER, self._roles(self.admin))

    def test_system_manager_is_not_limited(self):
        frappe.set_user(self.system_manager)
        doc = frappe.get_doc("User", self.moderator)
        doc.append("roles", {"role": SYSTEM_MANAGER})
        doc.save()
        self.assertIn(SYSTEM_MANAGER, self._roles(self.moderator))

    # --- moderator: allowed work ---

    def test_moderator_creates_user_with_work_roles(self):
        self._as_moderator()
        email = "adm-new-" + frappe.generate_hash(length=6) + "@av-prototype.invalid"
        frappe.get_doc({"doctype": "User", "email": email, "first_name": "New", "last_name": "Hire",
                        "send_welcome_email": 0, "mobile_no": "+10000000000",
                        "roles": [{"role": "AV Sales"}, {"role": "Sales User"}]}).insert()
        self.assertEqual(self._roles(email), {"AV Sales", "Sales User"})

    def test_moderator_grants_removes_roles_and_disables(self):
        self._as_moderator()
        doc = frappe.get_doc("User", self.worker)
        doc.append("roles", {"role": "AV Director"})
        doc.set("roles", [r for r in doc.roles if r.role != "AV Project Manager"])
        doc.first_name = "Renamed"
        doc.save()
        self.assertEqual(self._roles(self.worker), {"Projects User", "AV Director"})
        doc = frappe.get_doc("User", self.worker)
        doc.enabled = 0
        doc.save()
        self.assertEqual(frappe.db.get_value("User", self.worker, "enabled"), 0)

    def test_moderator_edits_own_profile(self):
        self._as_moderator()
        doc = frappe.get_doc("User", self.moderator)
        doc.last_name = "Moderator"
        doc.save()
        self.assertEqual(frappe.db.get_value("User", self.moderator, "last_name"), "Moderator")

    # --- moderator: escalation and protected accounts ---

    def test_moderator_cannot_create_privileged_users(self):
        self._as_moderator()
        for role in (SYSTEM_MANAGER, ADMIN_ROLE, MODERATOR_ROLE, "Accounts User"):
            email = "adm-esc-" + frappe.generate_hash(length=6) + "@av-prototype.invalid"
            self._denied(lambda: frappe.get_doc({
                "doctype": "User", "email": email, "first_name": "Escalation",
                "send_welcome_email": 0, "roles": [{"role": role}]}).insert())
            self.assertFalse(frappe.db.exists("User", email), role)

    def test_moderator_cannot_grant_or_remove_other_roles(self):
        self._as_moderator()
        for role in (SYSTEM_MANAGER, ADMIN_ROLE, MODERATOR_ROLE, "Projects Manager"):
            doc = frappe.get_doc("User", self.worker)
            doc.append("roles", {"role": role})
            self._denied(doc.save)
        doc = frappe.get_doc("User", self.accountant)
        doc.set("roles", [])
        self._denied(doc.save)
        self.assertEqual(self._roles(self.worker), {"Projects User", "AV Project Manager"})
        self.assertEqual(self._roles(self.accountant), {"Accounts User"})

    def test_moderator_cannot_touch_administrators_or_moderators(self):
        self._as_moderator()
        for target in (self.admin, self.system_manager, self.other_moderator):
            doc = frappe.get_doc("User", target)
            doc.enabled = 0
            self._denied(doc.save)
            doc = frappe.get_doc("User", target)
            doc.set("roles", [])
            self._denied(doc.save)
            self.assertEqual(frappe.db.get_value("User", target, "enabled"), 1)
        self.assertTrue({ADMIN_ROLE, SYSTEM_MANAGER} <= self._roles(self.admin))

    def test_moderator_cannot_change_own_roles_or_access(self):
        self._as_moderator()
        doc = frappe.get_doc("User", self.moderator)
        doc.append("roles", {"role": "AV Director"})
        self._denied(doc.save)
        doc = frappe.get_doc("User", self.moderator)
        doc.set("roles", [])
        self._denied(doc.save)
        doc = frappe.get_doc("User", self.moderator)
        doc.restrict_ip = "10.0.0.1"
        self._denied(doc.save)
        self.assertEqual(self._roles(self.moderator), {MODERATOR_ROLE})

    def test_moderator_cannot_change_access_fields_of_others(self):
        self._as_moderator()
        for field, value in (("restrict_ip", "10.0.0.1"), ("login_after", 1), ("api_key", "abc"),
                             ("api_secret", "secret"), ("new_password", "Synthetic-Only-Pass-917!"),
                             ("simultaneous_sessions", 9)):
            doc = frappe.get_doc("User", self.worker)
            doc.set(field, value)
            self._denied(doc.save)
        doc = frappe.get_doc("User", self.worker)
        doc.append("block_modules", {"module": "Accounts"})
        self._denied(doc.save)
        self._denied(lambda: change_password(self.worker, "Synthetic-Only-Pass-917!"))
        self.assertEqual(frappe.get_all("Block Module", filters={"parent": self.worker}), [])

    def test_role_profile_is_not_a_way_around(self):
        profile = frappe.get_doc({"doctype": "Role Profile",
                                  "role_profile": "ADM test " + frappe.generate_hash(length=6),
                                  "roles": [{"role": SYSTEM_MANAGER}]}).insert().name
        self._as_moderator()
        for target in (self.worker, self.moderator):
            doc = frappe.get_doc("User", target)
            doc.append("role_profiles", {"role_profile": profile})
            self._denied(doc.save)
            self.assertNotIn(SYSTEM_MANAGER, self._roles(target))
        email = "adm-prof-" + frappe.generate_hash(length=6) + "@av-prototype.invalid"
        self._denied(lambda: frappe.get_doc({
            "doctype": "User", "email": email, "first_name": "Profile", "send_welcome_email": 0,
            "role_profiles": [{"role_profile": profile}]}).insert())

    def test_child_row_channels_go_through_the_same_check(self):
        self._as_moderator()
        self._denied(lambda: frappe.client.insert({
            "doctype": "Has Role", "parenttype": "User", "parentfield": "roles",
            "parent": self.worker, "role": SYSTEM_MANAGER}))
        row = frappe.db.get_value("Has Role", {"parent": self.admin, "role": ADMIN_ROLE})
        self._denied(lambda: frappe.client.delete("Has Role", row))
        self._denied(lambda: frappe.client.set_value("User", self.admin, "enabled", 0))
        self.assertNotIn(SYSTEM_MANAGER, self._roles(self.worker))
        self.assertIn(ADMIN_ROLE, self._roles(self.admin))

    def test_moderator_has_no_delete_impersonate_or_business_access(self):
        self._as_moderator()
        worker = frappe.get_doc("User", self.worker)
        for ptype in ("delete", "export", "impersonate", "share"):
            self.assertFalse(frappe.has_permission("User", ptype, doc=worker), ptype)
        for doctype in ("Project", "Task", "Quotation", "AV Handover", "Role Profile",
                        "Custom DocPerm", "System Settings"):
            self.assertFalse(frappe.has_permission(doctype, "read"), doctype)
        self.assertNotIn("Administrator", frappe.get_list("User", pluck="name"))

    def test_moderator_desk_entry(self):
        self.assertEqual(home_page(self.moderator), "desk/user")
        self.assertIsNone(home_page(self.accountant))
        self._as_moderator()
        self.assertTrue(has_app_permission())
