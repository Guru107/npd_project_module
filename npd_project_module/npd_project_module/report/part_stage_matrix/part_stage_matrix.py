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

	Returns:
		tuple: (columns, data, message, chart, report_summary)
	"""
	return PartStageMatrix(filters).run()


class PartStageMatrix:
	def __init__(self, filters=None):
		self.filters = frappe._dict(filters or {})
		self.project = self.filters.get("project")
		self.part_numbers = self.filters.get("part_number") or []
		self.task_sequence = None  # Will be set in get_data()

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

		# Add a column for each part
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
		for stage_index, stage_info in enumerate(self.task_sequence):
			stage_name = stage_info["subject"]
			row = {"stage": stage_name}

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
		Get the status of a stage for a specific part.

		Logic:
		1. Check if stage is completed in any iteration (aggregate across iterations)
		2. If not completed, check latest iteration status
		3. If no task exists, check if it's blocked (dependencies not met)
		4. Return appropriate status string

		Args:
			tasks (list): All tasks for the project
			part_code (str): Part/Item code
			stage_index (int): Index of stage in task sequence
			stage_name (str): Name of the stage

		Returns:
			str: Status string (e.g., "Completed", "In Progress", "Blocked", "Not Started")
		"""
		# Filter tasks for this part
		part_tasks = [t for t in tasks if t.get("part_number") == part_code]

		if not part_tasks:
			return "No Tasks"

		# Check if stage is completed in any iteration (aggregate across iterations)
		completed_tasks = [
			t for t in part_tasks if self.is_stage_task(t, stage_name) and t.get("status") == "Completed"
		]

		if completed_tasks:
			return "Completed"

		# Get latest iteration number for this part
		latest_iteration = max([t.get("iteration_number") or 0 for t in part_tasks], default=0)

		# Get task for this stage in latest iteration
		latest_task = None
		for t in part_tasks:
			if t.get("iteration_number") == latest_iteration and self.is_stage_task(t, stage_name):
				latest_task = t
				break

		if not latest_task:
			# Check if this stage should exist (based on iteration start point)
			# Stage 0 (RFQ Data) always exists
			# Stages 1+ only exist if previous iterations had tasks
			if stage_index == 0:
				# RFQ Data should always exist
				return "Not Started"
			else:
				# Check if previous stage exists in any iteration
				if stage_index > 0 and self.task_sequence:
					prev_stage_info = self.task_sequence[stage_index - 1]
					prev_stage_name = prev_stage_info["subject"]
					prev_stage_exists = any(self.is_stage_task(t, prev_stage_name) for t in part_tasks)
					if not prev_stage_exists:
						return "Not Started"
					else:
						# Check if blocked by dependencies
						return self.check_if_blocked(part_tasks, stage_index, latest_iteration)
				return "Not Started"

		# Check if task is blocked
		if self.is_task_blocked(latest_task, part_tasks):
			return "Blocked"

		# Return status based on task status
		status = latest_task.get("status", "Open")
		status_map = {
			"Open": "Not Started",
			"Working": "In Progress",
			"Completed": "Completed",
			"Cancelled": "Cancelled",
			"Overdue": "Overdue",
		}

		return status_map.get(status, status)

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
		prev_stage_info = self.task_sequence[stage_index - 1]
		prev_stage_name = prev_stage_info["subject"]
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
