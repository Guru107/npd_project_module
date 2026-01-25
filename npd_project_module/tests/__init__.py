# Copyright (c) 2025, Guru107 and contributors
# For license information, please see license.txt

import frappe


def before_tests():
	"""Set up test environment for NPD Project Module."""
	frappe.clear_cache()

	# Ensure Transit Warehouse Type exists (required for Company default warehouses)
	# This must be created before Company records are created, as Company.on_update()
	# tries to create default warehouses that reference this Warehouse Type
	ensure_transit_warehouse_type()

	frappe.db.commit()
	frappe.clear_cache()


def ensure_transit_warehouse_type():
	"""Ensure 'Transit' Warehouse Type exists (required for Company default warehouses)."""
	try:
		frappe.reload_doc("stock", "doctype", "warehouse_type")
		if not frappe.db.exists("Warehouse Type", "Transit"):
			doc = frappe.new_doc("Warehouse Type")
			doc.name = "Transit"
			doc.insert(ignore_permissions=True)
			frappe.db.commit()
	except Exception as exc:
		frappe.log_error(
			message=f"Failed to create Transit Warehouse Type: {exc}",
			title="NPD Project Module Test Setup - Warehouse Type",
		)
		# Re-raise to make test failures visible
		raise


global_test_dependencies = ["User", "Company", "Item", "Project Template"]
