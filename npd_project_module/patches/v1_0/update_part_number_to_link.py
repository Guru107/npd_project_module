# Copyright (c) 2025, Guru107 and contributors
# For license information, please see license.txt

"""
Migration script to update part_number field from Data to Link (Item).
Since Frappe doesn't allow changing field type directly, we need to:
1. Delete the old Data field
2. Create the new Link field
"""

import frappe


def execute():
	"""
	Update part_number field from Data to Link (Item) in both Task and Project Part Number doctypes.
	"""
	# Update Task custom field
	update_task_part_number_field()
	
	# Update Project Part Number doctype field
	update_project_part_number_field()
	
	frappe.db.commit()
	frappe.msgprint("Updated part_number fields from Data to Link (Item)")


def update_task_part_number_field():
	"""
	Update Task.part_number from Data to Link (Item).
	"""
	custom_field_name = frappe.db.get_value(
		"Custom Field",
		{"dt": "Task", "fieldname": "part_number"},
		"name"
	)
	
	if custom_field_name:
		# Delete old field
		frappe.delete_doc("Custom Field", custom_field_name, force=True)
		frappe.msgprint(f"Deleted old Task.part_number field")
	
	# Create new Link field
	from frappe.custom.doctype.custom_field.custom_field import create_custom_fields
	
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
			}
		]
	}
	
	create_custom_fields(custom_fields, update=True)
	frappe.msgprint("Created new Task.part_number Link field")


def update_project_part_number_field():
	"""
	Update Project Part Number.part_number from Data to Link (Item).
	This is handled by the doctype JSON migration, but we verify it here.
	"""
	# The doctype field is updated via JSON migration
	# Just verify the field exists and is correct
	doctype = frappe.get_doc("DocType", "Project Part Number")
	part_number_field = None
	
	for field in doctype.fields:
		if field.fieldname == "part_number":
			part_number_field = field
			break
	
	if part_number_field:
		if part_number_field.fieldtype != "Link" or part_number_field.options != "Item":
			frappe.msgprint(
				f"Warning: Project Part Number.part_number field type is {part_number_field.fieldtype}, "
				f"expected Link with options Item. Please check the doctype JSON file."
			)
		else:
			frappe.msgprint("Project Part Number.part_number field is correctly configured as Link (Item)")

