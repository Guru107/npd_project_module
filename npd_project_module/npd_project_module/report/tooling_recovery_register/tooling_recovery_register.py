# Copyright (c) 2026, Guru107 and contributors
# For license information, please see license.txt

"""
Tooling Recovery Register

One row per tool, showing its customer PO ↔ supplier PO mapping, the tool's amount, and
the order-level recovery (aggregated across the customer PO's linked Sales Invoices) plus
ageing since the customer PO date. Answers "which tools map to which supplier PO, and has
the customer money been recovered — and for how long has it been outstanding".
"""

import frappe
from frappe import _
from frappe.utils import date_diff, flt, getdate, today

from npd_project_module.npd_project_module.doctype.npd_tooling.npd_tooling import compute_recovery_status


def execute(filters=None):
	filters = frappe._dict(filters or {})
	columns = get_columns()
	data = get_data(filters)
	return columns, data


def get_columns():
	return [
		{
			"label": _("Order"),
			"fieldname": "order",
			"fieldtype": "Link",
			"options": "NPD Tooling",
			"width": 130,
		},
		{
			"label": _("Project"),
			"fieldname": "project",
			"fieldtype": "Link",
			"options": "Project",
			"width": 120,
		},
		{
			"label": _("Part"),
			"fieldname": "part_number",
			"fieldtype": "Link",
			"options": "Item",
			"width": 120,
		},
		{
			"label": _("Tool Item"),
			"fieldname": "tool_item",
			"fieldtype": "Link",
			"options": "Item",
			"width": 120,
		},
		{"label": _("Description"), "fieldname": "description", "fieldtype": "Data", "width": 160},
		{"label": _("Tool Amount"), "fieldname": "amount", "fieldtype": "Currency", "width": 110},
		{
			"label": _("Supplier"),
			"fieldname": "supplier",
			"fieldtype": "Link",
			"options": "Supplier",
			"width": 120,
		},
		{
			"label": _("Supplier PO"),
			"fieldname": "supplier_po",
			"fieldtype": "Link",
			"options": "Purchase Order",
			"width": 130,
		},
		{"label": _("Tool Status"), "fieldname": "tool_status", "fieldtype": "Data", "width": 100},
		{
			"label": _("Customer"),
			"fieldname": "customer",
			"fieldtype": "Link",
			"options": "Customer",
			"width": 120,
		},
		{"label": _("Customer PO No"), "fieldname": "customer_po_no", "fieldtype": "Data", "width": 120},
		{"label": _("Customer PO Date"), "fieldname": "customer_po_date", "fieldtype": "Date", "width": 110},
		{"label": _("Ageing (Days)"), "fieldname": "ageing_days", "fieldtype": "Int", "width": 100},
		{"label": _("Order Invoiced"), "fieldname": "invoiced_amount", "fieldtype": "Currency", "width": 110},
		{
			"label": _("Order Recovered"),
			"fieldname": "amount_recovered",
			"fieldtype": "Currency",
			"width": 110,
		},
		{
			"label": _("Order Outstanding"),
			"fieldname": "outstanding_amount",
			"fieldtype": "Currency",
			"width": 110,
		},
		{"label": _("Recovery Status"), "fieldname": "recovery_status", "fieldtype": "Data", "width": 140},
	]


def get_data(filters):
	order_filters = {}
	if filters.get("project"):
		order_filters["project"] = filters.get("project")
	if filters.get("customer"):
		order_filters["customer"] = filters.get("customer")

	orders = frappe.get_all(
		"NPD Tooling",
		filters=order_filters,
		fields=["name", "project", "customer", "customer_po_no", "customer_po_date", "total_tooling_amount"],
	)
	if not orders:
		return []

	order_names = [o.name for o in orders]
	order_info = {o.name: o for o in orders}

	# Aggregate recovery per order from payments received and invoices billed.
	recovery = _compute_recovery(order_info)

	# Tool lines (optionally filtered by supplier).
	tool_filters = {"parent": ["in", order_names], "parenttype": "NPD Tooling"}
	if filters.get("supplier"):
		tool_filters["supplier"] = filters.get("supplier")

	tools = frappe.get_all(
		"NPD Tooling Item",
		filters=tool_filters,
		fields=[
			"parent",
			"part_number",
			"tool_item",
			"description",
			"amount",
			"supplier",
			"supplier_po",
			"tool_status",
		],
		order_by="parent asc, idx asc",
	)

	status_filter = filters.get("recovery_status")
	rows = []
	for tool in tools:
		order = order_info.get(tool.parent)
		if not order:
			continue
		rec = recovery.get(tool.parent, {})
		ageing = date_diff(today(), getdate(order.customer_po_date)) if order.customer_po_date else 0

		if status_filter and rec.get("recovery_status") != status_filter:
			continue

		rows.append(
			{
				"order": tool.parent,
				"project": order.project,
				"part_number": tool.part_number,
				"tool_item": tool.tool_item,
				"description": tool.description,
				"amount": tool.amount,
				"supplier": tool.supplier,
				"supplier_po": tool.supplier_po,
				"tool_status": tool.tool_status,
				"customer": order.customer,
				"customer_po_no": order.customer_po_no,
				"customer_po_date": order.customer_po_date,
				"ageing_days": ageing,
				"invoiced_amount": rec.get("invoiced", 0),
				"amount_recovered": rec.get("recovered", 0),
				"outstanding_amount": rec.get("outstanding", 0),
				"recovery_status": rec.get("recovery_status", "Pending"),
			}
		)

	return rows


def _compute_recovery(order_info):
	"""Return {order_name: {invoiced, recovered, outstanding, recovery_status}}.

	Recovered = money received (linked Payment Entries). Invoiced = billed (linked Sales
	Invoices, for reference). Outstanding = total tooling amount minus recovered.
	"""
	order_names = list(order_info.keys())
	# Recovered = amounts allocated to each PO on its payment rows (handles bulk receipts
	# split across POs). Invoiced = live grand totals of the linked Sales Invoices.
	recovered_by_order = _sum_child_field("NPD Tooling Payment", order_names, "allocated_amount")
	invoiced_by_order = _sum_child_amounts(
		"NPD Tooling Invoice", order_names, "sales_invoice", "Sales Invoice", "grand_total"
	)

	recovery = {}
	for order_name, order in order_info.items():
		recovered = recovered_by_order.get(order_name, 0)
		target = flt(order.total_tooling_amount)
		recovery[order_name] = {
			"invoiced": invoiced_by_order.get(order_name, 0),
			"recovered": recovered,
			"outstanding": max(target - flt(recovered), 0),
			"recovery_status": compute_recovery_status(target, recovered),
		}
	return recovery


def _sum_child_field(child_doctype, order_names, amount_field):
	"""Sum a numeric field stored directly on child rows, grouped by parent order."""
	totals = dict.fromkeys(order_names, 0)
	for row in frappe.get_all(
		child_doctype,
		filters={"parent": ["in", order_names], "parenttype": "NPD Tooling"},
		fields=["parent", amount_field],
	):
		totals[row.parent] = totals.get(row.parent, 0) + flt(row.get(amount_field))
	return totals


def _sum_child_amounts(child_doctype, order_names, link_field, link_doctype, amount_field):
	"""Sum a live amount from documents referenced by a child table, grouped by parent order."""
	links = frappe.get_all(
		child_doctype,
		filters={"parent": ["in", order_names], "parenttype": "NPD Tooling"},
		fields=["parent", link_field],
	)
	order_to_refs = {}
	all_refs = set()
	for link in links:
		ref = link.get(link_field)
		if not ref:
			continue
		order_to_refs.setdefault(link.parent, []).append(ref)
		all_refs.add(ref)

	amount_map = {}
	if all_refs:
		for row in frappe.get_all(
			link_doctype, filters={"name": ["in", list(all_refs)]}, fields=["name", amount_field]
		):
			amount_map[row.name] = flt(row.get(amount_field))

	totals = {}
	for order_name in order_names:
		totals[order_name] = sum(amount_map.get(ref, 0) for ref in order_to_refs.get(order_name, []))
	return totals
