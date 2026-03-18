# Copyright (c) 2025, Guru107 and contributors
# For license information, please see license.txt

"""
Test setup utilities for NPD Project Module tests.
Provides bootstrapping of site-local ERPNext test records for deterministic local/CI runs.
"""

from __future__ import annotations

import frappe
from erpnext.setup.utils import before_tests as erpnext_before_tests


def _warehouse_exists() -> bool:
	"""Check if any All Warehouses root warehouse exists (with or without company suffix)."""
	# ERPNext creates warehouses with company suffix, e.g., "All Warehouses - _TC"
	exists = frappe.get_all("Warehouse", filters={"name": ("like", "All Warehouses%")}, limit=1)
	return bool(exists)


def before_tests() -> None:
	"""Bootstrap site-local ERPNext test records for deterministic local/CI runs."""
	# Run ERPNext's standard test fixtures setup
	if not frappe.db.exists("Company", None):
		erpnext_before_tests()

	# Ensure All Warehouses root exists (ERPNext may create with company suffix)
	if not _warehouse_exists():
		warehouse = frappe.get_doc(
			{
				"doctype": "Warehouse",
				"warehouse_name": "All Warehouses",
				"is_group": 1,
			}
		)
		warehouse.insert(ignore_permissions=True)

	# Ensure default company is set
	company = "_Test Company" if frappe.db.exists("Company", "_Test Company") else None
	if not company:
		company = frappe.db.get_value("Company", {}, "name", order_by="creation asc")
	if company:
		frappe.db.set_single_value("Global Defaults", "default_company", company)
		frappe.defaults.set_user_default("company", company)

	frappe.db.commit()  # nosemgrep
