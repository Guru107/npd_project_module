# Copyright (c) 2025, Guru107 and contributors
# For license information, please see license.txt

"""
Server-side utility functions for Task doctype operations.
These functions are called from client scripts and server scripts.
"""

import frappe
from frappe import _

from npd_project_module.utils.task_generation import get_task_sequence_from_template


@frappe.whitelist()
def validate_task_cancellation(task_name, part_number, subject):
	"""
	Validate that RFQ Data (first task) cannot be cancelled.
	RFQ Data will always be completed and cannot be cancelled.

	Args:
		task_name: Name of the Task document
		part_number: Part number (Item code)
		subject: Task subject (kept for backward compatibility, but not used)

	Returns:
		dict: {"valid": bool, "message": str}
	"""
	if not part_number:
		return {"valid": True}

	try:
		# Get task document to access stage_type field
		task_doc = frappe.get_doc("Task", task_name)

		# Get project name from task
		project_name = task_doc.project
		task_sequence = get_task_sequence_from_template(project_name=project_name)

		# Check if this is RFQ Data (first task, index 0) using stage_type
		if not task_sequence:
			return {"valid": True}

		rfq_stage_type = task_sequence[0]["subject"]  # RFQ Data stage_type is always first

		# Use stage_type for exact matching instead of subject
		if task_doc.stage_type and task_doc.stage_type == rfq_stage_type:
			return {
				"valid": False,
				"message": _(
					"RFQ Data (1st stage) cannot be cancelled. It will always be completed after attaching the Request For Quotation file. "
					"Only tasks from stage 2 onwards can be cancelled."
				),
			}

		return {"valid": True}
	except Exception as e:
		frappe.log_error(f"Error validating task cancellation: {e!s}", "Task Cancellation Validation Error")
		return {"valid": True}  # Allow cancellation if validation fails


@frappe.whitelist()
def validate_task_dependencies(task_name, part_number, iteration_number, status):
	"""
	Validate task dependencies before allowing status change.
	This is called from client script before save.

	Args:
		task_name: Name of the Task document
		part_number: Part number (Item code)
		iteration_number: Iteration number
		status: New status

	Returns:
		dict: {"valid": bool, "message": str}
	"""
	if not part_number or iteration_number is None:
		return {"valid": True}

	if status not in ("Working", "Completed"):
		return {"valid": True}

	try:
		task_doc = frappe.get_doc("Task", task_name)

		if not task_doc.depends_on:
			return {"valid": True}

		# Check each dependency within the same iteration
		for dependency in task_doc.depends_on:
			dep_task_name = dependency.task

			try:
				dep_task_doc = frappe.get_doc("Task", dep_task_name)

				# Only validate dependencies within the same iteration
				if (
					dep_task_doc.part_number == part_number
					and dep_task_doc.iteration_number == iteration_number
				):
					if dep_task_doc.status not in ("Completed", "Cancelled"):
						item_name = frappe.db.get_value("Item", part_number, "item_name") or part_number
						return {
							"valid": False,
							"message": _(
								"Cannot {0} task {1} (Part: {2}, Iteration: {3}) as its dependent task {4} "
								"is not completed/cancelled. Dependencies are enforced within the same iteration only."
							).format(
								status.lower(),
								task_doc.subject,
								item_name,
								str(iteration_number),
								dep_task_doc.subject,
							),
						}
			except frappe.DoesNotExistError:
				continue

		return {"valid": True}
	except Exception as e:
		frappe.log_error(f"Error validating task dependencies: {e!s}", "Task Validation Error")
		return {"valid": True}  # Allow save if validation fails


@frappe.whitelist()
def handle_task_cancellation(task_name, part_number, iteration_number, project_name):
	"""
	Handle automatic cancellation of subsequent tasks when a task is cancelled.
	This is called from client script after save.

	Args:
		task_name: Name of the Task document
		part_number: Part number (Item code)
		iteration_number: Iteration number
		project_name: Project name

	Returns:
		dict: {"success": bool, "cancelled_count": int, "message": str}
	"""
	if not part_number or iteration_number is None:
		return {"success": True, "cancelled_count": 0}

	# Set flag to prevent recursive cancellation
	frappe.flags.in_cancellation_cascade = True

	try:
		task_doc = frappe.get_doc("Task", task_name)
		current_task_stage_type = task_doc.stage_type
		item_name = frappe.db.get_value("Item", part_number, "item_name") or part_number

		# Get task sequence from Project Template
		task_sequence = get_task_sequence_from_template(project_name=project_name)
		if not task_sequence:
			return {"success": True, "cancelled_count": 0}

		# Create a mapping of stage_type to index for efficient lookup
		stage_to_index = {task_info["subject"]: index for index, task_info in enumerate(task_sequence)}

		# Find current task's position in sequence using stage_type
		current_task_index = stage_to_index.get(current_task_stage_type) if current_task_stage_type else None

		if current_task_index is None:
			return {"success": True, "cancelled_count": 0}

		# Get all tasks for this part and iteration
		all_tasks = frappe.get_all(
			"Task",
			filters={
				"project": project_name,
				"part_number": part_number,
				"iteration_number": iteration_number,
				"status": ["!=", "Cancelled"],
			},
			fields=["name", "stage_type"],
			order_by="creation",
		)

		# Cancel subsequent tasks
		cancelled_count = 0
		for task in all_tasks:
			if task.name == task_name:
				continue

			# Find task's position in sequence using stage_type
			task_index = stage_to_index.get(task.stage_type) if task.stage_type else None

			# Cancel if it comes after the cancelled task
			if task_index is not None and task_index > current_task_index:
				frappe.db.set_value("Task", task.name, "status", "Cancelled")
				cancelled_count += 1

		if cancelled_count > 0:
			return {
				"success": True,
				"cancelled_count": cancelled_count,
				"message": _(
					"Cancelled {0} subsequent task(s) in the sequence for Part {1} (Iteration {2})"
				).format(cancelled_count, item_name, iteration_number),
			}

		return {"success": True, "cancelled_count": 0}
	finally:
		# Clear flag
		try:
			if hasattr(frappe.flags, "in_cancellation_cascade"):
				delattr(frappe.flags, "in_cancellation_cascade")
		except (KeyError, AttributeError):
			pass


@frappe.whitelist()
def check_task_blocked_status(task_names):
	"""
	Check if tasks are blocked (have unmet dependencies).
	Used for list view to show visual indicators.

	Args:
		task_names: List of task names to check

	Returns:
		dict: {task_name: bool} - True if task is blocked
	"""
	if isinstance(task_names, str):
		task_names = frappe.parse_json(task_names)

	if not task_names or not isinstance(task_names, list):
		return {}

	result = {}
	for task_name in task_names:
		try:
			task_doc = frappe.get_doc("Task", task_name)
			is_blocked = False

			# Check if task has dependencies
			if task_doc.depends_on and len(task_doc.depends_on) > 0:
				# Check each dependency
				for dependency in task_doc.depends_on:
					dep_task_name = dependency.task
					try:
						dep_task_doc = frappe.get_doc("Task", dep_task_name)

						# Only check dependencies within same iteration
						if (
							task_doc.part_number
							and dep_task_doc.part_number
							and task_doc.part_number == dep_task_doc.part_number
							and task_doc.iteration_number is not None
							and dep_task_doc.iteration_number is not None
							and task_doc.iteration_number == dep_task_doc.iteration_number
						):
							# Task is blocked if dependency is not completed or cancelled
							if dep_task_doc.status not in ("Completed", "Cancelled"):
								is_blocked = True
								break
					except frappe.DoesNotExistError:
						# Dependency task doesn't exist, consider blocked
						is_blocked = True
						break

			result[task_name] = is_blocked
		except frappe.DoesNotExistError:
			result[task_name] = False

	return result
