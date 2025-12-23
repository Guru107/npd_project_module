# Copyright (c) 2025, Guru107 and contributors
# For license information, please see license.txt

"""
Unit tests for task_utils.py
"""

import frappe
from frappe.tests import IntegrationTestCase

from npd_project_module.tests.utils import (
	NPDProjectModuleTestSuite,
	cleanup_test_data,
	make_test_item,
	make_test_project,
	make_test_task,
)
from npd_project_module.utils.task_generation import generate_tasks_for_part
from npd_project_module.utils.task_utils import (
	check_task_blocked_status,
	handle_task_cancellation,
	validate_task_cancellation,
	validate_task_dependencies,
)


class TestTaskUtils(NPDProjectModuleTestSuite):
	"""Test cases for task utility functions."""

	def setUp(self):
		super().setUp()
		self.test_item = None
		self.test_project = None

	def tearDown(self):
		if self.test_project:
			cleanup_test_data(project_name=self.test_project.project_name)
		if self.test_item:
			cleanup_test_data(item_codes=[self.test_item.item_code])
		super().tearDown()

	def test_validate_task_cancellation_rfq_data(self):
		"""Test that RFQ Data (1st stage) cannot be cancelled."""
		self.test_item = make_test_item("_Test Item RFQ Cancel")
		self.test_project = make_test_project("_Test Project RFQ Cancel")

		# Generate tasks
		generate_tasks_for_part(
			project_name=self.test_project.name,
			part_number=self.test_item.item_code,
			iteration_number=0,
		)

		# Get RFQ Data task (first task)
		tasks = frappe.get_all(
			"Task",
			filters={
				"project": self.test_project.name,
				"part_number": self.test_item.item_code,
				"iteration_number": 0,
			},
			order_by="creation",
			limit=1,
		)

		if tasks:
			task = frappe.get_doc("Task", tasks[0]["name"])
			result = validate_task_cancellation(
				task_name=task.name,
				part_number=self.test_item.item_code,
				subject=task.subject,
			)
			self.assertFalse(result["valid"])
			self.assertIn("RFQ Data", result["message"])
			self.assertIn("cannot be cancelled", result["message"])

	def test_validate_task_cancellation_other_task(self):
		"""Test that other tasks (not RFQ Data) can be cancelled."""
		self.test_item = make_test_item("_Test Item Other Cancel")
		self.test_project = make_test_project("_Test Project Other Cancel")

		# Generate tasks
		generate_tasks_for_part(
			project_name=self.test_project.name,
			part_number=self.test_item.item_code,
			iteration_number=0,
		)

		# Get second task (not RFQ Data)
		tasks = frappe.get_all(
			"Task",
			filters={
				"project": self.test_project.name,
				"part_number": self.test_item.item_code,
				"iteration_number": 0,
			},
			order_by="creation",
		)

		if len(tasks) > 1:
			task = frappe.get_doc("Task", tasks[1]["name"])
			result = validate_task_cancellation(
				task_name=task.name,
				part_number=self.test_item.item_code,
				subject=task.subject,
			)
			self.assertTrue(result["valid"])

	def test_validate_task_dependencies_within_iteration(self):
		"""Test dependency validation within same iteration."""
		self.test_item = make_test_item("_Test Item Deps 1")
		self.test_project = make_test_project("_Test Project Deps 1")

		# Generate tasks
		generate_tasks_for_part(
			project_name=self.test_project.name,
			part_number=self.test_item.item_code,
			iteration_number=0,
		)

		# Get tasks
		tasks = frappe.get_all(
			"Task",
			filters={
				"project": self.test_project.name,
				"part_number": self.test_item.item_code,
				"iteration_number": 0,
			},
			order_by="creation",
		)

		if len(tasks) > 1:
			# Try to complete second task before first
			task2 = frappe.get_doc("Task", tasks[1]["name"])
			result = validate_task_dependencies(
				task_name=task2.name,
				part_number=self.test_item.item_code,
				iteration_number=0,
				status="Completed",
			)
			self.assertFalse(result["valid"])
			self.assertIn("dependent task", result["message"])

			# Complete first task
			task1 = frappe.get_doc("Task", tasks[0]["name"])
			frappe.db.set_value("Task", task1.name, "status", "Completed")
			frappe.db.commit()

			# Now should be able to complete second task
			result = validate_task_dependencies(
				task_name=task2.name,
				part_number=self.test_item.item_code,
				iteration_number=0,
				status="Completed",
			)
			self.assertTrue(result["valid"])

	def test_validate_task_dependencies_across_iterations(self):
		"""Test that dependencies are not enforced across iterations."""
		self.test_item = make_test_item("_Test Item Cross Iter")
		self.test_project = make_test_project("_Test Project Cross Iter")

		# Generate tasks for iteration 0
		generate_tasks_for_part(
			project_name=self.test_project.name,
			part_number=self.test_item.item_code,
			iteration_number=0,
		)

		# Generate tasks for iteration 1 (starting from 2nd stage)
		from npd_project_module.utils.iteration_management import generate_tasks_from_cancelled_task

		generate_tasks_from_cancelled_task(
			project_name=self.test_project.name,
			part_number=self.test_item.item_code,
			iteration_number=1,
			start_index=1,
		)

		# Get first task from iteration 1
		tasks_iter_1 = frappe.get_all(
			"Task",
			filters={
				"project": self.test_project.name,
				"part_number": self.test_item.item_code,
				"iteration_number": 1,
			},
			order_by="creation",
		)

		if tasks_iter_1:
			# Task in iteration 1 should not depend on tasks in iteration 0
			task_iter_1 = frappe.get_doc("Task", tasks_iter_1[0]["name"])
			# Should be able to complete even if iteration 0 tasks are incomplete
			result = validate_task_dependencies(
				task_name=task_iter_1.name,
				part_number=self.test_item.item_code,
				iteration_number=1,
				status="Completed",
			)
			# Should be valid (no cross-iteration dependencies)
			self.assertTrue(result["valid"])

	def test_handle_task_cancellation_cascade(self):
		"""Test cascading cancellation of subsequent tasks."""
		self.test_item = make_test_item("_Test Item Cascade")
		self.test_project = make_test_project("_Test Project Cascade")

		# Generate tasks
		generate_tasks_for_part(
			project_name=self.test_project.name,
			part_number=self.test_item.item_code,
			iteration_number=0,
		)

		# Get tasks
		tasks = frappe.get_all(
			"Task",
			filters={
				"project": self.test_project.name,
				"part_number": self.test_item.item_code,
				"iteration_number": 0,
				"status": ["!=", "Cancelled"],
			},
			order_by="creation",
		)

		if len(tasks) > 2:
			# Cancel second task (not RFQ Data)
			task_to_cancel = frappe.get_doc("Task", tasks[1]["name"])
			frappe.db.set_value("Task", task_to_cancel.name, "status", "Cancelled")
			frappe.db.commit()

			# Handle cancellation
			result = handle_task_cancellation(
				task_name=task_to_cancel.name,
				part_number=self.test_item.item_code,
				iteration_number=0,
				project_name=self.test_project.name,
			)

			self.assertTrue(result["success"])
			self.assertGreater(result["cancelled_count"], 0)

			# Verify subsequent tasks are cancelled
			subsequent_tasks = frappe.get_all(
				"Task",
				filters={
					"project": self.test_project.name,
					"part_number": self.test_item.item_code,
					"iteration_number": 0,
					"status": "Cancelled",
				},
			)
			# Should have cancelled task + subsequent tasks
			self.assertGreater(len(subsequent_tasks), 1)

	def test_check_task_blocked_status(self):
		"""Test checking if tasks are blocked by dependencies."""
		self.test_item = make_test_item("_Test Item Blocked")
		self.test_project = make_test_project("_Test Project Blocked")

		# Generate tasks
		generate_tasks_for_part(
			project_name=self.test_project.name,
			part_number=self.test_item.item_code,
			iteration_number=0,
		)

		# Get tasks
		tasks = frappe.get_all(
			"Task",
			filters={
				"project": self.test_project.name,
				"part_number": self.test_item.item_code,
				"iteration_number": 0,
			},
			order_by="creation",
		)

		task_names = [task["name"] for task in tasks[:5]]  # Check first 5 tasks

		# Check blocked status
		result = check_task_blocked_status(task_names)
		self.assertIsInstance(result, dict)

		# First task should not be blocked (no dependencies)
		if task_names:
			self.assertFalse(result.get(task_names[0], True))

		# Second task should be blocked (depends on first)
		if len(task_names) > 1:
			self.assertTrue(result.get(task_names[1], False))

		# Complete first task
		if task_names:
			frappe.db.set_value("Task", task_names[0], "status", "Completed")
			frappe.db.commit()

		# Check again - second task should no longer be blocked
		result = check_task_blocked_status(task_names)
		if len(task_names) > 1:
			self.assertFalse(result.get(task_names[1], True))

