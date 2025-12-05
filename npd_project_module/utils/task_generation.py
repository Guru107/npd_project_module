# Copyright (c) 2025, Guru107 and contributors
# For license information, please see license.txt

"""
Utility functions for automatic task generation with dependencies.
"""

import frappe
from frappe import _


# List of 18 tasks in sequential order for New Part Development Process
NPD_TASK_SEQUENCE = [
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
	"Handover to Production"
]


def generate_tasks_for_part(project_name, part_number, iteration_number=0):
	"""
	Generate 18 tasks for a given part (Item) and iteration.
	
	Args:
		project_name (str): Name of the Project document
		part_number (str): Item code/name (part number)
		iteration_number (int): Iteration number (default: 0)
	
	Returns:
		list: List of created Task document names
	"""
	if not project_name:
		frappe.throw(_("Project name is required"))
	
	if not part_number:
		frappe.throw(_("Part number (Item) is required"))
	
	# Check if tasks already exist for this part and iteration
	if tasks_exist_for_part(project_name, part_number, iteration_number):
		frappe.msgprint(
			_("Tasks already exist for Part {0} in Iteration {1}. Skipping task generation.").format(
				part_number, iteration_number
			),
			indicator="orange"
		)
		return []
	
	# Get Item name for task naming
	item_name = frappe.db.get_value("Item", part_number, "item_name") or part_number
	
	# Set flag to indicate we're in task generation (to skip hooks)
	frappe.flags.in_task_generation = True
	
	try:
		# Create tasks in sequence
		created_tasks = []
		previous_task_name = None
		
		for index, task_name in enumerate(NPD_TASK_SEQUENCE):
			# Format task name: "[Item Name] [Task Name]"
			full_task_name = f"{item_name} {task_name}"
			
			# Create task document
			task_doc = frappe.get_doc({
				"doctype": "Task",
				"subject": full_task_name,
				"project": project_name,
				"part_number": part_number,
				"iteration_number": iteration_number,
				"status": "Open",
				"is_group": 0
			})
			
			# Add dependency on previous task if it exists
			if previous_task_name:
				task_doc.append("depends_on", {
					"task": previous_task_name
				})
			
			# Save task
			task_doc.insert(ignore_permissions=True)
			created_tasks.append(task_doc.name)
			previous_task_name = task_doc.name
		
		frappe.msgprint(
			_("Created {0} tasks for Part {1} (Iteration {2})").format(
				len(created_tasks), item_name, iteration_number
			),
			indicator="green"
		)
		
		return created_tasks
	finally:
		# Clear flag after task generation
		frappe.flags.in_task_generation = False


def tasks_exist_for_part(project_name, part_number, iteration_number):
	"""
	Check if tasks already exist for a given part and iteration.
	
	Args:
		project_name (str): Name of the Project document
		part_number (str): Item code/name (part number)
		iteration_number (int): Iteration number
	
	Returns:
		bool: True if tasks exist, False otherwise
	"""
	task_count = frappe.db.count("Task", {
		"project": project_name,
		"part_number": part_number,
		"iteration_number": iteration_number
	})
	
	return task_count > 0


def delete_tasks_for_part(project_name, part_number):
	"""
	Delete all tasks associated with a part (Item) across all iterations.
	
	Args:
		project_name (str): Name of the Project document
		part_number (str): Item code/name (part number)
	
	Returns:
		int: Number of tasks deleted
	"""
	tasks = frappe.get_all("Task", {
		"project": project_name,
		"part_number": part_number
	}, pluck="name")
	
	deleted_count = 0
	for task_name in tasks:
		try:
			frappe.delete_doc("Task", task_name, force=True, ignore_permissions=True)
			deleted_count += 1
		except Exception as e:
			frappe.log_error(f"Error deleting task {task_name}: {str(e)}")
	
	return deleted_count

