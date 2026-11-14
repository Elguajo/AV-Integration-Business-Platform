"""Which issued quotation is the current version of an offer.

User decision 14.11.2026: only the current version may be handed over to the PM.
Prototype grouping: quotations of one customer within one company are versions of one
offer, ordered by creation. A separate deal model (SAL-01) replaces this grouping later.
"""

import frappe


def version_filters(party_name, company):
    return {"quotation_to": "Customer", "party_name": party_name, "company": company}


def current_versions(groups):
    """Map (party_name, company) -> name of the latest submitted quotation.

    Reads without user permissions on purpose: a newer version issued by another
    salesperson still supersedes the older one. Only names are returned to callers.
    """
    parties = sorted({party for party, _company in groups if party})
    if not parties:
        return {}
    rows = frappe.get_all(
        "Quotation", fields=["name", "party_name", "company"],
        filters={"quotation_to": "Customer", "party_name": ["in", parties], "docstatus": 1},
        order_by="creation desc, name desc", limit_page_length=0,
    )
    current = {}
    for row in rows:
        current.setdefault((row.party_name, row.company), row.name)
    return current


def current_version(quote):
    return current_versions([(quote.party_name, quote.company)]).get(
        (quote.party_name, quote.company)
    )


def is_current_version(quote):
    return quote.docstatus == 1 and current_version(quote) == quote.name
