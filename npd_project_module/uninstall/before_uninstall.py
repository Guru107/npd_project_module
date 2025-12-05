# Copyright (c) 2025, Guru107 and contributors
# For license information, please see license.txt

import frappe


def before_uninstall():
	"""
	Clean up custom fields and configurations before app uninstallation.
	"""
	print("NPD Project Module: Starting cleanup...")

	remove_custom_fields()
	frappe.db.commit()

	print("NPD Project Module: Cleanup completed successfully")


def remove_custom_fields():
	"""
	Remove custom fields created by this module.
	"""
	# Remove custom fields from Task, Project, and Item doctypes
	custom_fields_to_remove = [
		{"dt": "Task", "fieldname": "part_number"},
		{"dt": "Task", "fieldname": "iteration_number"},
		{"dt": "Project", "fieldname": "part_numbers_section"},
		{"dt": "Project", "fieldname": "part_numbers"},
		{"dt": "Item", "fieldname": "project"},
	]

	for field_info in custom_fields_to_remove:
		try:
			if frappe.db.exists(
				"Custom Field", {"dt": field_info["dt"], "fieldname": field_info["fieldname"]}
			):
				custom_field_name = frappe.db.get_value(
					"Custom Field", {"dt": field_info["dt"], "fieldname": field_info["fieldname"]}, "name"
				)
				frappe.delete_doc("Custom Field", custom_field_name, force=True)
				print(f"  ✓ Removed custom field: {field_info['dt']}.{field_info['fieldname']}")
		except Exception as e:
			print(f"  ✗ Error removing custom field {field_info['dt']}.{field_info['fieldname']}: {e!s}")

	# Clear cache after removing fields
	frappe.clear_cache(doctype="Task")
	frappe.clear_cache(doctype="Project")
	frappe.clear_cache(doctype="Item")
	print("  ✓ Cache cleared for Task, Project, and Item doctypes")
