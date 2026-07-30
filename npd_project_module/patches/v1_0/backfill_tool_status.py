# Copyright (c) 2026, Guru107 and contributors
# For license information, please see license.txt

"""
Re-derive tool_status on existing NPD Tooling lines.

tool_status changed from a manual Select (Draft / PO Issued / In Development / Received /
Cancelled) to a read-only value derived from the matching Supplier PO line item. This
backfills existing rows so legacy values (e.g. "PO Issued", "In Development") are replaced
with the derived status; rows without a Supplier PO are cleared.
"""

import frappe

from npd_project_module.npd_project_module.doctype.npd_tooling.npd_tooling import get_tool_po_status


def execute():
	for row in frappe.get_all(
		"NPD Tooling Item",
		fields=["name", "supplier_po", "tool_item", "tool_status"],
	):
		status = get_tool_po_status(row.supplier_po, row.tool_item)
		if status != row.tool_status:
			frappe.db.set_value("NPD Tooling Item", row.name, "tool_status", status, update_modified=False)
