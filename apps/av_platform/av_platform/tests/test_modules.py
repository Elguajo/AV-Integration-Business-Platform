import frappe
from frappe.tests import IntegrationTestCase

from av_platform.patches.remove_av_platform_module import OLD_MODULE
from av_platform.patches.remove_av_platform_module import execute as remove_old_module


class TestModules(IntegrationTestCase):
    def test_doctypes_live_in_domain_modules(self):
        self.assertEqual(frappe.get_meta("AV Handover").module, "AV Sales")
        self.assertEqual(frappe.get_meta("AV Work Stage").module, "AV Projects")
        for module in ("AV Sales", "AV Projects"):
            self.assertEqual(frappe.db.get_value("Module Def", module, "app_name"), "av_platform")

    def test_old_module_is_gone_after_migrate(self):
        self.assertFalse(frappe.db.exists("Module Def", OLD_MODULE))

    def test_old_module_is_kept_while_referenced(self):
        frappe.get_doc(
            {"doctype": "Module Def", "module_name": OLD_MODULE, "app_name": "av_platform"}
        ).insert(ignore_permissions=True, ignore_if_duplicate=True)
        # A DocType still filed under the old module keeps it.
        frappe.db.set_value("DocType", "AV Work Stage", "module", OLD_MODULE, update_modified=False)
        try:
            remove_old_module()
            self.assertTrue(frappe.db.exists("Module Def", OLD_MODULE))
        finally:
            frappe.db.set_value("DocType", "AV Work Stage", "module", "AV Projects", update_modified=False)

        remove_old_module()
        self.assertFalse(frappe.db.exists("Module Def", OLD_MODULE))
