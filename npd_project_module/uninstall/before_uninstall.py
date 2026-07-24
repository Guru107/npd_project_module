# Copyright (c) 2025, Guru107 and contributors
# For license information, please see license.txt

import frappe


def before_uninstall():
	"""
	Clean up custom fields, configurations, templates, reports, and doctypes before app uninstallation.
	This function is idempotent - it checks for existence before attempting deletion.
	"""
	print("NPD Project Module: Starting cleanup...")

	remove_custom_fields()
	remove_npd_template()
	remove_custom_report()
	remove_tooling_setup()
	remove_custom_doctype()
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
		{"dt": "Task", "fieldname": "stage_type"},
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


def remove_npd_template():
	"""
	Remove the NPD Template (Project Template) created by this module.
	"""
	template_name = "NPD Template"
	try:
		if frappe.db.exists("Project Template", template_name):
			# Check if template has tasks that belong to this module
			template = frappe.get_doc("Project Template", template_name)
			# Delete template tasks first (if they exist and are not linked to real projects)
			if template.tasks:
				for task_link in template.tasks:
					task_name = task_link.task
					# Check if task is used in any real project
					used_in_projects = frappe.db.count(
						"Task", filters={"name": task_name, "project": ["is", "set"]}
					)
					if not used_in_projects:
						# Task is only a template, safe to delete
						try:
							frappe.delete_doc("Task", task_name, force=True, ignore_permissions=True)
						except Exception:
							pass  # Task might already be deleted or in use

			# Delete the template itself
			frappe.delete_doc("Project Template", template_name, force=True, ignore_permissions=True)
			print(f"  ✓ Removed NPD Template: {template_name}")
	except Exception as e:
		print(f"  ✗ Error removing NPD Template: {e!s}")


def remove_custom_report():
	"""
	Remove the reports created by this module.
	"""
	reports_to_remove = ["Part Stage Matrix", "Tooling Recovery Register"]
	for report_name in reports_to_remove:
		try:
			if frappe.db.exists("Report", report_name):
				frappe.delete_doc(
					"Report", report_name, force=True, ignore_permissions=True, ignore_missing=True
				)
				print(f"  ✓ Removed custom report: {report_name}")
		except Exception as e:
			print(f"  ✗ Error removing report {report_name}: {e!s}")


def remove_tooling_setup():
	"""
	Remove supporting master data created for the NPD Tooling feature.

	Only removes the "Tooling" Item Group when it has no Items assigned, so tool Items
	created by users are never orphaned. The NPD Tooling doctype and its records are
	removed automatically by Frappe when the app is uninstalled.
	"""
	item_group = "Tooling"
	try:
		if frappe.db.exists("Item Group", item_group):
			items_in_group = frappe.db.count("Item", filters={"item_group": item_group})
			if items_in_group:
				print(f"  ⚠ Item Group '{item_group}' has {items_in_group} item(s); leaving it in place")
			else:
				frappe.delete_doc(
					"Item Group", item_group, force=True, ignore_permissions=True, ignore_missing=True
				)
				print(f"  ✓ Removed Item Group: {item_group}")
	except Exception as e:
		print(f"  ✗ Error removing Item Group {item_group}: {e!s}")


def remove_custom_doctype():
	"""
	Remove the Project Part Number child table doctype created by this module.
	Note: Frappe automatically removes doctypes when uninstalling the app,
	but we include this for explicit cleanup and verification.
	"""
	doctype_name = "Project Part Number"
	try:
		if frappe.db.exists("DocType", doctype_name):
			# Check if doctype has any data
			table_name = frappe.db.get_value("DocType", doctype_name, "name")
			if table_name:
				# Frappe will handle the actual deletion during uninstall
				# We just verify it exists and log
				print("  ✓ Project Part Number doctype will be removed by Frappe")
	except Exception as e:
		print(f"  ✗ Error checking doctype {doctype_name}: {e!s}")
