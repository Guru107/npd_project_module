# Copyright (c) 2025, Guru107 and contributors
# For license information, please see license.txt

"""
Test setup utilities for NPD Project Module tests.
Provides bootstrapping of site-local ERPNext test records for deterministic local/CI runs.
"""

from __future__ import annotations

import frappe


def _run_erpnext_test_bootstrap() -> None:
	"""Run ERPNext's standard test-record bootstrap, across ERPNext v15 and v16.

	ERPNext v15 exposes ``erpnext.setup.utils.before_tests``; v16 removed it in favour
	of the shared setup-wizard flow. Import lazily so the module loads on both versions.
	"""
	try:
		from erpnext.setup.utils import before_tests as erpnext_before_tests

		erpnext_before_tests()
		return
	except ImportError:
		pass

	# ERPNext v16: run the setup wizard directly, then apply test defaults if available.
	from frappe.desk.page.setup_wizard.setup_wizard import setup_complete
	from frappe.utils.data import now_datetime

	current_year = now_datetime().year
	setup_complete(
		{
			"currency": "USD",
			"full_name": "Test User",
			"company_name": "Wind Power LLC",
			"timezone": "America/New_York",
			"company_abbr": "WP",
			"industry": "Manufacturing",
			"country": "United States",
			"fy_start_date": f"{current_year}-01-01",
			"fy_end_date": f"{current_year}-12-31",
			"language": "english",
			"company_tagline": "Testing",
			"email": "test@erpnext.com",
			"password": "test",
			"chart_of_accounts": "Standard",
		}
	)

	try:
		from erpnext.setup.utils import enable_all_roles_and_domains, set_defaults_for_tests

		enable_all_roles_and_domains()
		set_defaults_for_tests()
	except ImportError:
		pass

	frappe.db.commit()  # nosemgrep


def _warehouse_exists() -> bool:
	"""Check if any All Warehouses root warehouse exists (with or without company suffix)."""
	# ERPNext creates warehouses with company suffix, e.g., "All Warehouses - _TC"
	exists = frappe.get_all("Warehouse", filters={"name": ("like", "All Warehouses%")}, limit=1)
	return bool(exists)


def before_tests() -> None:
	"""Bootstrap site-local ERPNext test records for deterministic local/CI runs."""
	# Run ERPNext's standard test fixtures setup
	if not frappe.db.exists("Company", None):
		_run_erpnext_test_bootstrap()

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
