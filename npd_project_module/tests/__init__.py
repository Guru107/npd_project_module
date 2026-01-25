# Copyright (c) 2025, Guru107 and contributors
# For license information, please see license.txt

from functools import partial

import frappe
from erpnext.accounts.utils import get_fiscal_year
from frappe.desk.page.setup_wizard.setup_wizard import setup_complete
from frappe.utils import getdate
from frappe.utils.nestedset import get_root_of


def before_tests():
	"""Set up test environment for NPD Project Module."""
	frappe.clear_cache()

	# Ensure Transit Warehouse Type exists (required for Company default warehouses)
	# This must be created before Company records are created, as Company.on_update()
	# tries to create default warehouses that reference this Warehouse Type
	ensure_transit_warehouse_type()

	if not frappe.db.a_row_exists("Company"):
		today = getdate()
		year = today.year if today.month > 3 else today.year - 1

		setup_complete(
			{
				"currency": "INR",
				"full_name": "Test User",
				"company_name": "Wind Power LLP",
				"timezone": "Asia/Kolkata",
				"company_abbr": "WP",
				"industry": "Manufacturing",
				"country": "India",
				"fy_start_date": f"{year}-04-01",
				"fy_end_date": f"{year + 1}-03-31",
				"language": "English",
				"company_tagline": "Testing",
				"email": "test@example.com",
				"password": "test",
				"chart_of_accounts": "Standard",
			}
		)

		add_company_to_fiscal_year("Wind Power LLP")

	set_default_settings_for_tests()
	set_default_company_for_tests()
	frappe.db.commit()

	frappe.flags.country = "India"
	frappe.flags.skip_test_records = True
	frappe.enqueue = partial(frappe.enqueue, now=True)


def ensure_transit_warehouse_type():
	"""Ensure 'Transit' Warehouse Type exists (required for Company default warehouses)."""
	frappe.reload_doc("stock", "doctype", "warehouse_type")
	if not frappe.db.exists("Warehouse Type", "Transit"):
		doc = frappe.new_doc("Warehouse Type")
		doc.name = "Transit"
		doc.insert(ignore_permissions=True)
		frappe.db.commit()


def set_default_settings_for_tests():
	"""Set default settings required for NPD Project Module tests."""
	# Set default groups (like ERPNext and india_compliance)
	for key in ("Customer Group", "Supplier Group", "Item Group", "Territory"):
		frappe.db.set_default(frappe.scrub(key), get_root_of(key))

	# Allow Negative Stock
	frappe.db.set_single_value("Stock Settings", "allow_negative_stock", 1)


def set_default_company_for_tests():
	"""Set default company and configure it for tests."""
	company_name = "Wind Power LLP"
	if not frappe.db.exists("Company", company_name):
		return

	# Stock settings
	frappe.db.set_value(
		"Company",
		company_name,
		{
			"enable_perpetual_inventory": 1,
			"default_inventory_account": "Stock In Hand - WP",
			"stock_adjustment_account": "Stock Adjustment - WP",
			"stock_received_but_not_billed": "Stock Received But Not Billed - WP",
		},
	)

	# Set default company
	global_defaults = frappe.get_single("Global Defaults")
	global_defaults.default_company = company_name
	global_defaults.save()


def add_company_to_fiscal_year(company_name):
	"""Add company to the current fiscal year."""
	fy = get_fiscal_year(getdate(), as_dict=True)
	if not fy:
		return

	doc = frappe.get_doc("Fiscal Year", fy.name)
	fy_companies = [row.company for row in doc.companies]

	if company_name not in fy_companies:
		doc.append("companies", {"company": company_name})
		doc.save(ignore_permissions=True)


global_test_dependencies = ["User", "Company", "Item", "Project Template"]
