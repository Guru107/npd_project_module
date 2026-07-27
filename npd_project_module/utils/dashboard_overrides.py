# Copyright (c) 2026, Guru107 and contributors
# For license information, please see license.txt

"""Dashboard (Connections) overrides for core doctypes."""

import frappe
from frappe import _


def get_project_dashboard_data(data):
	"""Add a "Tooling" group with NPD Tooling to the Project form's Connections.

	NPD Tooling links to Project through its `project` field, which matches the Project
	dashboard's default fieldname, so the connection count resolves automatically.
	"""
	data = frappe._dict(data or {})
	data.setdefault("transactions", [])

	if not _has_item(data.transactions, "NPD Tooling"):
		data.transactions.append({"label": _("Tooling"), "items": ["NPD Tooling"]})

	return data


def _has_item(transactions, doctype):
	"""True if `doctype` already appears in any transactions group (avoids duplicates)."""
	for group in transactions:
		if doctype in frappe._dict(group).get("items", []):
			return True
	return False
