# Copyright (c) 2025, Guru107 and contributors
# For license information, please see license.txt

"""
Server-side utility functions for Project doctype operations.
These functions are called from client scripts and server scripts.
"""

import json

import frappe
from frappe import _

from npd_project_module.utils.task_generation import delete_tasks_for_part, generate_tasks_for_part


@frappe.whitelist()
def validate_project_parts(project_name, part_numbers):
	"""
	Validate that items don't already belong to another project.
	This is called from client script before save.

	Args:
		project_name: Name of the Project document
		part_numbers: List of part numbers (Item codes)

	Returns:
		dict: {"valid": bool, "message": str}
	"""
	if not part_numbers:
		return {"valid": True}

	for part_number in part_numbers:
		if not part_number:
			continue

		item_project = frappe.db.get_value("Item", part_number, "project")

		if item_project and item_project != project_name:
			item_name = frappe.db.get_value("Item", part_number, "item_name") or part_number
			return {
				"valid": False,
				"message": _(
					"Item {0} ({1}) already belongs to Project {2}. An item can only belong to one project."
				).format(item_name, part_number, item_project),
			}

	return {"valid": True}


@frappe.whitelist()
def handle_project_save(project_name, part_numbers_data, is_new=None):
	"""
	Handle task generation and project assignment after project save.
	This is called from client script after save.

	Args:
		project_name: Name of the Project document
		part_numbers_data: List of dicts with part_number and iteration_number (may be JSON string)
		is_new: Optional flag indicating if this is a new project (for backward compatibility with tests)

	Returns:
		dict: {"success": bool, "message": str}
	"""
	try:
		# Parse JSON string if needed
		if isinstance(part_numbers_data, str):
			try:
				part_numbers_data = json.loads(part_numbers_data)
			except json.JSONDecodeError:
				frappe.log_error(
					f"Failed to parse part_numbers_data as JSON: {part_numbers_data}", "Project Save Error"
				)
				frappe.throw(_("Invalid part_numbers_data format"))

		if not part_numbers_data:
			_handle_part_removal(project_name, [])
			return {"success": True}

		# Ensure part_numbers_data is a list
		if not isinstance(part_numbers_data, list):
			frappe.log_error(
				f"part_numbers_data is not a list: {type(part_numbers_data)} - {part_numbers_data}",
				"Project Save Error",
			)
			frappe.throw(_("part_numbers_data must be a list"))

		# Build current_part_numbers set with defensive checks
		current_part_numbers = set()
		for row in part_numbers_data:
			if isinstance(row, dict):
				part_num = row.get("part_number")
				if part_num:
					current_part_numbers.add(part_num)
			elif isinstance(row, str):
				# Handle case where row might be just a string (part_number)
				current_part_numbers.add(row)
			else:
				frappe.log_error(
					f"Invalid row format in part_numbers_data: {type(row)} - {row}", "Project Save Error"
				)

		# Ensure all items have project field set
		for part_row in part_numbers_data:
			# Ensure part_row is a dict
			if not isinstance(part_row, dict):
				frappe.log_error(f"Invalid part_row format: {part_row}", "Project Save Error")
				continue

			part_number = part_row.get("part_number")
			if part_number:
				current_item_project = frappe.db.get_value("Item", part_number, "project")
				if current_item_project != project_name:
					frappe.db.set_value("Item", part_number, "project", project_name)

		# Get existing part numbers with tasks
		parts_with_tasks = _get_existing_part_numbers(project_name)

		# Find new parts (parts that don't have tasks yet)
		new_parts = []
		for part_row in part_numbers_data:
			# Ensure part_row is a dict
			if not isinstance(part_row, dict):
				frappe.log_error(f"Invalid part_row format: {part_row}", "Project Save Error")
				continue

			part_number = part_row.get("part_number")
			if part_number and part_number not in parts_with_tasks:
				iteration_number = part_row.get("iteration_number") or 0
				new_parts.append({"part_number": part_number, "iteration_number": iteration_number})

		# Generate tasks for new parts
		for part_info in new_parts:
			generate_tasks_for_part(
				project_name=project_name,
				part_number=part_info["part_number"],
				iteration_number=part_info["iteration_number"],
			)

		# Handle part removal
		_handle_part_removal(project_name, current_part_numbers)

		return {"success": True, "message": _("Project saved successfully")}
	except Exception as e:
		frappe.log_error(f"Error handling project save: {e!s}", "Project Save Error")
		return {"success": False, "message": str(e)}


@frappe.whitelist()
def handle_project_delete(project_name):
	"""
	Handle cleanup when project is deleted.
	This is called from client script before delete.

	Args:
		project_name: Name of the Project document

	Returns:
		dict: {"success": bool, "message": str}
	"""
	try:
		# Delete all tasks
		tasks = frappe.db.get_all("Task", filters={"project": project_name}, fields=["name"])

		deleted_task_count = 0
		for task in tasks:
			try:
				frappe.delete_doc("Task", task.name, force=True, ignore_permissions=True)
				deleted_task_count += 1
			except Exception as e:
				frappe.log_error(f"Error deleting task {task.name}: {e!s}", "Project Deletion Error")

		# Clear project reference from Items
		items_with_project = frappe.db.get_all("Item", filters={"project": project_name}, fields=["name"])

		updated_count = 0
		for item in items_with_project:
			try:
				frappe.db.set_value("Item", item.name, "project", None)
				updated_count += 1
			except Exception as e:
				frappe.log_error(
					f"Error clearing project reference from Item {item.name}: {e!s}",
					"Project Deletion Error",
				)

		return {
			"success": True,
			"message": _("Deleted {0} task(s) and cleared project reference from {1} item(s)").format(
				deleted_task_count, updated_count
			),
		}
	except Exception as e:
		frappe.log_error(f"Error handling project delete: {e!s}", "Project Deletion Error")
		return {"success": False, "message": str(e)}


def _handle_part_removal(project_name, current_part_numbers):
	"""Helper function to handle part removal."""
	# Get all parts that currently have this project set in their project field
	# but are not in the current Part Numbers table
	items_with_project = frappe.db.get_all("Item", filters={"project": project_name}, fields=["name"])

	all_part_numbers_in_db = {item.name for item in items_with_project}

	# Find parts that were removed (exist in DB but not in current table)
	removed_parts = all_part_numbers_in_db - set(current_part_numbers)
	for part_number in removed_parts:
		# Delete tasks for this part
		delete_tasks_for_part(project_name=project_name, part_number=part_number)

		# Clear project reference from Item
		frappe.db.set_value("Item", part_number, "project", None)


def _get_existing_part_numbers(project_name):
	"""Get list of part numbers that have tasks."""
	if not project_name or project_name == "New Project":
		return set()

	part_numbers = frappe.db.get_all(
		"Task", filters={"project": project_name}, fields=["part_number"], distinct=True
	)

	return {row.part_number for row in part_numbers if row.part_number}
