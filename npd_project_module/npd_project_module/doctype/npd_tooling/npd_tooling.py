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
		"""Sum of amounts allocated to this PO across the payment rows."""
		return sum(flt(row.allocated_amount) for row in self.payments)

	def _get_invoiced_total(self):
		"""Sum of grand totals across linked Sales Invoices (computed live)."""
		invoice_names = [row.sales_invoice for row in self.invoices if row.sales_invoice]
		if not invoice_names:
			return 0
		rows = frappe.get_all(
			"Sales Invoice",
			filters={"name": ["in", invoice_names]},
			fields=["grand_total"],
		)
		return sum(flt(r.grand_total) for r in rows)


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
