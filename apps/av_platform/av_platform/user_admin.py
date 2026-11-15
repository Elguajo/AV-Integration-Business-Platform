"""System administrator and moderator roles (ADM-01, MVP-SPEC §3 "Администратор").

AV Administrator is the product role for full system administration and always carries the
standard System Manager role. Administrative access is not a business approval: accepting a
handover and similar decisions still need their own roles.

AV Moderator manages staff accounts: creates users, enables and disables them and grants or
removes the work roles in MODERATOR_ROLES. Frappe 16 gives User access only to System Manager,
and a role with write access to User roles could grant itself any role; so the moderator gets
User rights through Custom DocPerm and every change goes through `guard_user_change`, which runs
in User.before_validate for the Desk form, REST, child-row insert/delete, bulk edit and import.
"""

import json

import frappe
from frappe import _
from frappe.model import no_value_fields, table_fields
from frappe.permissions import AUTOMATIC_ROLES, add_permission, update_permission_property
from frappe.utils import cint, cstr, flt, get_datetime, getdate

ADMIN_ROLE = "AV Administrator"
MODERATOR_ROLE = "AV Moderator"
SYSTEM_MANAGER = "System Manager"

# Work roles a moderator may grant or remove. Everything else stays with administrators.
MODERATOR_ROLES = frozenset({"AV Sales", "Sales User", "AV Project Manager", "Projects User", "AV Director"})
# Accounts holding these roles are changed only by administrators (a moderator keeps self-service).
PROTECTED_ROLES = frozenset({"Administrator", SYSTEM_MANAGER, ADMIN_ROLE, MODERATOR_ROLE})
# Fields a moderator may set on another account, besides the roles table. Password, API keys,
# login hours, IP limits, module access, role profiles and e-mail accounts are not among them.
MODERATOR_FIELDS = frozenset({
    "enabled", "email", "first_name", "middle_name", "last_name", "full_name", "username",
    "language", "time_zone", "user_image", "gender", "phone", "mobile_no", "birth_date",
    "location", "send_welcome_email",
})
# On its own account a moderator has User write at permlevel 1, which a plain user lacks.
SELF_LOCKED_EXTRA = frozenset({"module_profile", "bypass_restrict_ip_check_if_2fa_enabled"})

MODERATOR_PERMS = ((0, ("read", "write", "create", "report")), (1, ("read", "write")))
# A new Custom DocPerm row grants export by default; the staff list is not exported.
MODERATOR_DENIED = ("export", "print", "email", "share", "import", "delete", "impersonate")


def ensure_setup():
    """Idempotent: both roles and the moderator's User rules (after install and every migrate)."""
    for role in (ADMIN_ROLE, MODERATOR_ROLE):
        if not frappe.db.exists("Role", role):
            frappe.get_doc({"doctype": "Role", "role_name": role, "desk_access": 1}).insert(
                ignore_permissions=True)
    for permlevel, ptypes in MODERATOR_PERMS:
        # The first custom rule copies the standard User rules (Frappe behaviour, same as the
        # Role Permission Manager); System Manager keeps exactly what it had.
        if not frappe.db.exists("Custom DocPerm", {"parent": "User", "role": MODERATOR_ROLE,
                                                   "permlevel": permlevel, "if_owner": 0}):
            add_permission("User", MODERATOR_ROLE, permlevel, "read")
        for ptype in ptypes:
            update_permission_property("User", MODERATOR_ROLE, permlevel, ptype, 1)
        for ptype in MODERATOR_DENIED:
            update_permission_property("User", MODERATOR_ROLE, permlevel, ptype, 0)


def _roles(doc):
    return {row.role for row in doc.get("roles") or []} - set(AUTOMATIC_ROLES)


def _scalar(value, df):
    if value in (None, ""):
        return None
    if df.fieldtype in ("Check", "Int"):
        return cint(value)
    if df.fieldtype in ("Float", "Currency", "Percent"):
        return flt(value)
    if df.fieldtype == "Date":
        return getdate(value)
    if df.fieldtype == "Datetime":
        return get_datetime(value)
    return cstr(value)


def _rows(doc, df):
    rows = []
    for row in doc.get(df.fieldname) or []:
        data = row.as_dict(no_default_fields=True, no_child_table_fields=True)
        rows.append(json.dumps({k: v for k, v in data.items()
                                if not k.startswith("__") and v not in (None, "")},
                               sort_keys=True, default=str))
    return sorted(rows)


def _changed_fields(doc, before):
    changed = set()
    for df in doc.meta.fields:
        if df.is_virtual:
            continue
        # Checked before no_value_fields: Frappe lists table types among them.
        if df.fieldtype in table_fields:
            if _rows(doc, df) != _rows(before, df):
                changed.add(df.fieldname)
        elif df.fieldtype in no_value_fields:
            continue
        elif _scalar(doc.get(df.fieldname), df) != _scalar(before.get(df.fieldname), df):
            changed.add(df.fieldname)
    return changed


def _moderates(user):
    """True when the user changes accounts only through the moderator rights."""
    if user == "Administrator":
        return False
    roles = set(frappe.get_roles(user))
    return MODERATOR_ROLE in roles and SYSTEM_MANAGER not in roles


def _deny(message):
    frappe.throw(message, frappe.PermissionError, title=_("Not permitted"))


def guard_user_change(doc, method=None):
    """User.before_validate: limit moderators, then keep System Manager with AV Administrator."""
    user = frappe.session.user
    if _moderates(user):
        _check_moderator_change(doc, user)
    if ADMIN_ROLE in _roles(doc) and SYSTEM_MANAGER not in _roles(doc):
        doc.append("roles", {"role": SYSTEM_MANAGER})


def _check_moderator_change(doc, user):
    if doc.is_new():
        before = frappe.new_doc("User")
    else:
        # Decided on the stored record, never on what the request claims.
        before = frappe.get_doc("User", doc.name)
    old_roles, new_roles = _roles(before), _roles(doc)
    changed = _changed_fields(doc, before) - {"roles"}

    if not doc.is_new() and doc.name == user:
        if old_roles != new_roles:
            _deny(_("A moderator cannot change their own roles."))
        locked = {df.fieldname for df in doc.meta.fields if df.permlevel} | SELF_LOCKED_EXTRA
        if changed & locked:
            _deny(_("A moderator cannot change access settings of their own account: {0}.").format(
                ", ".join(sorted(changed & locked))))
        return

    if old_roles & PROTECTED_ROLES:
        _deny(_("Only an administrator can change an administrator or moderator account."))
    outside = (old_roles ^ new_roles) - MODERATOR_ROLES
    if outside:
        _deny(_("A moderator can grant or remove only work roles. Not allowed: {0}.").format(
            ", ".join(sorted(outside))))
    if changed - MODERATOR_FIELDS:
        _deny(_("A moderator cannot change these fields of another account: {0}.").format(
            ", ".join(sorted(changed - MODERATOR_FIELDS))))
