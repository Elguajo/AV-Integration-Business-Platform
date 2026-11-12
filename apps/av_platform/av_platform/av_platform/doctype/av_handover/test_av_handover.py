import json
import os
from unittest.mock import patch

import frappe
from frappe.tests import IntegrationTestCase

from av_platform.av_platform.doctype.av_handover.av_handover import AVHandover, review_handover
from av_platform.demo import seed

# The suite builds its own synthetic data through seed(). Without this, Frappe walks every
# linked DocType (Quotation -> ... -> Payment Gateway) and fails on apps that are not installed.
IGNORE_TEST_RECORD_DEPENDENCIES = ["Quotation", "User", "Company", "Customer", "Currency", "Project"]


class TestAVHandover(IntegrationTestCase):
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
        frappe.db.savepoint("av_test_case")
        quote = frappe.copy_doc(frappe.get_doc("Quotation", self.demo["quotations"]["Q2"]))
        quote.title = "AV test " + frappe.generate_hash(length=10)
        quote.insert()
        quote.submit()
        self.quote_name = quote.name
        self.sales = self.demo["sales_user"]
        self.pm = self.demo["pm_user"]

    def tearDown(self):
        frappe.set_user("Administrator")
        frappe.db.rollback(save_point="av_test_case")
        frappe.clear_cache(user=self.pm)
        super().tearDown()

    def handover(self, submit=True):
        frappe.set_user(self.sales)
        doc = frappe.get_doc({
            "doctype": "AV Handover", "quotation": self.quote_name,
            "project_name": "AV test " + frappe.generate_hash(length=10),
            "project_manager": self.pm, "customer_approval_reference": "SYNTHETIC: customer accepts Q2.",
        }).insert()
        if submit:
            doc.submit()
        return doc

    def test_accept_and_retry_create_one_project(self):
        doc = self.handover()
        before = doc.snapshot_json
        frappe.set_user(self.pm)
        first = review_handover(doc.name, "accept")
        retry = review_handover(doc.name, "accept")
        self.assertEqual(first, retry)
        self.assertEqual(frappe.db.count("Project", {"project_name": doc.project_name}), 1)
        doc.reload()
        self.assertEqual(doc.snapshot_json, before)
        self.assertEqual(doc.reviewed_by, self.pm)
        self.assertEqual(doc.accepted_value, 16000)
        self.assertEqual([row["item_code"] for row in json.loads(doc.snapshot_json)["items"]],
                         ["AVP-M", "AVP-SERVICES"])
        project = frappe.get_doc("Project", first["project"])
        self.assertEqual(project.company, doc.company)
        self.assertEqual(project.customer, doc.customer)

    def test_catalogue_change_does_not_rewrite_baseline(self):
        doc = self.handover()
        before = doc.snapshot_json
        frappe.set_user("Administrator")
        item = frappe.get_doc("Item", "AVP-M")
        item.item_name = "New catalogue label"
        item.description = "New catalogue description"
        item.save()
        self.assertEqual(doc.reload().snapshot_json, before)
        self.assertNotEqual(json.loads(before)["items"][0]["item_name"], item.item_name)

    def test_direct_update_and_forged_capability_cannot_accept(self):
        doc = self.handover()
        doc.review_status = "Accepted"
        doc.flags.av_review_capability = True
        with self.assertRaises(frappe.ValidationError):
            doc.save()
        self.assertEqual(frappe.db.get_value("AV Handover", doc.name, "review_status"), "Pending")

    def test_sales_cannot_accept_own_handover(self):
        doc = self.handover()
        with self.assertRaises(frappe.PermissionError):
            review_handover(doc.name, "accept")
        self.assertEqual(frappe.db.count("Project", {"project_name": doc.project_name}), 0)

    def test_unassigned_pm_cannot_read_or_review(self):
        doc = self.handover()
        frappe.set_user("Administrator")
        email = "other-pm-" + frappe.generate_hash(length=8) + "@av-prototype.invalid"
        frappe.get_doc({"doctype": "User", "email": email, "first_name": "Other PM",
                        "send_welcome_email": 0, "roles": [{"role": "AV Project Manager"},
                                                              {"role": "Projects User"}]}).insert()
        frappe.set_user(email)
        with self.assertRaises(frappe.PermissionError):
            review_handover(doc.name, "accept")
        self.assertEqual(frappe.get_list("AV Handover", filters={"name": doc.name}), [])

    def test_return_requires_comment_and_does_not_create_project(self):
        doc = self.handover()
        frappe.set_user(self.pm)
        with self.assertRaises(frappe.ValidationError):
            review_handover(doc.name, "return")
        result = review_handover(doc.name, "return", "Clarify the agreed scope")
        self.assertEqual(result["status"], "Returned")
        self.assertFalse(result["project"])
        with self.assertRaises(frappe.ValidationError):
            review_handover(doc.name, "accept")

    def test_draft_handover_cannot_be_accepted(self):
        doc = self.handover(submit=False)
        frappe.set_user(self.pm)
        with self.assertRaises(frappe.ValidationError):
            review_handover(doc.name, "accept")

    def test_duplicate_transfer_of_same_quotation_rejected(self):
        self.handover()
        with self.assertRaises((frappe.UniqueValidationError, frappe.DuplicateEntryError)):
            self.handover()

    def test_submitted_snapshot_cannot_be_rewritten_or_cancelled(self):
        doc = self.handover()
        doc.snapshot_json = "{}"
        with self.assertRaises(frappe.ValidationError):
            doc.save()
        with self.assertRaises((frappe.ValidationError, frappe.PermissionError)):
            doc.reload().cancel()

    def test_missing_project_create_permission_leaves_handover_pending(self):
        doc = self.handover()
        frappe.set_user("Administrator")
        user = frappe.get_doc("User", self.pm)
        user.set("roles", [row for row in user.roles if row.role != "Projects User"])
        user.save()
        frappe.clear_cache(user=self.pm)
        frappe.set_user(self.pm)
        with self.assertRaises(frappe.PermissionError):
            review_handover(doc.name, "accept")
        self.assertEqual(frappe.db.count("Project", {"project_name": doc.project_name}), 0)
        self.assertEqual(frappe.db.get_value("AV Handover", doc.name, "review_status"), "Pending")

    def test_failure_after_project_insert_rolls_back_project_and_decision(self):
        doc = self.handover()
        frappe.set_user(self.pm)
        with patch.object(AVHandover, "before_update_after_submit",
                          side_effect=frappe.ValidationError("Injected save failure")):
            with self.assertRaises(frappe.ValidationError):
                review_handover(doc.name, "accept")
        self.assertEqual(frappe.db.count("Project", {"project_name": doc.project_name}), 0)
        self.assertEqual(frappe.db.get_value("AV Handover", doc.name, "review_status"), "Pending")
        self.assertFalse(frappe.db.get_value("AV Handover", doc.name, "project"))
