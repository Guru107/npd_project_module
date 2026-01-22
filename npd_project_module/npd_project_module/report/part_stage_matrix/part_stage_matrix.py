# Copyright (c) 2025, Guru107 and contributors
# For license information, please see license.txt

"""
Part Stage Matrix Report

Shows a matrix view of task stages (rows) vs parts (columns) for a project.
Displays the status of each stage for each part, aggregating across iterations.
"""

import frappe
from frappe import _

from npd_project_module.utils.task_generation import get_task_sequence_from_template


def execute(filters=None):
	"""
	Execute the Part Stage Matrix report.

	Args:
		filters (dict): Report filters containing:
			- project (str): Project name (required)
			- part_number (list): List of part numbers (Items) to filter (optional)
			- show_all_iterations (int): If 1, shows all iterations for selected parts (optional, default: 0)

	Returns:
		tuple: (columns, data, message, chart, report_summary)
	"""
	return PartStageMatrix(filters).run()


class PartStageMatrix:
	def __init__(self, filters=None):
		self.filters = frappe._dict(filters or {})
		self.project = self.filters.get("project")
		self.part_numbers = self.filters.get("part_number") or []
		self.show_all_iterations = self.filters.get("show_all_iterations", 0)
		self.task_sequence = None  # Will be set in get_data()
		self.part_iterations = {}  # Will store {part_code: [iteration_numbers]} when show_all_iterations is True

	def run(self):
		"""Run the report and return formatted data."""
		if not self.project:
			frappe.throw(_("Project is required"))

		self.get_columns()
		self.get_data()

		return self.columns, self.data, None, None, None

	def get_columns(self):
		"""Build column definitions for the matrix report."""
		self.columns = []

		# First column: Stage name
		self.columns.append(
			{
				"label": _("Stage"),
				"fieldname": "stage",
				"fieldtype": "Data",
				"width": 250,
			}
		)

		# Get all parts for the project
		parts = self.get_parts()

		if self.show_all_iterations and self.part_numbers:
			# "Show All Iterations" view: Create columns for each iteration of each selected part
			# Get all iterations for selected parts
			self.part_iterations = self.get_all_iterations_for_parts([p.get("name") for p in parts])

			for part in parts:
				part_code = part.get("name")
				part_name = part.get("item_name") or part_code
				iterations = self.part_iterations.get(part_code, [0])  # Default to [0] if no iterations found

				# Sort iterations in descending order (latest first) for "Show All Iterations" view
				sorted_iterations = sorted(iterations, reverse=True)

				# Create a column for each iteration (latest iteration first)
				for iteration in sorted_iterations:
					self.columns.append(
						{
							"label": f"{part_name} ({part_code}) (Iter {iteration})",
							"fieldname": f"part_{part_code}_iter_{iteration}",
							"fieldtype": "Data",
							"width": 150,
						}
					)
		else:
			# Default view: One column per part (shows latest iteration)
			for part in parts:
				part_code = part.get("name")
				part_name = part.get("item_name") or part_code

				self.columns.append(
					{
						"label": f"{part_name} ({part_code})",
						"fieldname": f"part_{part_code}",
						"fieldtype": "Data",
						"width": 150,
					}
				)

	def get_parts(self):
		"""Get all parts (Items) for the project, optionally filtered."""
		# Get parts from Project's Part Numbers child table
		project_doc = frappe.get_doc("Project", self.project)
		parts_from_project = []

		if hasattr(project_doc, "part_numbers") and project_doc.part_numbers:
			for row in project_doc.part_numbers:
				if row.part_number:
					parts_from_project.append(row.part_number)

		if not parts_from_project:
			return []

		# If part_number filter is specified, filter the list
		if self.part_numbers:
			parts_from_project = [p for p in parts_from_project if p in self.part_numbers]

		# Get Item details
		parts = frappe.get_all(
			"Item",
			filters={"name": ["in", parts_from_project]},
			fields=["name", "item_name"],
			order_by="name",
		)

		return parts

	def get_all_iterations_for_parts(self, part_codes):
		"""
		Get all iteration numbers for the specified parts.

		Args:
			part_codes (list): List of part/Item codes

		Returns:
			dict: {part_code: [iteration_numbers]} - Dictionary mapping part codes to their iteration numbers
		"""
		if not part_codes:
			return {}

		# Get all tasks for these parts to find all iterations
		tasks = frappe.get_all(
			"Task",
			filters={
				"project": self.project,
				"part_number": ["in", part_codes],
			},
			fields=["part_number", "iteration_number"],
			distinct=True,
		)

		# Group iterations by part
		part_iterations = {}
		for task in tasks:
			part_code = task.get("part_number")
			iteration = task.get("iteration_number") or 0

			if part_code not in part_iterations:
				part_iterations[part_code] = []

			if iteration not in part_iterations[part_code]:
				part_iterations[part_code].append(iteration)

		# Ensure each part has at least iteration 0
		for part_code in part_codes:
			if part_code not in part_iterations:
				part_iterations[part_code] = [0]
			elif 0 not in part_iterations[part_code]:
				part_iterations[part_code].append(0)

		# Sort iterations for each part
		for part_code in part_iterations:
			part_iterations[part_code] = sorted(part_iterations[part_code])

		return part_iterations

	def get_data(self):
		"""Build matrix data: rows = stages, columns = parts."""
		self.data = []
		parts = self.get_parts()

		if not parts:
			return

		# Get task sequence from Project Template and store as instance variable
		self.task_sequence = get_task_sequence_from_template(project_name=self.project)

		# Get all tasks for this project and parts
		part_codes = [p.get("name") for p in parts]
		tasks = self.get_tasks(part_codes)

		# Build matrix: for each stage, get status for each part
		for stage_index, stage_item in enumerate(self.task_sequence):
			# Handle both string and dict formats (backward compatibility)
			if isinstance(stage_item, dict):
				stage_name = stage_item["subject"]
			else:
				stage_name = stage_item
			row = {"stage": stage_name}

			if self.show_all_iterations and self.part_numbers:
				# "Show All Iterations" view: Create cells for each iteration of each part
				for part in parts:
					part_code = part.get("name")
					iterations = self.part_iterations.get(part_code, [0])

					# Sort iterations in descending order (latest first) to match column order
					sorted_iterations = sorted(iterations, reverse=True)

					for iteration in sorted_iterations:
						status = self.get_stage_status_for_part_and_iteration(
							tasks, part_code, stage_index, stage_name, iteration
						)
						row[f"part_{part_code}_iter_{iteration}"] = status
			else:
				# Default view: Show latest iteration status for each part
				for part in parts:
					part_code = part.get("name")
					status = self.get_stage_status_for_part(tasks, part_code, stage_index, stage_name)
					row[f"part_{part_code}"] = status

			self.data.append(row)

	def get_tasks(self, part_codes):
		"""Get all tasks for the project and specified parts."""
		# Note: depends_on is a child table, so we can't fetch it directly with get_all
		# We'll fetch it when needed in is_task_blocked
		return frappe.get_all(
			"Task",
			filters={
				"project": self.project,
				"part_number": ["in", part_codes],
			},
			fields=[
				"name",
				"subject",
				"part_number",
				"iteration_number",
				"status",
				"stage_type",
			],
			order_by="part_number, iteration_number, creation",
		)

	def get_stage_status_for_part(self, tasks, part_code, stage_index, stage_name):
		"""
		Get the status of a stage for a specific part from the latest iteration only.

		Logic:
		1. Identify the latest iteration number for this part
		2. Special handling for RFQ Data (stage_index == 0):
		   - If RFQ Data is completed in iteration 0, always show as "Completed (Iter 0)"
		   - Otherwise, check latest iteration status
		3. For other stages: Get task for this stage in the latest iteration only
		4. If no task exists in latest iteration, check if it's blocked or not started
		5. Return status string with iteration number: "{status} (Iter {iteration_number})"

		Args:
			tasks (list): All tasks for the project
			part_code (str): Part/Item code
			stage_index (int): Index of stage in task sequence
			stage_name (str): Name of the stage

		Returns:
			str: Status string with iteration number (e.g., "Completed (Iter 0)", "Completed (Iter 1)", "Not Started (Iter 2)")
		"""
		# Filter tasks for this part
		part_tasks = [t for t in tasks if t.get("part_number") == part_code]

		if not part_tasks:
			return "No Tasks"

		# Get latest iteration number for this part
		latest_iteration = max([t.get("iteration_number") or 0 for t in part_tasks], default=0)

		# Special handling for RFQ Data (stage_index == 0)
		# RFQ Data is always created in iteration 0 and never cancelled
		# If completed in iteration 0, it should show as Completed even in later iterations
		if stage_index == 0:
			# Check if RFQ Data is completed in iteration 0
			rfq_iter_0_task = None
			for t in part_tasks:
				if t.get("iteration_number") == 0 and self.is_stage_task(t, stage_name):
					rfq_iter_0_task = t
					break

			if rfq_iter_0_task and rfq_iter_0_task.get("status") == "Completed":
				# RFQ Data completed in iteration 0 - show as Completed (Iter 0)
				return "Completed (Iter 0)"

			# RFQ Data not completed in iteration 0, check latest iteration
			latest_task = None
			for t in part_tasks:
				if t.get("iteration_number") == latest_iteration and self.is_stage_task(t, stage_name):
					latest_task = t
					break

			if latest_task:
				# Check if task is blocked
				if self.is_task_blocked(latest_task, part_tasks):
					return f"Blocked (Iter {latest_iteration})"

				# Return status based on task status with iteration number
				task_status = latest_task.get("status", "Open")
				status_map = {
					"Open": "Not Started",
					"Working": "In Progress",
					"Completed": "Completed",
					"Cancelled": "Cancelled",
					"Overdue": "Overdue",
				}
				mapped_status = status_map.get(task_status, task_status)
				return f"{mapped_status} (Iter {latest_iteration})"
			else:
				# RFQ Data should always exist
				return f"Not Started (Iter {latest_iteration})"

		# Get task for this stage in latest iteration only
		latest_task = None
		for t in part_tasks:
			if t.get("iteration_number") == latest_iteration and self.is_stage_task(t, stage_name):
				latest_task = t
				break

		# Determine status and format with iteration number
		if not latest_task:
			# No task exists for this stage in latest iteration
			# Check if this stage should exist (based on iteration start point)
			# Stages 1+ only exist if previous iterations had tasks
			# Check if previous stage exists in latest iteration
			if stage_index > 0 and self.task_sequence:
				prev_stage_item = self.task_sequence[stage_index - 1]
				# Handle both string and dict formats (backward compatibility)
				if isinstance(prev_stage_item, dict):
					prev_stage_name = prev_stage_item["subject"]
				else:
					prev_stage_name = prev_stage_item
				# Check if previous stage exists in latest iteration
				prev_stage_exists = any(
					t.get("iteration_number") == latest_iteration and self.is_stage_task(t, prev_stage_name)
					for t in part_tasks
				)
				if not prev_stage_exists:
					status = "Not Started"
				else:
					# Check if blocked by dependencies
					blocked_status = self.check_if_blocked(part_tasks, stage_index, latest_iteration)
					status = blocked_status
			else:
				status = "Not Started"

			# Return status with iteration number
			return f"{status} (Iter {latest_iteration})"

		# Check if task is blocked
		if self.is_task_blocked(latest_task, part_tasks):
			return f"Blocked (Iter {latest_iteration})"

		# Return status based on task status with iteration number
		task_status = latest_task.get("status", "Open")
		status_map = {
			"Open": "Not Started",
			"Working": "In Progress",
			"Completed": "Completed",
			"Cancelled": "Cancelled",
			"Overdue": "Overdue",
		}

		mapped_status = status_map.get(task_status, task_status)
		return f"{mapped_status} (Iter {latest_iteration})"

	def get_stage_status_for_part_and_iteration(
		self, tasks, part_code, stage_index, stage_name, iteration_number
	):
		"""
		Get the status of a stage for a specific part and iteration.
		Used in "Show All Iterations" view.

		If a task doesn't exist in the current iteration, the status from the most recent
		previous iteration that had a task for this stage will be returned.

		Args:
			tasks (list): All tasks for the project
			part_code (str): Part/Item code
			stage_index (int): Index of stage in task sequence
			stage_name (str): Name of the stage
			iteration_number (int): Specific iteration number to check

		Returns:
			str: Status string (e.g., "Completed", "Not Started", "Blocked")
		"""
		# Filter tasks for this part (all iterations, not just current)
		all_part_tasks = [t for t in tasks if t.get("part_number") == part_code]

		# Filter tasks for this part and iteration
		part_tasks = [t for t in all_part_tasks if t.get("iteration_number") == iteration_number]

		# Special handling for RFQ Data (stage_index == 0)
		if stage_index == 0:
			# RFQ Data always exists in iteration 0
			if iteration_number == 0:
				# Check if RFQ Data task exists and its status
				rfq_task = None
				for t in part_tasks:
					if self.is_stage_task(t, stage_name):
						rfq_task = t
						break

				if rfq_task:
					# Check if task is blocked
					if self.is_task_blocked(rfq_task, part_tasks):
						return "Blocked"

					# Return status based on task status
					task_status = rfq_task.get("status", "Open")
					status_map = {
						"Open": "Not Started",
						"Working": "In Progress",
						"Completed": "Completed",
						"Cancelled": "Cancelled",
						"Overdue": "Overdue",
					}
					return status_map.get(task_status, task_status)
				else:
					return "Not Started"
			else:
				# RFQ Data only exists in iteration 0, so for other iterations show status from iteration 0
				# Check iteration 0 for RFQ Data status
				rfq_iter_0_tasks = [t for t in all_part_tasks if t.get("iteration_number") == 0]
				rfq_task = None
				for t in rfq_iter_0_tasks:
					if self.is_stage_task(t, stage_name):
						rfq_task = t
						break

				if rfq_task:
					task_status = rfq_task.get("status", "Open")
					status_map = {
						"Open": "Not Started",
						"Working": "In Progress",
						"Completed": "Completed",
						"Cancelled": "Cancelled",
						"Overdue": "Overdue",
					}
					return status_map.get(task_status, task_status)
				else:
					return "Not Started"

		# For other stages, check if task exists in this iteration
		iteration_task = None
		for t in part_tasks:
			if self.is_stage_task(t, stage_name):
				iteration_task = t
				break

		if not iteration_task:
			# Task doesn't exist in this iteration
			# Look for status from previous iterations (in descending order)
			# This cascades the status from the most recent previous iteration that had this stage
			for prev_iter in range(iteration_number - 1, -1, -1):
				prev_iter_tasks = [t for t in all_part_tasks if t.get("iteration_number") == prev_iter]
				prev_iter_task = None
				for t in prev_iter_tasks:
					if self.is_stage_task(t, stage_name):
						prev_iter_task = t
						break

				if prev_iter_task:
					# Found a task in a previous iteration, return its status (cascade it forward)
					task_status = prev_iter_task.get("status", "Open")
					status_map = {
						"Open": "Not Started",
						"Working": "In Progress",
						"Completed": "Completed",
						"Cancelled": "Cancelled",
						"Overdue": "Overdue",
					}
					mapped_status = status_map.get(task_status, task_status)
					# Return the cascaded status (no iteration number in "Show All Iterations" view)
					# IMPORTANT: Always cascade the status, even if it's "Cancelled" or other statuses
					return mapped_status

			# No task found in any previous iteration
			# This means the stage was never attempted in any previous iteration
			# Check if previous stage exists in this iteration to determine if it's blocked
			if stage_index > 0 and self.task_sequence:
				prev_stage_item = self.task_sequence[stage_index - 1]
				# Handle both string and dict formats (backward compatibility)
				if isinstance(prev_stage_item, dict):
					prev_stage_name = prev_stage_item["subject"]
				else:
					prev_stage_name = prev_stage_item

				# Check if previous stage exists in this iteration
				prev_stage_exists = any(self.is_stage_task(t, prev_stage_name) for t in part_tasks)

				if not prev_stage_exists:
					return "Not Started"
				else:
					# Check if blocked by dependencies
					blocked_status = self.check_if_blocked(part_tasks, stage_index, iteration_number)
					return blocked_status
			else:
				return "Not Started"

		# Check if task is blocked (use all_part_tasks to check dependencies across iterations if needed)
		# For "Show All Iterations" view, we check dependencies within the same iteration
		if self.is_task_blocked(iteration_task, all_part_tasks):
			return "Blocked"

		# Return status based on task status
		task_status = iteration_task.get("status", "Open")
		status_map = {
			"Open": "Not Started",
			"Working": "In Progress",
			"Completed": "Completed",
			"Cancelled": "Cancelled",
			"Overdue": "Overdue",
		}

		return status_map.get(task_status, task_status)

	def is_stage_task(self, task, stage_name):
		"""Check if a task belongs to a specific stage."""
		# Use stage_type field to match tasks to stages
		task_stage_type = task.get("stage_type")
		return task_stage_type == stage_name

	def check_if_blocked(self, part_tasks, stage_index, iteration_number):
		"""Check if a stage is blocked due to unmet dependencies."""
		if stage_index == 0:
			return "Not Started"  # RFQ Data is never blocked

		# Check if previous stage is completed in this iteration
		if not self.task_sequence or stage_index < 1:
			return "Not Started"
		prev_stage_item = self.task_sequence[stage_index - 1]
		# Handle both string and dict formats (backward compatibility)
		if isinstance(prev_stage_item, dict):
			prev_stage_name = prev_stage_item["subject"]
		else:
			prev_stage_name = prev_stage_item
		prev_stage_task = None

		for t in part_tasks:
			if t.get("iteration_number") == iteration_number and self.is_stage_task(t, prev_stage_name):
				prev_stage_task = t
				break

		if not prev_stage_task:
			return "Blocked"

		if prev_stage_task.get("status") not in ("Completed", "Cancelled"):
			return "Blocked"

		return "Not Started"

	def is_task_blocked(self, task, all_part_tasks):
		"""Check if a task is blocked due to unmet dependencies."""
		# Get task document to access depends_on child table
		try:
			task_doc = frappe.get_doc("Task", task.get("name"))
		except frappe.DoesNotExistError:
			return False

		if not task_doc.depends_on or len(task_doc.depends_on) == 0:
			return False

		# Check each dependency
		for dep in task_doc.depends_on:
			dep_task_name = dep.task
			if not dep_task_name:
				continue

			# Find the dependency task
			dep_task = None
			for t in all_part_tasks:
				if t.get("name") == dep_task_name:
					dep_task = t
					break

			if not dep_task:
				# Try to get the dependency task from database
				try:
					dep_task_doc = frappe.get_doc("Task", dep_task_name)
					dep_task = {
						"name": dep_task_doc.name,
						"status": dep_task_doc.status,
						"part_number": dep_task_doc.part_number,
						"iteration_number": dep_task_doc.iteration_number,
					}
				except frappe.DoesNotExistError:
					return True  # Dependency task not found, consider blocked

			# Only check dependencies within the same part and iteration
			if dep_task.get("part_number") == task.get("part_number") and dep_task.get(
				"iteration_number"
			) == task.get("iteration_number"):
				# Check if dependency is completed or cancelled
				if dep_task.get("status") not in ("Completed", "Cancelled"):
					return True  # Dependency not met

		return False


@frappe.whitelist()
def get_task_details(project, part_number, stage_name):
	"""
	Get task details for a specific part and stage.

	Args:
		project (str): Project name
		part_number (str): Part/Item code
		stage_name (str): Stage name

	Returns:
		list: List of task dictionaries with details
	"""
	# Get all tasks for this project, part, and stage
	# Filter directly using stage_type field
	tasks = frappe.get_all(
		"Task",
		filters={
			"project": project,
			"part_number": part_number,
			"stage_type": stage_name,
		},
		fields=[
			"name",
			"subject",
			"part_number",
			"iteration_number",
			"status",
			"progress",
			"exp_start_date",
			"exp_end_date",
			"stage_type",
		],
		order_by="iteration_number, creation",
	)

	return tasks
