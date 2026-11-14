"""Synthetic P1 seed only; no real customer records or external communications."""

import os

import frappe
from frappe.utils import add_days, today


def _guard():
    if not frappe.conf.get("av_prototype"):
        frappe.throw("Demo operations require av_prototype = 1.")
    if frappe.session.user != "Administrator":
        frappe.throw("Demo setup requires Administrator.", frappe.PermissionError)


def _get_or_insert(doctype, filters, values):
    name = frappe.db.exists(doctype, filters)
    return frappe.get_doc(doctype, name) if name else frappe.get_doc({"doctype": doctype, **values}).insert()


def _user(email, first_name, roles, password):
    if not password:
        frappe.throw("Demo user passwords must be supplied through environment variables.")
    user = _get_or_insert("User", email, {
        "email": email, "first_name": first_name, "send_welcome_email": 0,
        "user_type": "System User", "new_password": password,
        "roles": [{"role": role} for role in roles],
    })
    required = set(roles)
    if not required.issubset({row.role for row in user.roles}):
        frappe.throw(f"Existing demo user {email} has unexpected roles. Review it manually.")
    return user.name


def seed():
    _guard()
    from erpnext.setup.setup_wizard.operations.install_fixtures import install

    if not frappe.db.exists("Item Group", "All Item Groups"):
        install(country="Uzbekistan")  # Standard ERPNext roots, UOMs and setup defaults.
    company = _get_or_insert("Company", "AV Prototype", {
        "company_name": "AV Prototype", "abbr": "AVP", "default_currency": "USD",
        "country": "Uzbekistan", "chart_of_accounts": "Standard",
    })
    year = today()[:4]
    _get_or_insert("Fiscal Year", year, {
        "year": year, "year_start_date": f"{year}-01-01", "year_end_date": f"{year}-12-31",
    })
    customer = _get_or_insert("Customer", "Synthetic P1 Customer", {
        "customer_name": "Synthetic P1 Customer", "customer_type": "Company",
        # ERPNext rejects group (tree parent) customer groups on Customer; use fixture leaves.
        "customer_group": "Commercial", "territory": "Uzbekistan",
    })
    sales = _user("sales@av-prototype.invalid", "Prototype Sales", ["Sales User", "AV Sales"],
                  os.environ.get("AV_SALES_PASSWORD"))
    pm = _user("pm@av-prototype.invalid", "Prototype PM", ["Projects User", "AV Project Manager"],
               os.environ.get("AV_PM_PASSWORD"))
    _get_or_insert("Price List", "AV Prototype USD", {
        "price_list_name": "AV Prototype USD", "selling": 1, "currency": "USD", "enabled": 1,
    })
    # ERPNext 16 refuses has_serial_no on Item until serial/batch tracking is activated.
    frappe.db.set_single_value("Stock Settings", "enable_serial_and_batch_no_for_item", 1)
    for code, label, stock in (
        ("AVP-M", "Synthetic serial device M", 1),
        ("AVP-SERVICES", "Synthetic P1 services", 0),
        ("AVP-ALTERNATIVE", "Synthetic unselected alternative", 0),
    ):
        _get_or_insert("Item", code, {
            "item_code": code, "item_name": label, "item_group": "All Item Groups",
            "stock_uom": "Nos", "is_stock_item": stock, "has_serial_no": stock,
        })
    # Standard ERPNext alternative rows are excluded from quotation totals.
    # This slice accepts the main scope; choosing an alternative requires a new issued quote.
    quotes = {}
    for revision, lines in (
        ("Q1", [("AVP-M", 4, 2000, 0), ("AVP-SERVICES", 1, 7000, 0)]),
        ("Q2", [("AVP-M", 4, 2000, 0), ("AVP-ALTERNATIVE", 4, 2000, 1),
                ("AVP-SERVICES", 1, 8000, 0)]),
    ):
        marker = f"AV-PROTOTYPE-T1-{revision}"
        existing = frappe.db.exists("Quotation", {"title": marker})
        if existing:
            quote = frappe.get_doc("Quotation", existing)
        else:
            quote = frappe.get_doc({
                "doctype": "Quotation", "title": marker, "quotation_to": "Customer",
                "party_name": customer.name, "company": company.name, "currency": "USD",
                "conversion_rate": 1, "selling_price_list": "AV Prototype USD",
                "price_list_currency": "USD", "plc_conversion_rate": 1,
                "transaction_date": today(), "valid_till": add_days(today(), 30),
                "order_type": "Sales", "ignore_pricing_rule": 1,
                "items": [{"item_code": code, "qty": qty, "rate": rate, "is_alternative": alternative}
                          for code, qty, rate, alternative in lines],
                "terms": f"SYNTHETIC ONLY. {marker}. No taxes for arithmetic test. Rooms A and B.",
            }).insert()
            quote.submit()
        quotes[revision] = quote.name
    if frappe.get_doc("Quotation", quotes["Q2"]).grand_total != 16000:
        frappe.throw("Seed Q2 does not match the T1 accepted value of 16000. Inspect configuration.")
    existing_handover = frappe.db.exists("AV Handover", {"quotation": quotes["Q2"]})
    if existing_handover:
        handover = frappe.get_doc("AV Handover", existing_handover)
    else:
        # Switch identity; ownership and permission checks exercise the Sales account.
        frappe.set_user(sales)
        try:
            handover = frappe.get_doc({
                "doctype": "AV Handover", "quotation": quotes["Q2"],
                "project_name": "Synthetic P1 — Rooms A/B", "project_manager": pm,
                "customer_approval_reference": "SYNTHETIC: T1 step 1, Q2 main scope accepted, 2026-11-05.",
            }).insert()
            handover.submit()
        finally:
            frappe.set_user("Administrator")
    board_project = _seed_board(company.name, customer.name, pm)
    frappe.db.set_single_value("Global Defaults", "default_company", company.name)
    frappe.db.set_single_value("Global Defaults", "default_currency", "USD")
    frappe.db.set_single_value("System Settings", "time_zone", "Asia/Tashkent")
    frappe.db.set_single_value("System Settings", "setup_complete", 1)
    return {"synthetic": True, "quotations": quotes, "handover": handover.name,
            "sales_user": sales, "pm_user": pm, "accepted_value": 16000,
            "review_status": handover.review_status, "board_project": board_project}


# (subject, stage, room, system, start offset, end offset, block reason, depends on subject)
BOARD_TASKS = (
    ("Обследование помещений A и B", "done", "A, B", None, -14, -10, None, None),
    ("Схема видеотракта", "review", "A", "Видео", -9, -2, None, None),
    ("Кабельная ведомость", "in_progress", "A, B", "Кабельные линии", -5, 3, None, None),
    ("Монтаж дисплеев", "ready", "A", "Видео", 4, 8, None, "Схема видеотракта"),
    ("Монтаж акустики", "planned", "B", "Аудио", 6, 9,
     "Нет подтверждённой даты поставки акустики", None),
    ("Программирование контроллера", "planned", "A, B", "Управление", 10, 15, None, None),
    ("Проверка звукового поля", "planned", "B", "Аудио", None, None, None, "Монтаж акустики"),
    ("Подготовка исполнительной документации", "planned", None, None, None, None, None, None),
)


def _seed_board(company, customer, pm):
    """Synthetic project with tasks in every board stage (PM-01); the PM is a project member."""
    from frappe.desk.form import assign_to

    marker = "AV-PROTOTYPE-T1 Board"
    project_name = frappe.db.exists("Project", {"project_name": marker})
    if not project_name:
        project_name = frappe.get_doc({
            "doctype": "Project", "project_name": marker, "company": company,
            "customer": customer, "status": "Open", "users": [{"user": pm}],
        }).insert().name
    names = {}
    for subject, stage, room, system, start, end, block, depends in BOARD_TASKS:
        existing = frappe.db.exists("Task", {"project": project_name, "subject": subject})
        if existing:
            names[subject] = existing
            continue
        task = frappe.get_doc({
            "doctype": "Task", "subject": subject, "project": project_name, "company": company,
            "av_stage": stage, "av_room": room, "av_system": system, "av_block_reason": block,
            "exp_start_date": add_days(today(), start) if start is not None else None,
            "exp_end_date": add_days(today(), end) if end is not None else None,
            "depends_on": [{"task": names[depends]}] if depends else [],
        }).insert()
        names[subject] = task.name
        if stage != "done":
            assign_to.add({"assign_to": [pm], "doctype": "Task", "name": task.name,
                           "description": subject})
    return project_name
