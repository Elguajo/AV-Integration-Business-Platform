import frappe

OLD_MODULE = "AV Platform"


def execute():
    """The single "AV Platform" module was split into AV Sales and AV Projects (modules.txt).

    Migrate registers the new modules and moves the DocTypes before this runs; the old Module Def
    is then empty. It is deleted only if nothing on the site still refers to it.
    """
    if not frappe.db.exists("Module Def", OLD_MODULE):
        return
    for doctype, fieldname in _module_links():
        if frappe.db.exists(doctype, {fieldname: OLD_MODULE}):
            print(f"Module Def {OLD_MODULE!r} kept: {doctype}.{fieldname} still refers to it")
            return
    frappe.delete_doc("Module Def", OLD_MODULE, ignore_permissions=True)


def _module_links():
    """Every stored Link field that points to a Module Def."""
    fields = frappe.get_all(
        "DocField", filters={"fieldtype": "Link", "options": "Module Def"}, fields=["parent", "fieldname"]
    )
    fields += frappe.get_all(
        "Custom Field",
        filters={"fieldtype": "Link", "options": "Module Def"},
        fields=["dt as parent", "fieldname"],
    )
    for field in fields:
        doctype = frappe.db.get_value("DocType", field.parent, ["issingle", "is_virtual"], as_dict=True)
        if doctype and not doctype.issingle and not doctype.is_virtual:
            yield field.parent, field.fieldname
