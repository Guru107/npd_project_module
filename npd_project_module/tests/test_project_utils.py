# Copyright (c) 2025, Guru107 and contributors
# For license information, please see license.txt

"""
Unit tests for project_utils.py
"""

import frappe

from npd_project_module.tests.compat import IntegrationTestCase
from npd_project_module.tests.utils import (
	NPDProjectModuleTestSuite,
	cleanup_test_data,
	make_test_item,
	make_test_project,
	make_test_project_with_parts,
)
from npd_project_module.utils.project_utils import (
	handle_project_delete,
	handle_project_save,
	validate_project_parts,
)


class TestProjectUtils(NPDProjectModuleTestSuite):
	"""Test cases for project utility functions."""

	def setUp(self):
		super().setUp()
		self.test_items = []
		self.test_projects = []

	def tearDown(self):
		for project_name in self.test_projects:
			cleanup_test_data(project_name=project_name)
		item_codes = [item.item_code for item in self.test_items]
		cleanup_test_data(item_codes=item_codes)
		super().tearDown()

	def test_validate_project_parts_empty(self):
		"""Test validation with empty part numbers list."""
		result = validate_project_parts(project_name="Test", part_numbers=[])
		self.assertTrue(result["valid"])

	def test_validate_project_parts_no_conflict(self):
		"""Test validation when items don't belong to other projects."""
		item1 = make_test_item("_Test Item No Conflict 1")
		item2 = make_test_item("_Test Item No Conflict 2")
		self.test_items.extend([item1, item2])

		result = validate_project_parts(
			project_name="Test Project", part_numbers=[item1.item_code, item2.item_code]
		)
		self.assertTrue(result["valid"])

	def test_validate_project_parts_with_conflict(self):
		"""Test validation when item belongs to another project."""
		item = make_test_item("_Test Item With Conflict")
		self.test_items.append(item)

		# Assign item to first project
		project1 = make_test_project("_Test Project 1")
		frappe.db.set_value("Item", item.item_code, "project", project1.name)
		frappe.db.commit()
		self.test_projects.append(project1.project_name)

		# Try to assign same item to second project
		result = validate_project_parts(project_name="Test Project 2", part_numbers=[item.item_code])
		self.assertFalse(result["valid"])
		self.assertIn("already belongs to", result["message"])

	def test_handle_project_save_new_project(self):
		"""Test handling save for new project with parts."""
		item1 = make_test_item("_Test Item Save 1")
		item2 = make_test_item("_Test Item Save 2")
		self.test_items.extend([item1, item2])

		project = make_test_project("_Test Project Save New")
		self.test_projects.append(project.project_name)

		part_numbers_data = [
			{"part_number": item1.item_code, "iteration_number": 0},
			{"part_number": item2.item_code, "iteration_number": 0},
		]

		result = handle_project_save(project.name, part_numbers_data, is_new=True)
		self.assertTrue(result["success"])

		# Verify tasks were generated
		tasks = frappe.get_all("Task", filters={"project": project.name})
		self.assertEqual(len(tasks), 36)  # 2 parts * 18 tasks

		# Verify item project fields were set
		item1_project = frappe.db.get_value("Item", item1.item_code, "project")
		item2_project = frappe.db.get_value("Item", item2.item_code, "project")
		self.assertEqual(item1_project, project.name)
		self.assertEqual(item2_project, project.name)

	def test_handle_project_save_update_add_parts(self):
		"""Test handling save when adding new parts to existing project."""
		item1 = make_test_item("_Test Item Update 1")
		item2 = make_test_item("_Test Item Update 2")
		self.test_items.extend([item1, item2])

		# Create project with one part
		project = make_test_project_with_parts("_Test Project Update", [item1.item_code])
		self.test_projects.append(project.project_name)

		# Add second part
		part_numbers_data = [
			{"part_number": item1.item_code, "iteration_number": 0},
			{"part_number": item2.item_code, "iteration_number": 0},
		]

		result = handle_project_save(project.name, part_numbers_data, is_new=False)
		self.assertTrue(result["success"])

		# Verify tasks for both parts
		tasks = frappe.get_all("Task", filters={"project": project.name})
		self.assertEqual(len(tasks), 36)  # 2 parts * 18 tasks

	def test_handle_project_save_update_remove_parts(self):
		"""Test handling save when removing parts from project."""
		item1 = make_test_item("_Test Item Remove 1")
		item2 = make_test_item("_Test Item Remove 2")
		self.test_items.extend([item1, item2])

		# Create project with two parts
		project = make_test_project_with_parts("_Test Project Remove", [item1.item_code, item2.item_code])
		self.test_projects.append(project.project_name)

		# Remove second part
		part_numbers_data = [{"part_number": item1.item_code, "iteration_number": 0}]

		result = handle_project_save(project.name, part_numbers_data, is_new=False)
		self.assertTrue(result["success"])

		# Verify tasks for removed part are deleted
		tasks_item2 = frappe.get_all(
			"Task", filters={"project": project.name, "part_number": item2.item_code}
		)
		self.assertEqual(len(tasks_item2), 0)

		# Verify item2 project field cleared
		item2_project = frappe.db.get_value("Item", item2.item_code, "project")
		self.assertIsNone(item2_project)

	def test_handle_project_delete(self):
		"""Test handling project deletion."""
		item1 = make_test_item("_Test Item Delete 1")
		item2 = make_test_item("_Test Item Delete 2")
		self.test_items.extend([item1, item2])

		# Create project with parts and tasks
		project = make_test_project_with_parts("_Test Project Delete", [item1.item_code, item2.item_code])

		# Trigger task generation
		part_numbers_data = [
			{"part_number": item1.item_code, "iteration_number": 0},
			{"part_number": item2.item_code, "iteration_number": 0},
		]
		handle_project_save(project.name, part_numbers_data, is_new=True)

		# Verify tasks exist
		tasks_before = frappe.get_all("Task", filters={"project": project.name})
		self.assertGreater(len(tasks_before), 0)

		# Delete project
		result = handle_project_delete(project.name)
		self.assertTrue(result["success"])

		# Verify tasks deleted
		tasks_after = frappe.get_all("Task", filters={"project": project.name})
		self.assertEqual(len(tasks_after), 0)

		# Verify item project fields cleared
		item1_project = frappe.db.get_value("Item", item1.item_code, "project")
		item2_project = frappe.db.get_value("Item", item2.item_code, "project")
		self.assertIsNone(item1_project)
		self.assertIsNone(item2_project)

	def test_handle_project_save_invalid_data(self):
		"""Test handling save with invalid data formats."""
		project = make_test_project("_Test Project Invalid")
		self.test_projects.append(project.project_name)

		# Test with invalid JSON string - function tries to parse as JSON first
		result = handle_project_save(project.name, "{invalid json}", is_new=True)
		self.assertFalse(result["success"])
		self.assertIn("Invalid part_numbers_data format", result["message"])

		# Test with non-list data (valid JSON but not a list) - use a dict
		# We need to pass valid JSON that's not a list to test the "must be a list" check
		result = handle_project_save(project.name, '{"not": "a list"}', is_new=True)
		self.assertFalse(result["success"])
		self.assertIn("part_numbers_data must be a list", result["message"])
