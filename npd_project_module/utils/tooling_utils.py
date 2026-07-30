# Copyright (c) 2026, Guru107 and contributors
# For license information, please see license.txt

"""Server-side helpers for the NPD Tooling doctype."""

import frappe

from npd_project_module.npd_project_module.doctype.npd_tooling.npd_tooling import get_tool_po_status


@frappe.whitelist()
def refresh_tool_statuses(tooling):
	"""Re-derive each tool line's status from its Supplier PO line and store it.

	Lets users pull the latest without editing the order — useful when a PO's receipt
	state changed after the tooling order was last saved. Returns how many rows changed.
	"""
	# Writes derived values onto the order's child rows, so require write permission.
	frappe.has_permission("NPD Tooling", "write", doc=tooling, throw=True)

	updated = 0
	for row in frappe.get_all(
		"NPD Tooling Item",
		filters={"parent": tooling, "parenttype": "NPD Tooling"},
		fields=["name", "supplier_po", "tool_item", "tool_status"],
	):
		status = get_tool_po_status(row.supplier_po, row.tool_item)
		if status != row.tool_status:
			frappe.db.set_value("NPD Tooling Item", row.name, "tool_status", status, update_modified=False)
			updated += 1

	if updated:
		frappe.clear_document_cache("NPD Tooling", tooling)

	return {"updated": updated}
