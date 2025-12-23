# Copyright (c) 2025, Guru107 and contributors
# For license information, please see license.txt

"""
Unit tests for iteration_management.py
"""

import frappe
from frappe.tests import IntegrationTestCase

from npd_project_module.tests.utils import (
	NPDProjectModuleTestSuite,
	cleanup_test_data,
	make_test_item,
	make_test_project,
)
from npd_project_module.utils.iteration_management import (
	create_new_iteration,
	generate_tasks_from_cancelled_task,
	get_cancelled_task_for_part,
	get_incomplete_tasks_count,
	get_iteration_info,
	get_latest_iteration_number,
	mark_tasks_as_obsolete,
	validate_iteration_limit,
)
from npd_project_module.utils.task_generation import generate_tasks_for_part


class TestIterationManagement(NPDProjectModuleTestSuite):
	"""Test cases for iteration management utilities."""

	def setUp(self):
		super().setUp()
		self.test_item = None
		self.test_project = None
		# Clean up any existing test data before starting
		self._cleanup_existing_test_data()

	def tearDown(self):
		if self.test_project:
			cleanup_test_data(project_name=self.test_project.project_name)
		if self.test_item:
			cleanup_test_data(item_codes=[self.test_item.item_code])
		super().tearDown()

	def _cleanup_existing_test_data(self):
		"""Clean up any existing test data that might interfere with tests."""
		# Clean up projects with test names
		test_projects = frappe.get_all(
			"Project",
			filters={"project_name": ["like", "_Test Project Iteration%"]},
			fields=["name", "project_name"],
		)
		for proj in test_projects:
			try:
				cleanup_test_data(project_name=proj.project_name)
			except Exception:
				pass

		# Clean up items with test names
		test_items = frappe.get_all(
			"Item",
			filters={"item_code": ["like", "_Test Item Iteration%"]},
			fields=["item_code"],
		)
		for item in test_items:
			try:
				cleanup_test_data(item_codes=[item.item_code])
			except Exception:
				pass

		frappe.db.commit()

	def test_get_latest_iteration_number(self):
		"""Test getting latest iteration number for a part."""
		self.test_item = make_test_item("_Test Item Iteration 1")
		self.test_project = make_test_project("_Test Project Iteration 1")

		# Initially no iterations - ensure no leftover tasks exist
		# Delete any existing tasks for this part/project combination
		existing_tasks = frappe.get_all(
			"Task",
			filters={
				"project": self.test_project.name,
				"part_number": self.test_item.item_code,
			},
			fields=["name"],
		)
		for task in existing_tasks:
			try:
				frappe.delete_doc("Task", task.name, force=True, ignore_permissions=True)
			except Exception:
				pass
		frappe.db.commit()

		latest = get_latest_iteration_number(self.test_project.name, self.test_item.item_code)
		self.assertIsNone(latest)

		# Create iteration 0
		generate_tasks_for_part(
			project_name=self.test_project.name,
			part_number=self.test_item.item_code,
			iteration_number=0,
		)

		latest = get_latest_iteration_number(self.test_project.name, self.test_item.item_code)
		self.assertEqual(latest, 0)

		# Create iteration 1
		generate_tasks_for_part(
			project_name=self.test_project.name,
			part_number=self.test_item.item_code,
			iteration_number=1,
		)

		latest = get_latest_iteration_number(self.test_project.name, self.test_item.item_code)
		self.assertEqual(latest, 1)

	def test_get_incomplete_tasks_count(self):
		"""Test counting incomplete tasks in an iteration."""
		self.test_item = make_test_item("_Test Item Incomplete 1")
		self.test_project = make_test_project("_Test Project Incomplete 1")

		# Generate tasks
		generate_tasks_for_part(
			project_name=self.test_project.name,
			part_number=self.test_item.item_code,
			iteration_number=0,
		)

		# All tasks should be incomplete initially
		incomplete_count = get_incomplete_tasks_count(
			self.test_project.name, self.test_item.item_code, 0
		)
		self.assertEqual(incomplete_count, 18)

		# Complete first task
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
			frappe.db.set_value("Task", tasks[0]["name"], "status", "Completed")
			frappe.db.commit()

		# Count should decrease
		incomplete_count = get_incomplete_tasks_count(
			self.test_project.name, self.test_item.item_code, 0
		)
		self.assertEqual(incomplete_count, 17)

	def test_get_cancelled_task_for_part(self):
		"""Test finding cancelled task in latest iteration."""
		self.test_item = make_test_item("_Test Item Cancelled 1")
		self.test_project = make_test_project("_Test Project Cancelled 1")

		# Generate tasks
		generate_tasks_for_part(
			project_name=self.test_project.name,
			part_number=self.test_item.item_code,
			iteration_number=0,
		)

		# Cancel a task (not RFQ Data - that's index 0)
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
			frappe.db.set_value("Task", tasks[1]["name"], "status", "Cancelled")
			frappe.db.commit()

		# Find cancelled task
		cancelled_task = get_cancelled_task_for_part(
			self.test_project.name, self.test_item.item_code
		)
		self.assertIsNotNone(cancelled_task)
		self.assertEqual(cancelled_task["iteration_number"], 0)

	def test_validate_iteration_limit(self):
		"""Test iteration limit validation."""
		self.test_item = make_test_item("_Test Item Limit 1")
		self.test_project = make_test_project("_Test Project Limit 1")

		# Initially can create iteration
		result = validate_iteration_limit(self.test_project.name, self.test_item.item_code)
		self.assertTrue(result["can_create"])

		# Create 10 iterations (0-9)
		for i in range(10):
			generate_tasks_for_part(
				project_name=self.test_project.name,
				part_number=self.test_item.item_code,
				iteration_number=i,
			)

		# Should not be able to create more
		result = validate_iteration_limit(self.test_project.name, self.test_item.item_code)
		self.assertFalse(result["can_create"])
		self.assertIn("maximum iteration limit", result["message"])

	def test_get_iteration_info(self):
		"""Test getting iteration information."""
		self.test_item = make_test_item("_Test Item Info 1")
		self.test_project = make_test_project("_Test Project Info 1")

		# Initially no iterations
		info = get_iteration_info(self.test_project.name, self.test_item.item_code)
		self.assertIsNone(info["latest_iteration"])
		self.assertTrue(info["can_create_new"])

		# Create iteration 0
		generate_tasks_for_part(
			project_name=self.test_project.name,
			part_number=self.test_item.item_code,
			iteration_number=0,
		)

		info = get_iteration_info(self.test_project.name, self.test_item.item_code)
		self.assertEqual(info["latest_iteration"], 0)
		self.assertTrue(info["can_create_new"])
		self.assertEqual(info["new_iteration_start_task"]["task_index"], 1)  # Always starts from 2nd stage

	def test_mark_tasks_as_obsolete(self):
		"""Test marking tasks as obsolete."""
		self.test_item = make_test_item("_Test Item Obsolete 1")
		self.test_project = make_test_project("_Test Project Obsolete 1")

		# Generate tasks
		generate_tasks_for_part(
			project_name=self.test_project.name,
			part_number=self.test_item.item_code,
			iteration_number=0,
		)

		# Mark as obsolete
		obsoleted_count = mark_tasks_as_obsolete(
			self.test_project.name, self.test_item.item_code, 0
		)
		self.assertEqual(obsoleted_count, 18)

		# Verify tasks are cancelled
		cancelled_tasks = frappe.get_all(
			"Task",
			filters={
				"project": self.test_project.name,
				"part_number": self.test_item.item_code,
				"iteration_number": 0,
				"status": "Cancelled",
			},
		)
		self.assertEqual(len(cancelled_tasks), 18)

	def test_create_new_iteration(self):
		"""Test creating a new iteration."""
		self.test_item = make_test_item("_Test Item New Iter 1")
		self.test_project = make_test_project("_Test Project New Iter 1")

		# Create iteration 0
		generate_tasks_for_part(
			project_name=self.test_project.name,
			part_number=self.test_item.item_code,
			iteration_number=0,
		)

		# Cancel a task (not RFQ Data)
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
			frappe.db.set_value("Task", tasks[1]["name"], "status", "Cancelled")
			frappe.db.commit()

		# Create new iteration
		result = create_new_iteration(self.test_project.name, self.test_item.item_code)
		self.assertTrue(result["success"])
		self.assertEqual(result["new_iteration_number"], 1)
		self.assertEqual(len(result["tasks_created"]), 17)  # Starts from 2nd stage (17 tasks)

		# Verify new iteration tasks exist
		tasks_iter_1 = frappe.get_all(
			"Task",
			filters={
				"project": self.test_project.name,
				"part_number": self.test_item.item_code,
				"iteration_number": 1,
			},
		)
		self.assertEqual(len(tasks_iter_1), 17)

	def test_create_new_iteration_no_cancelled_task(self):
		"""Test creating iteration when no cancelled task exists."""
		self.test_item = make_test_item("_Test Item No Cancel 1")
		self.test_project = make_test_project("_Test Project No Cancel 1")

		# Create iteration 0 without cancelling any task
		generate_tasks_for_part(
			project_name=self.test_project.name,
			part_number=self.test_item.item_code,
			iteration_number=0,
		)

		# Should fail to create new iteration
		with self.assertRaises(frappe.ValidationError):
			create_new_iteration(self.test_project.name, self.test_item.item_code)

	def test_create_new_iteration_max_limit(self):
		"""Test creating iteration when max limit reached."""
		self.test_item = make_test_item("_Test Item Max Limit 1")
		self.test_project = make_test_project("_Test Project Max Limit 1")

		# Create 10 iterations
		for i in range(10):
			generate_tasks_for_part(
				project_name=self.test_project.name,
				part_number=self.test_item.item_code,
				iteration_number=i,
			)
			# Cancel a task in each iteration (except last)
			if i < 9:
				tasks = frappe.get_all(
					"Task",
					filters={
						"project": self.test_project.name,
						"part_number": self.test_item.item_code,
						"iteration_number": i,
					},
					order_by="creation",
				)
				if len(tasks) > 1:
					frappe.db.set_value("Task", tasks[1]["name"], "status", "Cancelled")
					frappe.db.commit()

		# Cancel a task in iteration 9
		tasks = frappe.get_all(
			"Task",
			filters={
				"project": self.test_project.name,
				"part_number": self.test_item.item_code,
				"iteration_number": 9,
			},
			order_by="creation",
		)
		if len(tasks) > 1:
			frappe.db.set_value("Task", tasks[1]["name"], "status", "Cancelled")
			frappe.db.commit()

		# Should fail to create 11th iteration
		with self.assertRaises(frappe.ValidationError):
			create_new_iteration(self.test_project.name, self.test_item.item_code)

