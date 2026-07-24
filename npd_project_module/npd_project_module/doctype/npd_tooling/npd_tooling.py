# Copyright (c) 2026, Guru107 and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import date_diff, flt, getdate, today


class NPDTooling(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		customer: DF.Link | None
		customer_po_date: DF.Date | None
		customer_po_no: DF.Data
		invoices: DF.Table
		naming_series: DF.Literal["NPD-TOOL-.YYYY.-.####"]
		payments: DF.Table
		project: DF.Link
		remarks: DF.SmallText | None
		tools: DF.Table
		total_tooling_amount: DF.Currency
	# end: auto-generated types

	def validate(self):
		self._set_line_amounts_and_total()
		self._set_payment_allocations()

	def _set_line_amounts_and_total(self):
		"""Compute each tool line amount (qty x rate) and the order total."""
		total = 0
		for row in self.tools:
			row.amount = flt(row.qty) * flt(row.rate)
			total += flt(row.amount)
		self.total_tooling_amount = total

	def _set_payment_allocations(self):
		"""Default and sanity-check the amount allocated from each receipt to this PO.

		The customer often pays in bulk against several POs, so a Payment Entry's full
		amount is not necessarily for this order. Each row's `allocated_amount` is the slice
		applied here; it defaults to the full receipt and must not exceed it.
		"""
		for row in self.payments:
			if not row.payment_entry:
				continue
			received = flt(frappe.db.get_value("Payment Entry", row.payment_entry, "paid_amount"))
			row.paid_amount = received
			if not row.allocated_amount:
				row.allocated_amount = received
			elif flt(row.allocated_amount) > received + 0.01:
				frappe.msgprint(
					_("Payment {0}: allocated amount ({1}) exceeds the received amount ({2}).").format(
						row.payment_entry,
						frappe.format_value(row.allocated_amount, {"fieldtype": "Currency"}),
						frappe.format_value(received, {"fieldtype": "Currency"}),
					),
					indicator="orange",
					alert=True,
				)

	# --- Virtual fields (computed live, never stored) ---

	@property
	def ageing_days(self):
		"""Days elapsed since the customer PO date."""
		if not self.customer_po_date:
			return 0
		return date_diff(today(), getdate(self.customer_po_date))

	@property
	def invoiced_amount(self):
		"""Total billed to the customer so far (linked Sales Invoices)."""
		return self._get_invoiced_total()

	@property
	def amount_recovered(self):
		"""Money received and allocated to this PO across linked payments."""
		return self._get_recovered_total()

	@property
	def outstanding_amount(self):
		"""Tooling amount still to be recovered."""
		return max(flt(self.total_tooling_amount) - flt(self._get_recovered_total()), 0)

	@property
	def recovery_status(self):
		"""Recovery status from money received vs the total tooling amount."""
		return compute_recovery_status(self.total_tooling_amount, self._get_recovered_total())

	def _get_recovered_total(self):
		"""Money recovered against this PO.

		Combines money paid against the linked Sales Invoices (ERPNext allocates bulk
		receipts to specific invoices automatically) with manual advance allocations for
		receipts not yet applied to those invoices.
		"""
		invoice_names = [row.sales_invoice for row in self.invoices if row.sales_invoice]
		payment_allocations = [
			(row.payment_entry, row.allocated_amount) for row in self.payments if row.payment_entry
		]
		invoice_figures = _get_invoice_figures(invoice_names)
		on_invoice = _payments_applied_to_invoices([pe for pe, _amt in payment_allocations], invoice_names)
		return compute_recovered(invoice_figures, payment_allocations, on_invoice)

	def _get_invoiced_total(self):
		"""Sum of grand totals across linked Sales Invoices (billed reference, computed live)."""
		return sum(flt(gt) for gt, _out in _get_invoice_figures(self._invoice_names()))

	def _invoice_names(self):
		return [row.sales_invoice for row in self.invoices if row.sales_invoice]


def _get_invoice_figures(invoice_names):
	"""Return [(grand_total, outstanding_amount), ...] for the given Sales Invoices."""
	if not invoice_names:
		return []
	rows = frappe.get_all(
		"Sales Invoice",
		filters={"name": ["in", invoice_names]},
		fields=["grand_total", "outstanding_amount"],
	)
	return [(r.grand_total, r.outstanding_amount) for r in rows]


def _payments_applied_to_invoices(payment_entries, invoice_names):
	"""Return the set of Payment Entries that are applied to any of the given Sales Invoices.

	Money from these receipts is already reflected in the invoice outstanding, so it must
	not be double-counted from the manual allocation rows.
	"""
	if not payment_entries or not invoice_names:
		return set()
	refs = frappe.get_all(
		"Payment Entry Reference",
		filters={
			"parent": ["in", payment_entries],
			"reference_doctype": "Sales Invoice",
			"reference_name": ["in", invoice_names],
		},
		fields=["parent"],
	)
	return {r.parent for r in refs}


def compute_recovered(invoice_figures, payment_allocations, payments_on_invoice):
	"""Total money recovered against a tooling PO, double-count free.

	invoice_figures: iterable of (grand_total, outstanding_amount) for the linked invoices —
	        contributes the amount already paid (grand_total minus outstanding).
	payment_allocations: iterable of (payment_entry, allocated_amount) manual rows.
	payments_on_invoice: Payment Entries already applied to the linked invoices; their manual
	        allocation is skipped because that money is counted through the invoice above.
	"""
	invoice_paid = sum(max(flt(gt) - flt(out), 0) for gt, out in invoice_figures)
	on_invoice = set(payments_on_invoice or ())
	advances = sum(flt(amt) for pe, amt in payment_allocations if pe not in on_invoice)
	return invoice_paid + advances


def compute_recovery_status(target, recovered):
	"""Recovery status from money received (`recovered`) vs the tooling `target`.

	Pending when nothing is received; Fully Recovered once receipts reach the target
	(within a small tolerance); Partially Recovered otherwise.
	"""
	if flt(recovered) <= 0:
		return "Pending"
	if flt(target) > 0 and flt(recovered) >= flt(target) - 0.01:
		return "Fully Recovered"
	return "Partially Recovered"
