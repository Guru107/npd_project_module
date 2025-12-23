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
	create_npd_template()
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
				"description": "Item (part) associated with this task",
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
				"description": "Iteration number for this task (system-managed)",
			},
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
				"collapsible": 0,
			},
			{
				"fieldname": "part_numbers",
				"label": "Part Numbers",
				"fieldtype": "Table",
				"insert_after": "part_numbers_section",
				"options": "Project Part Number",
				"description": "Add part numbers to track multiple parts in this project",
			},
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
				"description": "Project this item (part) belongs to",
			}
		]
	}

	# Create custom fields (function is idempotent - checks for existing fields)
	create_custom_fields(custom_fields, update=True)
	print("  ✓ Custom field for Item doctype created")


def create_npd_template():
	"""
	Create default NPD Project Template with 18 tasks.
	This template will be used to fetch the task sequence for new projects.
	"""
	template_name = "NPD Template"

	# List of 18 tasks in sequential order for New Part Development Process
	task_names = [
		"RFQ Data",
		"Internal Team Technical Feasibility",
		"Supplier Quote & Tooling Sequence",
		"Technical Sign Off",
		"Commercial with M&M",
		"VOB or LOBA",
		"TKO Data",
		"Comparison of TKO & RFQ Data",
		"Commercial with Supplier",
		"Time Plan",
		"Design Approval Process",
		"Buy Off",
		"HLTO",
		"IPTR",
		"PPAP",
		"JPTR",
		"APQP",
		"Handover to Production",
	]

	# Check if template already exists and has correct number of tasks
	if frappe.db.exists("Project Template", template_name):
		template = frappe.get_doc("Project Template", template_name)
		if template.tasks and len(template.tasks) == len(task_names):
			print(f"  ✓ NPD Template already exists with {len(task_names)} tasks")
			return
		# Template exists but needs updating, clear existing tasks
		template.tasks = []

	# Create template Task documents (these are just templates, not real tasks)
	# We need to create them in sequence and add dependencies
	template_tasks = []
	previous_task_name = None

	for task_name in task_names:
		# Check if template task already exists by subject (without project)
		existing_tasks = frappe.get_all(
			"Task", filters={"subject": task_name, "project": ["is", "not set"]}, fields=["name"], limit=1
		)

		if existing_tasks:
			existing_task_name = existing_tasks[0].name
			template_tasks.append(existing_task_name)

			# Update dependencies if needed
			if previous_task_name:
				existing_task_doc = frappe.get_doc("Task", existing_task_name)
				# Check if dependency already exists
				has_dependency = any(dep.task == previous_task_name for dep in existing_task_doc.depends_on)
				if not has_dependency:
					existing_task_doc.append("depends_on", {"task": previous_task_name})
					existing_task_doc.save(ignore_permissions=True)
					frappe.db.commit()

			previous_task_name = existing_task_name
		else:
			# Create new template task
			template_task = frappe.get_doc(
				{
					"doctype": "Task",
					"subject": task_name,
					"status": "Open",
					"is_group": 0,
				}
			)

			# Add dependency on previous task if it exists
			if previous_task_name:
				template_task.append("depends_on", {"task": previous_task_name})

			template_task.insert(ignore_permissions=True)
			frappe.db.commit()
			template_tasks.append(template_task.name)
			previous_task_name = template_task.name

	# Create or update Project Template
	if frappe.db.exists("Project Template", template_name):
		template = frappe.get_doc("Project Template", template_name)
	else:
		# Create new Project Template with name "NPD Template"
		template = frappe.get_doc(
			{
				"doctype": "Project Template",
				"name": template_name,  # "NPD Template"
				"project_type": None,  # Can be set later if needed
				"disabled": 0,
			}
		)
		# Explicitly set the name for doctypes with autoname "Prompt"
		template.name = template_name

	# Add tasks to template in sequence
	for task_name in template_tasks:
		template.append("tasks", {"task": task_name})

	if frappe.db.exists("Project Template", template_name):
		template.save(ignore_permissions=True)
	else:
		template.insert(ignore_permissions=True)
	frappe.db.commit()

	print(f"  ✓ Created/Updated NPD Template with {len(task_names)} tasks")
