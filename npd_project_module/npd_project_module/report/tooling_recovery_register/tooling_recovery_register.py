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

from npd_project_module.npd_project_module.doctype.npd_tooling.npd_tooling import (
	compute_recovered,
	compute_recovery_status,
	get_tool_po_status,
)


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
				"tool_status": get_tool_po_status(tool.supplier_po, tool.tool_item),
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

	Recovered mirrors the doctype controller: money paid against the linked Sales Invoices
	(ERPNext handles bulk allocation) plus manual advance allocations not yet applied to
	those invoices. Invoiced = billed grand totals (reference). Outstanding = total tooling
	amount minus recovered.
	"""
	order_names = list(order_info.keys())

	# Linked invoices per order, with live figures.
	order_invoices, si_figures = _linked_invoices(order_names)
	# Linked manual payment allocations per order.
	order_payments = _linked_payments(order_names)
	# Which Payment Entries are applied to which of our linked invoices.
	pe_to_invoices = _payment_references(order_payments, si_figures)

	recovery = {}
	for order_name, order in order_info.items():
		sis = order_invoices.get(order_name, set())
		invoice_figures = [si_figures[s] for s in sis if s in si_figures]
		invoiced = sum(flt(gt) for gt, _out in invoice_figures)

		payments = order_payments.get(order_name, [])
		on_invoice = {pe for pe, _amt in payments if pe_to_invoices.get(pe, set()) & sis}

		recovered = compute_recovered(invoice_figures, payments, on_invoice)
		target = flt(order.total_tooling_amount)
		recovery[order_name] = {
			"invoiced": invoiced,
			"recovered": recovered,
			"outstanding": max(target - flt(recovered), 0),
			"recovery_status": compute_recovery_status(target, recovered),
		}
	return recovery


def _linked_invoices(order_names):
	"""Return ({order: {sales_invoice}}, {sales_invoice: (grand_total, outstanding)})."""
	links = frappe.get_all(
		"NPD Tooling Invoice",
		filters={"parent": ["in", order_names], "parenttype": "NPD Tooling"},
		fields=["parent", "sales_invoice"],
	)
	order_invoices = {}
	all_si = set()
	for link in links:
		if not link.sales_invoice:
			continue
		order_invoices.setdefault(link.parent, set()).add(link.sales_invoice)
		all_si.add(link.sales_invoice)

	si_figures = {}
	if all_si:
		for r in frappe.get_all(
			"Sales Invoice",
			filters={"name": ["in", list(all_si)]},
			fields=["name", "grand_total", "outstanding_amount"],
		):
			si_figures[r.name] = (r.grand_total, r.outstanding_amount)
	return order_invoices, si_figures


def _linked_payments(order_names):
	"""Return {order: [(payment_entry, allocated_amount), ...]}."""
	rows = frappe.get_all(
		"NPD Tooling Payment",
		filters={"parent": ["in", order_names], "parenttype": "NPD Tooling"},
		fields=["parent", "payment_entry", "allocated_amount"],
	)
	order_payments = {}
	for row in rows:
		if not row.payment_entry:
			continue
		order_payments.setdefault(row.parent, []).append((row.payment_entry, row.allocated_amount))
	return order_payments


def _payment_references(order_payments, si_figures):
	"""Return {payment_entry: {sales_invoice}} for our linked PEs against our linked invoices."""
	all_pe = {pe for payments in order_payments.values() for pe, _amt in payments}
	all_si = set(si_figures.keys())
	if not all_pe or not all_si:
		return {}
	pe_to_invoices = {}
	for r in frappe.get_all(
		"Payment Entry Reference",
		filters={
			"parent": ["in", list(all_pe)],
			"reference_doctype": "Sales Invoice",
			"reference_name": ["in", list(all_si)],
		},
		fields=["parent", "reference_name"],
	):
		pe_to_invoices.setdefault(r.parent, set()).add(r.reference_name)
	return pe_to_invoices
