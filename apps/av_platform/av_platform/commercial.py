"""Pure snapshot rules; no database and no alternative stock/financial journal."""

import hashlib
import json
import math
from datetime import date, datetime
from decimal import Decimal


def _normalize(value):
    if isinstance(value, dict):
        return {key: _normalize(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_normalize(item) for item in value]
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    if isinstance(value, Decimal):
        if not value.is_finite():
            raise ValueError("Non-finite commercial number")
        return str(value)
    if isinstance(value, float):
        if not math.isfinite(value):
            raise ValueError("Non-finite commercial number")
        return str(value)
    return value


HEADER_FIELDS = (
    "name", "modified", "company", "quotation_to", "party_name", "customer_name",
    "currency", "conversion_rate", "transaction_date", "valid_till", "order_type",
    "total", "net_total", "grand_total", "rounded_total", "rounding_adjustment",
    "base_grand_total", "discount_amount", "additional_discount_percentage",
    "apply_discount_on", "taxes_and_charges", "total_taxes_and_charges", "terms",
)
ITEM_FIELDS = (
    "name", "idx", "item_code", "item_name", "description", "qty", "stock_qty",
    "uom", "stock_uom", "conversion_factor", "rate", "amount", "net_rate",
    "net_amount", "base_rate", "base_amount", "discount_percentage", "discount_amount",
    "delivery_date", "is_alternative", "has_alternative_item",
)
TAX_FIELDS = (
    "name", "idx", "charge_type", "account_head", "description", "rate",
    "tax_amount", "total", "included_in_print_rate",
)
PAYMENT_FIELDS = ("payment_term", "description", "due_date", "invoice_portion", "payment_amount")


def build_snapshot(quotation, approval_reference):
    if quotation.get("docstatus") != 1:
        raise ValueError("A submitted quotation is required")
    if quotation.get("quotation_to") != "Customer" or not quotation.get("party_name"):
        raise ValueError("The quotation must be addressed to a Customer")
    if not approval_reference or not approval_reference.strip():
        raise ValueError("Customer approval evidence is required")
    items = quotation.get("items", [])
    if not any(not row.get("is_alternative") for row in items):
        raise ValueError("The quotation must contain accepted main items")
    payload = {"schema_version": 1, "approval_reference": approval_reference.strip()}
    payload["quotation"] = {field: quotation.get(field) for field in HEADER_FIELDS}
    for table, fields in (
        ("items", ITEM_FIELDS), ("taxes", TAX_FIELDS), ("payment_schedule", PAYMENT_FIELDS)
    ):
        payload[table] = [{field: row.get(field) for field in fields} for row in quotation.get(table, [])]
    # ERPNext v16 excludes is_alternative rows from quotation totals. Preserve them
    # for evidence, but keep them out of the accepted scope used downstream.
    payload["excluded_alternatives"] = [row for row in payload["items"] if row["is_alternative"]]
    payload["items"] = [row for row in payload["items"] if not row["is_alternative"]]
    return _normalize(payload)


def serialize_snapshot(snapshot):
    return json.dumps(snapshot, sort_keys=True, ensure_ascii=False, separators=(",", ":"), allow_nan=False)


def snapshot_digest(serialized):
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()
