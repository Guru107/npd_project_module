# Copyright (c) 2025, Guru107 and contributors
# For license information, please see license.txt

"""
Unit tests for task_generation.py
"""

import frappe
from frappe.tests import IntegrationTestCase

from npd_project_module.tests.utils import (
	NPDProjectModuleTestSuite,
	cleanup_test_data,
	make_test_item,
	make_test_project,
)
from npd_project_module.utils.task_generation import (
	delete_tasks_for_part,
	generate_tasks_for_part,
	get_task_sequence_from_template,
	tasks_exist_for_part,
)


class TestTaskGeneration(NPDProjectModuleTestSuite):
	"""Test cases for task generation utilities."""

	def setUp(self):
		super().setUp()
		self.test_project = None
		self.test_item = None

	def tearDown(self):
		if self.test_project:
			cleanup_test_data(project_name=self.test_project.project_name)
		if self.test_item:
			cleanup_test_data(item_codes=[self.test_item.item_code])
		super().tearDown()

	def test_get_task_sequence_from_template(self):
		"""Test getting task sequence from NPD Template."""
		sequence = get_task_sequence_from_template()
		self.assertIsInstance(sequence, list)
		self.assertEqual(len(sequence), 18)
		self.assertEqual(sequence[0], "RFQ Data")
		self.assertEqual(sequence[1], "Internal Team Technical Feasibility")

	def test_get_task_sequence_from_template_with_project(self):
		"""Test getting task sequence from template using project."""
		self.test_project = make_test_project("_Test Project for Sequence")
		sequence = get_task_sequence_from_template(project_name=self.test_project.name)
		self.assertIsInstance(sequence, list)
		self.assertEqual(len(sequence), 18)

	def test_get_task_sequence_from_template_fallback(self):
		"""Test fallback to hardcoded sequence if template not found."""
		# Use non-existent template
		sequence = get_task_sequence_from_template(template_name="Non-Existent Template")
		self.assertIsInstance(sequence, list)
		self.assertEqual(len(sequence), 18)  # Should use fallback

	def test_generate_tasks_for_part(self):
		"""Test generating tasks for a part."""
		self.test_item = make_test_item("_Test Part 001")
		self.test_project = make_test_project("_Test Project for Generation")

		# Generate tasks
		created_tasks = generate_tasks_for_part(
			project_name=self.test_project.name,
			part_number=self.test_item.item_code,
			iteration_number=0,
		)

		# Verify tasks were created
		self.assertEqual(len(created_tasks), 18)

		# Verify task details
		for task_name in created_tasks:
			task = frappe.get_doc("Task", task_name)
			self.assertEqual(task.project, self.test_project.name)
			self.assertEqual(task.part_number, self.test_item.item_code)
			self.assertEqual(task.iteration_number, 0)
			self.assertIn(self.test_item.item_name or self.test_item.item_code, task.subject)

	def test_generate_tasks_for_part_with_dependencies(self):
		"""Test that tasks are created with sequential dependencies."""
		self.test_item = make_test_item("_Test Part 002")
		self.test_project = make_test_project("_Test Project for Dependencies")

		created_tasks = generate_tasks_for_part(
			project_name=self.test_project.name,
			part_number=self.test_item.item_code,
			iteration_number=0,
		)

		# Verify dependencies
		for i in range(1, len(created_tasks)):
			task = frappe.get_doc("Task", created_tasks[i])
			self.assertGreater(len(task.depends_on), 0)
			# First task should depend on previous task
			self.assertEqual(task.depends_on[0].task, created_tasks[i - 1])

	def test_generate_tasks_for_part_idempotent(self):
		"""Test that generating tasks twice doesn't create duplicates."""
		self.test_item = make_test_item("_Test Part 003")
		self.test_project = make_test_project("_Test Project for Idempotency")

		# Generate tasks first time
		created_tasks_1 = generate_tasks_for_part(
			project_name=self.test_project.name,
			part_number=self.test_item.item_code,
			iteration_number=0,
		)
		self.assertEqual(len(created_tasks_1), 18)

		# Generate tasks second time (should skip)
		created_tasks_2 = generate_tasks_for_part(
			project_name=self.test_project.name,
			part_number=self.test_item.item_code,
			iteration_number=0,
		)
		self.assertEqual(len(created_tasks_2), 0)  # Should return empty list

		# Verify no duplicates
		task_count = frappe.db.count(
			"Task",
			filters={
				"project": self.test_project.name,
				"part_number": self.test_item.item_code,
				"iteration_number": 0,
			},
		)
		self.assertEqual(task_count, 18)

	def test_tasks_exist_for_part(self):
		"""Test checking if tasks exist for a part."""
		self.test_item = make_test_item("_Test Part 004")
		self.test_project = make_test_project("_Test Project for Existence Check")

		# Initially no tasks should exist
		self.assertFalse(
			tasks_exist_for_part(
				project_name=self.test_project.name,
				part_number=self.test_item.item_code,
				iteration_number=0,
			)
		)

		# Generate tasks
		generate_tasks_for_part(
			project_name=self.test_project.name,
			part_number=self.test_item.item_code,
			iteration_number=0,
		)

		# Now tasks should exist
		self.assertTrue(
			tasks_exist_for_part(
				project_name=self.test_project.name,
				part_number=self.test_item.item_code,
				iteration_number=0,
			)
		)

	def test_delete_tasks_for_part(self):
		"""Test deleting all tasks for a part."""
		self.test_item = make_test_item("_Test Part 005")
		self.test_project = make_test_project("_Test Project for Deletion")

		# Generate tasks
		generate_tasks_for_part(
			project_name=self.test_project.name,
			part_number=self.test_item.item_code,
			iteration_number=0,
		)

		# Verify tasks exist
		task_count_before = frappe.db.count(
			"Task",
			filters={
				"project": self.test_project.name,
				"part_number": self.test_item.item_code,
			},
		)
		self.assertEqual(task_count_before, 18)

		# Delete tasks
		deleted_count = delete_tasks_for_part(
			project_name=self.test_project.name, part_number=self.test_item.item_code
		)
		self.assertEqual(deleted_count, 18)

		# Verify tasks deleted
		task_count_after = frappe.db.count(
			"Task",
			filters={
				"project": self.test_project.name,
				"part_number": self.test_item.item_code,
			},
		)
		self.assertEqual(task_count_after, 0)

	def test_generate_tasks_for_part_multiple_iterations(self):
		"""Test generating tasks for multiple iterations."""
		self.test_item = make_test_item("_Test Part 006")
		self.test_project = make_test_project("_Test Project for Multiple Iterations")

		# Generate tasks for iteration 0
		tasks_iter_0 = generate_tasks_for_part(
			project_name=self.test_project.name,
			part_number=self.test_item.item_code,
			iteration_number=0,
		)
		self.assertEqual(len(tasks_iter_0), 18)

		# Generate tasks for iteration 1
		tasks_iter_1 = generate_tasks_for_part(
			project_name=self.test_project.name,
			part_number=self.test_item.item_code,
			iteration_number=1,
		)
		self.assertEqual(len(tasks_iter_1), 18)

		# Verify both iterations have tasks
		task_count_iter_0 = frappe.db.count(
			"Task",
			filters={
				"project": self.test_project.name,
				"part_number": self.test_item.item_code,
				"iteration_number": 0,
			},
		)
		task_count_iter_1 = frappe.db.count(
			"Task",
			filters={
				"project": self.test_project.name,
				"part_number": self.test_item.item_code,
				"iteration_number": 1,
			},
		)

		self.assertEqual(task_count_iter_0, 18)
		self.assertEqual(task_count_iter_1, 18)

	def test_generate_tasks_for_part_validation(self):
		"""Test validation errors for task generation."""
		# Test missing project name
		with self.assertRaises(frappe.ValidationError):
			generate_tasks_for_part(project_name=None, part_number="Test", iteration_number=0)

		# Test missing part number
		with self.assertRaises(frappe.ValidationError):
			generate_tasks_for_part(project_name="Test", part_number=None, iteration_number=0)

