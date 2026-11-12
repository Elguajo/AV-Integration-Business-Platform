import os
from unittest.mock import patch

import frappe
from frappe.tests import IntegrationTestCase

from av_platform.demo import seed
from av_platform.sales_api import create_handover, get_quotation, get_workspace


class TestSalesWorkspaceAPI(IntegrationTestCase):
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
        frappe.db.savepoint("av_sales_api_case")
        quote = frappe.copy_doc(frappe.get_doc("Quotation", self.demo["quotations"]["Q2"]))
        quote.title = "AV UI test " + frappe.generate_hash(length=10)
        quote.insert()
        quote.submit()
        self.fresh = quote.name
        self.sales = self.demo["sales_user"]
        self.pm = self.demo["pm_user"]

    def tearDown(self):
        frappe.set_user("Administrator")
        frappe.db.rollback(save_point="av_sales_api_case")
        super().tearDown()

    def _other_sales(self):
        email = "other-sales-" + frappe.generate_hash(length=8) + "@av-prototype.invalid"
        frappe.get_doc({"doctype": "User", "email": email, "first_name": "Other Sales",
                        "send_welcome_email": 0, "roles": [{"role": "AV Sales"},
                                                          {"role": "Sales User"}]}).insert()
        return email

    def test_workspace_shows_stages_from_server(self):
        frappe.set_user(self.sales)
        rows = {row["name"]: row for row in get_workspace()["quotations"]}
        self.assertEqual(rows[self.demo["quotations"]["Q2"]]["stage"], "handover_pending")
        self.assertEqual(rows[self.fresh]["stage"], "issued")
        self.assertIsNone(rows[self.fresh]["handover"])

    def test_quotation_separates_main_scope_and_alternatives(self):
        frappe.set_user(self.sales)
        data = get_quotation(self.demo["quotations"]["Q2"])
        self.assertEqual(data["main_total"], 16000)
        self.assertEqual([row["item_code"] for row in data["main_items"]],
                         ["AVP-M", "AVP-SERVICES"])
        self.assertEqual([row["item_code"] for row in data["alternatives"]], ["AVP-ALTERNATIVE"])
        self.assertIn("handover_exists", data["blockers"])
        self.assertFalse(data["can_handover"])
        self.assertEqual(data["pm_options"], [])
        self.assertEqual([v["version"] for v in data["versions"]][:2], [1, 2])

    def test_fresh_quotation_can_be_handed_over_once(self):
        frappe.set_user(self.sales)
        data = get_quotation(self.fresh)
        self.assertTrue(data["can_handover"], data["blockers"])
        self.assertIn(self.pm, [row["name"] for row in data["pm_options"]])
        result = create_handover(self.fresh, self.pm, "UI test project",
                                 "SYNTHETIC: customer accepted the main scope.")
        self.assertEqual(result["review_status"], "Pending")
        self.assertEqual(result["accepted_value"], 16000)
        self.assertEqual(get_quotation(self.fresh)["stage"], "handover_pending")
        with self.assertRaises((frappe.UniqueValidationError, frappe.DuplicateEntryError)):
            create_handover(self.fresh, self.pm, "UI test project",
                            "SYNTHETIC: customer accepted the main scope.")

    def test_missing_customer_approval_creates_nothing(self):
        frappe.set_user(self.sales)
        with self.assertRaises(frappe.ValidationError):
            create_handover(self.fresh, self.pm, "UI test project", "   ")
        frappe.set_user("Administrator")
        self.assertTrue(frappe.db.exists("Quotation", self.fresh))
        self.assertFalse(frappe.db.exists("AV Handover", {"quotation": self.fresh}))

    def test_pm_cannot_use_sales_workspace(self):
        frappe.set_user(self.pm)
        with self.assertRaises(frappe.PermissionError):
            get_workspace()
        with self.assertRaises(frappe.PermissionError):
            create_handover(self.fresh, self.pm, "UI test project", "SYNTHETIC: approval.")

    def test_other_sales_sees_existence_but_not_details(self):
        other = self._other_sales()
        frappe.set_user(other)
        rows = {row["name"]: row for row in get_workspace()["quotations"]}
        q2 = rows[self.demo["quotations"]["Q2"]]
        self.assertEqual(q2["stage"], "handover_unknown")
        self.assertIsNone(q2["handover"])
        data = get_quotation(self.demo["quotations"]["Q2"])
        self.assertIsNone(data["handover"])
        self.assertIn("handover_exists", data["blockers"])
