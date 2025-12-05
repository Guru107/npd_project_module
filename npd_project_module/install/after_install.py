# Copyright (c) 2025, Guru107 and contributors
# For license information, please see license.txt

import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields


def after_install():
	"""
	Setup custom fields and configurations after app installation.
	This function is idempotent - it checks for existing resources before creating.
	"""
	create_task_custom_fields()
	create_project_custom_fields()
	create_item_custom_fields()
	frappe.db.commit()
	print("NPD Project Module: Custom fields and configurations created successfully")


def create_task_custom_fields():
	"""
	Create custom fields for Task doctype to support part-based iteration management.
	"""
	custom_fields = {
		"Task": [
			{
				"fieldname": "part_number",
				"label": "Part Number",
				"fieldtype": "Link",
				"options": "Item",
				"insert_after": "project",
				"in_list_view": 1,
				"in_standard_filter": 1,
				"in_global_search": 1,
				"translatable": 0,
				"description": "Item (part) associated with this task"
			},
			{
				"fieldname": "iteration_number",
				"label": "Iteration Number",
				"fieldtype": "Int",
				"insert_after": "part_number",
				"in_list_view": 1,
				"in_standard_filter": 1,
				"read_only": 1,
				"default": "0",
				"non_negative": 1,
				"description": "Iteration number for this task (system-managed)"
			}
		]
	}

	# Create custom fields (function is idempotent - checks for existing fields)
	create_custom_fields(custom_fields, update=True)
	print("  ✓ Custom fields for Task doctype created")


def create_project_custom_fields():
	"""
	Create child table field in Project doctype for Part Numbers.
	"""
	custom_fields = {
		"Project": [
			{
				"fieldname": "part_numbers_section",
				"label": "Part Numbers",
				"fieldtype": "Section Break",
				"insert_after": "project_template",
				"collapsible": 0
			},
			{
				"fieldname": "part_numbers",
				"label": "Part Numbers",
				"fieldtype": "Table",
				"insert_after": "part_numbers_section",
				"options": "Project Part Number",
				"description": "Add part numbers to track multiple parts in this project"
			}
		]
	}

	# Create custom fields (function is idempotent - checks for existing fields)
	create_custom_fields(custom_fields, update=True)
	print("  ✓ Child table field for Project doctype created")


def create_item_custom_fields():
	"""
	Create custom field in Item doctype to link items to projects.
	"""
	custom_fields = {
		"Item": [
			{
				"fieldname": "project",
				"label": "Project",
				"fieldtype": "Link",
				"options": "Project",
				"insert_after": "is_fixed_asset",
				"in_list_view": 1,
				"in_standard_filter": 1,
				"in_global_search": 1,
				"translatable": 0,
				"description": "Project this item (part) belongs to"
			}
		]
	}

	# Create custom fields (function is idempotent - checks for existing fields)
	create_custom_fields(custom_fields, update=True)
	print("  ✓ Custom field for Item doctype created")

