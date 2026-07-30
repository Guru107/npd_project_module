# Copyright (c) 2026, Guru107 and contributors
# For license information, please see license.txt

"""Server-side helpers for the NPD Tooling doctype."""

import frappe

from npd_project_module.npd_project_module.doctype.npd_tooling.npd_tooling import get_tool_po_statuses


@frappe.whitelist()
def refresh_tool_statuses(tooling: str):
	"""Re-derive each tool line's status from its Supplier PO line and store it.

	Lets users pull the latest without editing the order — useful when a PO's receipt
	state changed after the tooling order was last saved. Returns how many rows changed.
	"""
	# Writes derived values onto the order's child rows, so require write permission.
	frappe.has_permission("NPD Tooling", "write", doc=tooling, throw=True)

	rows = frappe.get_all(
		"NPD Tooling Item",
		filters={"parent": tooling, "parenttype": "NPD Tooling"},
		fields=["name", "supplier_po", "tool_item", "tool_status"],
	)
	statuses = get_tool_po_statuses((r.supplier_po, r.tool_item) for r in rows)

	updated = 0
	for r in rows:
		status = statuses.get((r.supplier_po, r.tool_item))
		if status != r.tool_status:
			frappe.db.set_value("NPD Tooling Item", r.name, "tool_status", status, update_modified=False)
			updated += 1

	if updated:
		frappe.clear_document_cache("NPD Tooling", tooling)

	return {"updated": updated}
