# Copyright (c) 2025, Guru107 and contributors
# For license information, please see license.txt

"""
Utility functions for iteration management in NPD Project Module.
"""

import frappe
from frappe import _

from npd_project_module.utils.task_generation import generate_tasks_for_part, get_task_sequence_from_template


@frappe.whitelist()
def get_cancelled_task_for_part(project_name, part_number):
	"""
	Find the cancelled/failed task in the latest iteration for a given part.

	Args:
		project_name (str): Name of the Project document
		part_number (str): Item code/name (part number)

	Returns:
		dict: Dictionary with cancelled task info or None if no cancelled task found
		{
			"task_name": str,
			"task_subject": str,
			"iteration_number": int,
			"task_index": int  # Index in task sequence
		}
	"""
	if not project_name or not part_number:
		return None

	# Get the latest iteration number for this part
	latest_iteration = get_latest_iteration_number(project_name, part_number)
	if latest_iteration is None:
		return None

	# Get all tasks for this part and iteration, ordered by creation
	tasks = frappe.get_all(
		"Task",
		filters={"project": project_name, "part_number": part_number, "iteration_number": latest_iteration},
		fields=["name", "subject", "status"],
		order_by="creation",
	)

	if not tasks:
		return None

	# Find the first cancelled task in the sequence
	item_name = frappe.db.get_value("Item", part_number, "item_name") or part_number

	# Get task sequence from Project Template
	task_sequence = get_task_sequence_from_template(project_name=project_name)
	if not task_sequence:
		return None

	for task in tasks:
		if task.status == "Cancelled":
			# Find which task in the sequence this is
			for index, task_name in enumerate(task_sequence):
				expected_subject = f"{item_name} {task_name}"
				if task.subject == expected_subject:
					return {
						"task_name": task.name,
						"task_subject": task.subject,
						"iteration_number": latest_iteration,
						"task_index": index,
					}

	return None


@frappe.whitelist()
def validate_iteration_limit(project_name, part_number):
	"""
	Check if a part has reached the maximum iteration limit of 10.

	Args:
		project_name (str): Name of the Project document
		part_number (str): Item code/name (part number)

	Returns:
		dict: {
			"can_create": bool,
			"current_iteration": int,
			"message": str (if limit reached)
		}
	"""
	if not project_name or not part_number:
		frappe.throw(_("Project name and part number are required"))

	latest_iteration = get_latest_iteration_number(project_name, part_number)

	if latest_iteration is None:
		# No iterations exist yet, can create iteration 0
		return {"can_create": True, "current_iteration": -1, "message": None}

	if latest_iteration >= 9:  # 0-9 = 10 iterations, so 9 is the last allowed
		return {
			"can_create": False,
			"current_iteration": latest_iteration,
			"message": _(
				"Part {0} has reached the maximum iteration limit of 10. Cannot create more iterations."
			).format(part_number),
		}

	return {"can_create": True, "current_iteration": latest_iteration, "message": None}


@frappe.whitelist()
def get_incomplete_tasks_count(project_name, part_number, iteration_number):
	"""
	Count incomplete tasks in a specific iteration for a part.

	Args:
		project_name (str): Name of the Project document
		part_number (str): Item code/name (part number)
		iteration_number (int): Iteration number

	Returns:
		int: Number of incomplete tasks
	"""
	if not project_name or not part_number or iteration_number is None:
		return 0

	incomplete_count = frappe.db.count(
		"Task",
		{
			"project": project_name,
			"part_number": part_number,
			"iteration_number": iteration_number,
			"status": ["not in", ["Completed", "Cancelled"]],
		},
	)

	return incomplete_count


@frappe.whitelist()
def get_latest_iteration_number(project_name, part_number):
	"""
	Get the latest iteration number for a part.

	Args:
		project_name (str): Name of the Project document
		part_number (str): Item code/name (part number)

	Returns:
		int: Latest iteration number, or None if no iterations exist
	"""
	if not project_name or not part_number:
		return None

	result = frappe.db.sql(
		"""
		SELECT MAX(iteration_number) as max_iteration
		FROM `tabTask`
		WHERE project = %s AND part_number = %s
	""",
		(project_name, part_number),
		as_dict=True,
	)

	if result and result[0].get("max_iteration") is not None:
		return result[0]["max_iteration"]

	return None


@frappe.whitelist()
def get_iteration_info(project_name, part_number):
	"""
	Get information about iterations for a part.

	Args:
		project_name (str): Name of the Project document
		part_number (str): Item code/name (part number)

	Returns:
		dict: {
			"latest_iteration": int,
			"cancelled_task": dict or None,
			"new_iteration_start_task": dict,  # Task that new iteration will start from (always 2nd stage)
			"incomplete_tasks_count": int,
			"can_create_new": bool
		}
	"""
	if not project_name or not part_number:
		frappe.throw(_("Project name and part number are required"))

	latest_iteration = get_latest_iteration_number(project_name, part_number)

	if latest_iteration is None:
		return {
			"latest_iteration": None,
			"cancelled_task": None,
			"new_iteration_start_task": None,
			"incomplete_tasks_count": 0,
			"can_create_new": True,
		}

	cancelled_task = get_cancelled_task_for_part(project_name, part_number)
	incomplete_count = get_incomplete_tasks_count(project_name, part_number, latest_iteration)
	limit_check = validate_iteration_limit(project_name, part_number)

	# New iteration always starts from the 2nd stage: "Internal Team Technical Feasibility"
	# RFQ Data (1st stage) is never cancelled and will always be completed
	item_name = frappe.db.get_value("Item", part_number, "item_name") or part_number

	# Get task sequence from Project Template
	task_sequence = get_task_sequence_from_template(project_name=project_name)
	if not task_sequence or len(task_sequence) < 2:
		frappe.throw(_("Project Template must have at least 2 tasks"))
	start_task_name = task_sequence[1]  # Index 1 = "Internal Team Technical Feasibility"
	start_task_subject = f"{item_name} {start_task_name}"

	new_iteration_start_task = {
		"task_name": start_task_name,
		"task_subject": start_task_subject,
		"task_index": 1,
	}

	return {
		"latest_iteration": latest_iteration,
		"cancelled_task": cancelled_task,
		"new_iteration_start_task": new_iteration_start_task,
		"incomplete_tasks_count": incomplete_count,
		"can_create_new": limit_check["can_create"],
	}


@frappe.whitelist()
def create_new_iteration(project_name, part_number):
	"""
	Create a new iteration for a part, always starting from the 2nd stage
	("Internal Team Technical Feasibility"). RFQ Data (1st stage) is never cancelled
	and will always be completed.

	Args:
		project_name (str): Name of the Project document
		part_number (str): Item code/name (part number)

	Returns:
		dict: {
			"success": bool,
			"new_iteration_number": int,
			"tasks_created": list,
			"tasks_obsoleted": int,
			"message": str
		}
	"""
	if not project_name or not part_number:
		frappe.throw(_("Project name and part number are required"))

	# Validate iteration limit
	limit_check = validate_iteration_limit(project_name, part_number)
	if not limit_check["can_create"]:
		frappe.throw(_(limit_check["message"]))

	# Get latest iteration info
	latest_iteration = get_latest_iteration_number(project_name, part_number)
	if latest_iteration is None:
		frappe.throw(
			_(
				"No previous iteration found. Initial iteration (0) should be created automatically when parts are added to the project."
			)
		)

	# Check if there's at least one cancelled task in latest iteration
	# (RFQ Data will never be cancelled, so we check for any cancelled task)
	cancelled_task = get_cancelled_task_for_part(project_name, part_number)
	if not cancelled_task:
		frappe.throw(
			_(
				"No cancelled task found in the latest iteration. Cannot create new iteration without a cancelled task."
			)
		)

	# Calculate new iteration number
	new_iteration_number = latest_iteration + 1

	# Mark incomplete tasks from previous iteration as obsolete
	tasks_obsoleted = mark_tasks_as_obsolete(project_name, part_number, latest_iteration)

	# Always start from the 2nd stage (index 1): "Internal Team Technical Feasibility"
	# RFQ Data (index 0) is never cancelled and will always be completed
	start_index = 1

	# Get task sequence from Project Template
	task_sequence = get_task_sequence_from_template(project_name=project_name)
	if not task_sequence or len(task_sequence) < 2:
		frappe.throw(_("Project Template must have at least 2 tasks"))
	start_task_name = task_sequence[start_index]

	# Generate tasks starting from the 2nd stage
	tasks_created = generate_tasks_from_cancelled_task(
		project_name=project_name,
		part_number=part_number,
		iteration_number=new_iteration_number,
		start_index=start_index,
	)

	# Update Part Numbers table iteration number
	update_part_iteration_number(project_name, part_number, new_iteration_number)

	item_name = frappe.db.get_value("Item", part_number, "item_name") or part_number
	start_task_subject = f"{item_name} {start_task_name}"
	message = _("Created new iteration {0} for Part {1}. Generated {2} tasks starting from {3}.").format(
		new_iteration_number, item_name, len(tasks_created), start_task_subject
	)

	if tasks_obsoleted > 0:
		message += _(" Marked {0} incomplete task(s) from previous iteration as obsolete.").format(
			tasks_obsoleted
		)

	frappe.msgprint(message, indicator="green")

	return {
		"success": True,
		"new_iteration_number": new_iteration_number,
		"tasks_created": tasks_created,
		"tasks_obsoleted": tasks_obsoleted,
		"message": message,
	}


def generate_tasks_from_cancelled_task(project_name, part_number, iteration_number, start_index):
	"""
	Generate tasks starting from a specific task index in the sequence.

	Args:
		project_name (str): Name of the Project document
		part_number (str): Item code/name (part number)
		iteration_number (int): New iteration number
		start_index (int): Index in task sequence to start from

	Returns:
		list: List of created Task document names
	"""
	if not project_name or not part_number:
		frappe.throw(_("Project name and part number are required"))

	# Get task sequence from Project Template
	task_sequence = get_task_sequence_from_template(project_name=project_name)
	if not task_sequence:
		frappe.throw(_("Project Template not found or has no tasks"))

	if start_index < 0 or start_index >= len(task_sequence):
		frappe.throw(_("Invalid start index for task generation"))

	# Check if tasks already exist for this part and iteration
	if tasks_exist_for_part(project_name, part_number, iteration_number):
		frappe.msgprint(
			_("Tasks already exist for Part {0} in Iteration {1}. Skipping task generation.").format(
				part_number, iteration_number
			),
			indicator="orange",
		)
		return []

	# Get Item name for task naming
	item_name = frappe.db.get_value("Item", part_number, "item_name") or part_number

	# Set flag to indicate we're in task generation (to skip hooks)
	frappe.flags.in_task_generation = True

	try:
		# Create tasks starting from start_index
		created_tasks = []
		previous_task_name = None

		for index in range(start_index, len(task_sequence)):
			task_name = task_sequence[index]
			full_task_name = f"{item_name} {task_name}"

			# Create task document
			task_doc = frappe.get_doc(
				{
					"doctype": "Task",
					"subject": full_task_name,
					"project": project_name,
					"part_number": part_number,
					"iteration_number": iteration_number,
					"status": "Open",
					"is_group": 0,
				}
			)

			# Add dependency on previous task in this iteration if it exists
			if previous_task_name:
				task_doc.append("depends_on", {"task": previous_task_name})

			# Save task
			task_doc.insert(ignore_permissions=True)
			created_tasks.append(task_doc.name)
			previous_task_name = task_doc.name

		return created_tasks
	finally:
		# Clear flag after task generation
		frappe.flags.in_task_generation = False


@frappe.whitelist()
def mark_tasks_as_obsolete(project_name, part_number, iteration_number):
	"""
	Mark all incomplete tasks from a specific iteration as obsolete.

	Args:
		project_name (str): Name of the Project document
		part_number (str): Item code/name (part number)
		iteration_number (int): Iteration number to mark tasks as obsolete

	Returns:
		int: Number of tasks marked as obsolete
	"""
	if not project_name or not part_number or iteration_number is None:
		return 0

	# Get all incomplete tasks for this part and iteration
	incomplete_tasks = frappe.get_all(
		"Task",
		filters={
			"project": project_name,
			"part_number": part_number,
			"iteration_number": iteration_number,
			"status": ["not in", ["Completed", "Cancelled"]],
		},
		fields=["name"],
	)

	obsoleted_count = 0
	for task in incomplete_tasks:
		try:
			task_doc = frappe.get_doc("Task", task.name)
			# Use "Cancelled" status to mark as obsolete (Frappe doesn't have "Obsolete" status)
			# We'll use a custom field or status in the future if needed
			# For now, we'll use "Cancelled" status
			if task_doc.status != "Cancelled":
				task_doc.status = "Cancelled"
				task_doc.save(ignore_permissions=True)
				obsoleted_count += 1
		except Exception as e:
			frappe.log_error(f"Error marking task {task.name} as obsolete: {e!s}")

	return obsoleted_count


def update_part_iteration_number(project_name, part_number, new_iteration_number):
	"""
	Update the iteration number in the Project's Part Numbers table.

	Args:
		project_name (str): Name of the Project document
		part_number (str): Item code/name (part number)
		new_iteration_number (int): New iteration number to set
	"""
	if not project_name or not part_number:
		return

	# Get the Project document
	project_doc = frappe.get_doc("Project", project_name)

	# Find the part in the Part Numbers table
	for part_row in project_doc.part_numbers:
		if part_row.part_number == part_number:
			part_row.iteration_number = new_iteration_number
			project_doc.save(ignore_permissions=True)
			return

	# If part not found in table, log warning
	frappe.log_error(
		f"Part {part_number} not found in Project {project_name} Part Numbers table",
		"Iteration Update Warning",
	)


def tasks_exist_for_part(project_name, part_number, iteration_number):
	"""
	Check if tasks already exist for a given part and iteration.
	(Re-exported from task_generation for convenience)
	"""
	from npd_project_module.utils.task_generation import tasks_exist_for_part as check_tasks_exist

	return check_tasks_exist(project_name, part_number, iteration_number)
