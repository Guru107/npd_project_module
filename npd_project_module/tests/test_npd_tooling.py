# Copyright (c) 2026, Guru107 and contributors
# For license information, please see license.txt

"""
Unit tests for the NPD Tooling order doctype and Tooling Recovery Register report.

An NPD Tooling record is a customer-PO tooling order with child tool lines (a part can
need several tools, each possibly from a different supplier). Recovery combines money paid
against linked Sales Invoices with manual advance allocations (for receipts not yet on an
invoice), versus the total tooling amount, so it counts even before a tax invoice exists
and never double-counts. The double-count-free combination is unit-tested purely; order
totals, ageing, and manual-allocation recovery are tested end-to-end, with the Payment
Entry helper skipping gracefully if the site lacks the accounting fixtures.
"""

import frappe
from frappe.utils import add_days, today

from npd_project_module.npd_project_module.doctype.npd_tooling.npd_tooling import (
	compute_recovered,
	compute_recovery_status,
)
from npd_project_module.npd_project_module.report.tooling_recovery_register.tooling_recovery_register import (
	execute as run_recovery_register,
)
from npd_project_module.tests.utils import (
	NPDProjectModuleTestSuite,
	cleanup_test_data,
	make_test_item,
	make_test_project_with_parts,
)


class TestNPDTooling(NPDProjectModuleTestSuite):
	"""Test cases for the NPD Tooling order controller."""

	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		from npd_project_module.install.after_install import create_tooling_setup

		create_tooling_setup()
		frappe.db.commit()

	def setUp(self):
		super().setUp()
		self.test_items = []
		self.test_projects = []
		self.test_tooling = []

	def tearDown(self):
		for name in self.test_tooling:
			try:
				frappe.delete_doc("NPD Tooling", name, force=True, ignore_permissions=True)
			except Exception:
				pass
		for project_name in self.test_projects:
			cleanup_test_data(project_name=project_name)
		cleanup_test_data(item_codes=[item.item_code for item in self.test_items])
		super().tearDown()

	def _make_order(self, tools=None, **kwargs):
		"""Create an NPD Tooling order. `tools` is a list of dicts for child rows."""
		part = make_test_item("_Test Tooling Part")
		project = make_test_project_with_parts("_Test Tooling Project", [part.item_code])
		self.test_items.append(part)
		self.test_projects.append(project.project_name)

		if tools is None:
			tool = make_test_item("_Test Tool Item", item_group="Tooling")
			self.test_items.append(tool)
			tools = [{"part_number": part.item_code, "tool_item": tool.item_code, "qty": 1, "rate": 1000}]

		doc = frappe.get_doc(
			{
				"doctype": "NPD Tooling",
				"project": project.name,
				"customer": kwargs.get("customer"),
				"customer_po_no": kwargs.get("customer_po_no", "PO-TEST-001"),
				"customer_po_date": kwargs.get("customer_po_date"),
				"tools": tools,
			}
		)
		doc.insert(ignore_permissions=True)
		frappe.db.commit()
		self.test_tooling.append(doc.name)
		return doc

	def _company(self):
		return (
			frappe.db.get_default("company")
			or frappe.db.get_single_value("Global Defaults", "default_company")
			or (frappe.get_all("Company", pluck="name") or [None])[0]
		)

	def _make_customer(self):
		name = "_Test Tooling Customer"
		if not frappe.db.exists("Customer", name):
			frappe.get_doc(
				{
					"doctype": "Customer",
					"customer_name": name,
					"customer_group": frappe.db.get_value("Customer Group", {"is_group": 0}, "name"),
					"territory": frappe.db.get_value("Territory", {"is_group": 0}, "name"),
				}
			).insert(ignore_permissions=True)
			self.addCleanup(lambda: frappe.delete_doc("Customer", name, force=True, ignore_permissions=True))
		return name

	def _make_payment_entry(self, customer, amount, company):
		"""Create a customer receipt Payment Entry (kept as a draft to avoid GL / fiscal-year
		fixtures — recovery reads `paid_amount`, which is present on drafts). Skips gracefully
		if the environment cannot build one."""
		receivable = frappe.db.get_value("Company", company, "default_receivable_account")
		paid_to = frappe.db.get_value("Company", company, "default_cash_account") or frappe.db.get_value(
			"Company", company, "default_bank_account"
		)
		if not (receivable and paid_to):
			self.skipTest("Company default receivable/cash accounts not configured for Payment Entry test")
		try:
			pe = frappe.get_doc(
				{
					"doctype": "Payment Entry",
					"payment_type": "Receive",
					"party_type": "Customer",
					"party": customer,
					"company": company,
					"paid_from": receivable,
					"paid_to": paid_to,
					"paid_amount": amount,
					"received_amount": amount,
					"reference_no": "ADV-TEST",
					"reference_date": today(),
				}
			).insert(ignore_permissions=True)
		except Exception as e:
			self.skipTest(f"Payment Entry could not be created in this environment: {e}")
		self.addCleanup(self._delete_payment_entry, pe.name)
		return pe.name

	def _delete_payment_entry(self, name):
		try:
			frappe.delete_doc("Payment Entry", name, force=True, ignore_permissions=True)
		except Exception:
			pass

	def test_create_tooling_order(self):
		"""An order persists with its naming series and one tool line."""
		doc = self._make_order()
		self.assertTrue(doc.name.startswith("NPD-TOOL-"))
		reloaded = frappe.get_doc("NPD Tooling", doc.name)
		self.assertEqual(len(reloaded.tools), 1)
		self.assertEqual(reloaded.tools[0].tool_item, "_Test Tool Item")

	def test_line_amount_and_total(self):
		"""Line amount = qty x rate and the order total sums the lines."""
		part = make_test_item("_Test Tooling Part")
		tool_a = make_test_item("_Test Tool A", item_group="Tooling")
		tool_b = make_test_item("_Test Tool B", item_group="Tooling")
		self.test_items.extend([part, tool_a, tool_b])
		doc = self._make_order(
			tools=[
				{"part_number": part.item_code, "tool_item": tool_a.item_code, "qty": 2, "rate": 100},
				{"part_number": part.item_code, "tool_item": tool_b.item_code, "qty": 1, "rate": 350},
			]
		)
		self.assertEqual(doc.tools[0].amount, 200)
		self.assertEqual(doc.tools[1].amount, 350)
		self.assertEqual(doc.total_tooling_amount, 550)

	def test_multiple_tools_same_part(self):
		"""A single part can carry multiple tools on one order (stamping die set)."""
		part = make_test_item("_Test Tooling Part")
		tool_a = make_test_item("_Test Tool A", item_group="Tooling")
		tool_b = make_test_item("_Test Tool B", item_group="Tooling")
		self.test_items.extend([part, tool_a, tool_b])
		doc = self._make_order(
			tools=[
				{"part_number": part.item_code, "tool_item": tool_a.item_code, "qty": 1, "rate": 500},
				{"part_number": part.item_code, "tool_item": tool_b.item_code, "qty": 1, "rate": 500},
			]
		)
		self.assertEqual(len(doc.tools), 2)
		self.assertEqual({t.part_number for t in doc.tools}, {part.item_code})

	def test_tools_span_multiple_parts(self):
		"""One order can include tools for different parts."""
		part_a = make_test_item("_Test Part A")
		part_b = make_test_item("_Test Part B")
		tool_a = make_test_item("_Test Tool A", item_group="Tooling")
		tool_b = make_test_item("_Test Tool B", item_group="Tooling")
		self.test_items.extend([part_a, part_b, tool_a, tool_b])
		doc = self._make_order(
			tools=[
				{"part_number": part_a.item_code, "tool_item": tool_a.item_code, "qty": 1, "rate": 100},
				{"part_number": part_b.item_code, "tool_item": tool_b.item_code, "qty": 1, "rate": 100},
			]
		)
		self.assertEqual({t.part_number for t in doc.tools}, {part_a.item_code, part_b.item_code})

	def test_ageing_days_from_customer_po_date(self):
		"""Ageing counts days since the customer PO date."""
		doc = self._make_order(customer_po_date=add_days(today(), -30))
		self.assertEqual(doc.ageing_days, 30)

	def test_ageing_days_zero_without_date(self):
		"""Ageing is zero when no customer PO date is set."""
		doc = self._make_order()
		self.assertEqual(doc.ageing_days, 0)

	def test_recovery_defaults_without_payments(self):
		"""Without any receipts, recovery is Pending and the full tooling amount is outstanding."""
		doc = self._make_order()  # single tool line at rate 1000
		self.assertEqual(doc.recovery_status, "Pending")
		self.assertEqual(doc.amount_recovered, 0)
		self.assertEqual(doc.invoiced_amount, 0)
		self.assertEqual(doc.outstanding_amount, doc.total_tooling_amount)
		self.assertEqual(doc.outstanding_amount, 1000)

	def test_recovery_from_payments(self):
		"""Linked Payment Entries count as recovered — even before any invoice."""
		company = self._company()
		customer = self._make_customer()
		part = make_test_item("_Test Tooling Part")
		tool = make_test_item("_Test Tool Item", item_group="Tooling")
		project = make_test_project_with_parts("_Test Tooling Project", [part.item_code])
		self.test_items.extend([part, tool])
		self.test_projects.append(project.project_name)
		doc = frappe.get_doc(
			{
				"doctype": "NPD Tooling",
				"project": project.name,
				"customer": customer,
				"customer_po_no": "PO-PAY-001",
				"tools": [
					{"part_number": part.item_code, "tool_item": tool.item_code, "qty": 1, "rate": 1000}
				],
			}
		).insert(ignore_permissions=True)
		self.test_tooling.append(doc.name)

		# A partial advance receipt (no invoice yet).
		pe1 = self._make_payment_entry(customer, 400, company)
		doc.append("payments", {"payment_entry": pe1, "reference_milestone": "40% advance"})
		doc.save(ignore_permissions=True)
		doc.reload()
		self.assertEqual(doc.amount_recovered, 400)
		self.assertEqual(doc.outstanding_amount, 600)
		self.assertEqual(doc.recovery_status, "Partially Recovered")
		self.assertEqual(doc.invoiced_amount, 0)  # recovery counts without any invoice

		# The remaining balance received.
		pe2 = self._make_payment_entry(customer, 600, company)
		doc.append("payments", {"payment_entry": pe2, "reference_milestone": "balance"})
		doc.save(ignore_permissions=True)
		doc.reload()
		self.assertEqual(doc.amount_recovered, 1000)
		self.assertEqual(doc.outstanding_amount, 0)
		self.assertEqual(doc.recovery_status, "Fully Recovered")

	def test_bulk_payment_partial_allocation(self):
		"""A bulk receipt spanning several POs counts only for the portion allocated here."""
		company = self._company()
		customer = self._make_customer()
		part = make_test_item("_Test Tooling Part")
		tool = make_test_item("_Test Tool Item", item_group="Tooling")
		project = make_test_project_with_parts("_Test Tooling Project", [part.item_code])
		self.test_items.extend([part, tool])
		self.test_projects.append(project.project_name)
		doc = frappe.get_doc(
			{
				"doctype": "NPD Tooling",
				"project": project.name,
				"customer": customer,
				"customer_po_no": "PO-BULK-001",
				"tools": [
					{"part_number": part.item_code, "tool_item": tool.item_code, "qty": 1, "rate": 1000}
				],
			}
		).insert(ignore_permissions=True)
		self.test_tooling.append(doc.name)

		# One ₹1500 receipt covers several POs; only ₹400 of it is for this order.
		pe = self._make_payment_entry(customer, 1500, company)
		doc.append("payments", {"payment_entry": pe, "allocated_amount": 400})
		doc.save(ignore_permissions=True)
		doc.reload()

		self.assertEqual(doc.amount_recovered, 400)  # allocated slice, not the ₹1500 receipt
		self.assertEqual(doc.outstanding_amount, 600)
		self.assertEqual(doc.recovery_status, "Partially Recovered")
		self.assertEqual(doc.payments[0].paid_amount, 1500)  # full receipt captured for reference

	def test_report_lists_each_tool(self):
		"""The Tooling Recovery Register emits one row per tool with order-level context."""
		part_a = make_test_item("_Test Part A")
		part_b = make_test_item("_Test Part B")
		tool_1 = make_test_item("_Test Tool 1", item_group="Tooling")
		tool_2 = make_test_item("_Test Tool 2", item_group="Tooling")
		tool_3 = make_test_item("_Test Tool 3", item_group="Tooling")
		self.test_items.extend([part_a, part_b, tool_1, tool_2, tool_3])
		doc = self._make_order(
			customer_po_no="3200278423",
			customer_po_date=add_days(today(), -10),
			tools=[
				{"part_number": part_a.item_code, "tool_item": tool_1.item_code, "qty": 1, "rate": 100},
				{"part_number": part_a.item_code, "tool_item": tool_2.item_code, "qty": 1, "rate": 200},
				{"part_number": part_b.item_code, "tool_item": tool_3.item_code, "qty": 1, "rate": 300},
			],
		)

		_columns, data = run_recovery_register({"project": doc.project})
		# One row per tool line.
		our_rows = [r for r in data if r["order"] == doc.name]
		self.assertEqual(len(our_rows), 3)
		# Order-level context is carried on each row.
		self.assertTrue(all(r["customer_po_no"] == "3200278423" for r in our_rows))
		self.assertTrue(all(r["ageing_days"] == 10 for r in our_rows))
		self.assertTrue(all(r["recovery_status"] == "Pending" for r in our_rows))
		self.assertEqual({r["tool_item"] for r in our_rows}, {"_Test Tool 1", "_Test Tool 2", "_Test Tool 3"})


class TestRecoveryStatusLogic(NPDProjectModuleTestSuite):
	"""Pure-logic tests for recovery status: money received vs the tooling target."""

	def test_pending_when_nothing_received(self):
		self.assertEqual(compute_recovery_status(1000, 0), "Pending")

	def test_partially_recovered(self):
		self.assertEqual(compute_recovery_status(1000, 400), "Partially Recovered")

	def test_fully_recovered(self):
		self.assertEqual(compute_recovery_status(1000, 1000), "Fully Recovered")

	def test_fully_recovered_when_over_received(self):
		# Receipts including tax can exceed the basic tooling target.
		self.assertEqual(compute_recovery_status(1000, 1180), "Fully Recovered")

	def test_fully_recovered_within_rounding_tolerance(self):
		self.assertEqual(compute_recovery_status(1000, 999.995), "Fully Recovered")


class TestRecoveredComputation(NPDProjectModuleTestSuite):
	"""Pure-logic tests for combining invoice payments with manual advance allocations."""

	def test_advances_only_no_invoices(self):
		# No invoices linked: recovered is the sum of manual allocations.
		self.assertEqual(compute_recovered([], [("PE1", 400), ("PE2", 600)], set()), 1000)

	def test_invoice_paid_only(self):
		# Paid = grand_total - outstanding, summed over linked invoices.
		self.assertEqual(compute_recovered([(1000, 600)], [], set()), 400)

	def test_invoice_plus_standalone_advance(self):
		# An advance not applied to any linked invoice adds on top of invoice payments.
		self.assertEqual(compute_recovered([(1000, 600)], [("PE2", 200)], set()), 600)

	def test_advance_applied_to_invoice_not_double_counted(self):
		# PE1 is applied to the linked invoice (already in its outstanding), so its manual
		# allocation is skipped — recovered stays 400, not 800.
		self.assertEqual(compute_recovered([(1000, 600)], [("PE1", 400)], {"PE1"}), 400)

	def test_invoice_fully_paid(self):
		self.assertEqual(compute_recovered([(1000, 0)], [], set()), 1000)

	def test_unpaid_invoice_contributes_zero(self):
		# A fully-outstanding invoice means nothing has been recovered through it.
		self.assertEqual(compute_recovered([(1000, 1000)], [], set()), 0)
