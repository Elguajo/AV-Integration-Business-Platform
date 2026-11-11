import copy
import json
import unittest
from datetime import date
from decimal import Decimal

from av_platform.commercial import build_snapshot, serialize_snapshot, snapshot_digest


def quotation():
    return {
        "name": "Q2", "docstatus": 1, "quotation_to": "Customer", "party_name": "Synthetic P1",
        "currency": "USD", "grand_total": Decimal("16000.00"), "transaction_date": date(2026, 11, 5),
        "items": [{"name": "ROW-M", "item_code": "M", "qty": 4, "rate": Decimal(2000),
                   "amount": Decimal(8000)},
                  {"name": "ROW-S", "item_code": "SERVICES", "qty": 1, "rate": Decimal(8000)}],
        "terms": "Q2 main scope; alternatives excluded",
    }


class CommercialSnapshotTests(unittest.TestCase):
    def test_t1_preserves_accepted_scope_and_16000(self):
        snapshot = build_snapshot(quotation(), "Test approval")
        self.assertEqual(snapshot["quotation"]["grand_total"], "16000.00")
        self.assertEqual([row["item_code"] for row in snapshot["items"]], ["M", "SERVICES"])
        self.assertEqual(snapshot["quotation"]["transaction_date"], "2026-11-05")

    def test_later_source_changes_cannot_rewrite_snapshot(self):
        quote = quotation()
        snapshot = build_snapshot(quote, "Test approval")
        original = serialize_snapshot(snapshot)
        quote["items"][0]["rate"] = Decimal(9999)
        quote["terms"] = "New catalogue terms"
        self.assertEqual(serialize_snapshot(snapshot), original)

    def test_standard_erpnext_alternative_stays_out_of_accepted_scope(self):
        quote = quotation()
        quote["items"].insert(1, {"name": "ALT", "item_code": "ALT-M", "qty": 4,
                                  "rate": 2000, "is_alternative": 1})
        snapshot = build_snapshot(quote, "Test")
        self.assertEqual([row["item_code"] for row in snapshot["items"]], ["M", "SERVICES"])
        self.assertEqual(snapshot["excluded_alternatives"][0]["item_code"], "ALT-M")
        self.assertEqual(snapshot["quotation"]["grand_total"], "16000.00")

    def test_draft_and_cancelled_quote_rejected(self):
        for status in (0, 2):
            quote = quotation()
            quote["docstatus"] = status
            with self.assertRaisesRegex(ValueError, "submitted"):
                build_snapshot(quote, "Test approval")

    def test_missing_evidence_customer_or_items_rejected(self):
        for changes, evidence in (({}, "  "), ({"quotation_to": "Lead"}, "Test"),
                                  ({"party_name": ""}, "Test"), ({"items": []}, "Test")):
            with self.subTest(changes=changes, evidence=evidence), self.assertRaises(ValueError):
                build_snapshot({**quotation(), **changes}, evidence)

    def test_checksum_stable_across_key_order_but_detects_price_changes(self):
        quote = quotation()
        first = serialize_snapshot(build_snapshot(quote, "Test approval"))
        reordered = dict(reversed(list(quote.items())))
        self.assertEqual(first, serialize_snapshot(build_snapshot(reordered, "Test approval")))
        changed = copy.deepcopy(quote)
        changed["items"][0]["rate"] = Decimal(2001)
        self.assertNotEqual(snapshot_digest(first), snapshot_digest(serialize_snapshot(build_snapshot(changed, "Test approval"))))

    def test_non_finite_numbers_rejected(self):
        for value in (float("nan"), float("inf"), Decimal("NaN"), Decimal("Infinity")):
            with self.subTest(value=value), self.assertRaises(ValueError):
                build_snapshot({**quotation(), "grand_total": value}, "Test")

    def test_operational_metadata_and_internal_cost_fields_excluded(self):
        quote = quotation()
        quote["_comments"] = "Private comment"
        quote["items"][0]["valuation_rate"] = 1000
        snapshot = json.loads(serialize_snapshot(build_snapshot(quote, "Test")))
        self.assertNotIn("_comments", snapshot["quotation"])
        self.assertNotIn("valuation_rate", snapshot["items"][0])


if __name__ == "__main__":
    unittest.main()
