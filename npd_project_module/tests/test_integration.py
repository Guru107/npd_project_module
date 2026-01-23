# Copyright (c) 2025, Guru107 and contributors
# For license information, please see license.txt

"""
Integration tests for complete workflows in NPD Project Module.
These tests verify end-to-end functionality across multiple components.
"""

import frappe

from npd_project_module.tests.compat import IntegrationTestCase
from npd_project_module.tests.utils import (
	NPDProjectModuleTestSuite,
	cleanup_test_data,
	make_test_item,
	make_test_project_with_parts,
)
from npd_project_module.utils.iteration_management import create_new_iteration
from npd_project_module.utils.project_utils import handle_project_save


class TestIntegrationWorkflows(NPDProjectModuleTestSuite):
	"""Integration tests for complete workflows."""

	def setUp(self):
		super().setUp()
		self.test_items = []
		self.test_projects = []
		# Clean up any existing test data before starting
		self._cleanup_existing_test_data()

	def tearDown(self):
		for project_name in self.test_projects:
			cleanup_test_data(project_name=project_name)
		item_codes = [item.item_code for item in self.test_items]
		cleanup_test_data(item_codes=item_codes)
		super().tearDown()

	def _cleanup_existing_test_data(self):
		"""Clean up any existing test data that might interfere with tests."""
		# Clean up projects with test names
		test_projects = frappe.get_all(
			"Project",
			filters={"project_name": ["like", "_Test Integration%"]},
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
			filters={"item_code": ["like", "_Test Integration%"]},
			fields=["item_code"],
		)
		for item in test_items:
			try:
				cleanup_test_data(item_codes=[item.item_code])
			except Exception:
				pass

		frappe.db.commit()

	def test_complete_workflow_multiple_parts(self):
		"""Test complete workflow: create project with multiple parts, verify task generation."""
		# Create test items
		item1 = make_test_item("_Test Integration Part 1")
		item2 = make_test_item("_Test Integration Part 2")
		item3 = make_test_item("_Test Integration Part 3")
		self.test_items.extend([item1, item2, item3])

		# Create project with parts
		project = make_test_project_with_parts(
			"_Test Integration Project 1", [item1.item_code, item2.item_code, item3.item_code]
		)
		self.test_projects.append(project.project_name)

		# Trigger task generation
		part_numbers_data = [
			{"part_number": item1.item_code, "iteration_number": 0},
			{"part_number": item2.item_code, "iteration_number": 0},
			{"part_number": item3.item_code, "iteration_number": 0},
		]
		result = handle_project_save(project.name, part_numbers_data, is_new=True)
		self.assertTrue(result["success"])

		# Verify tasks generated - filter by part_number and iteration_number to avoid leftover tasks
		tasks = frappe.get_all(
			"Task",
			filters={
				"project": project.name,
				"part_number": ["in", [item1.item_code, item2.item_code, item3.item_code]],
				"iteration_number": 0,
			},
		)
		self.assertEqual(len(tasks), 54)  # 3 parts * 18 tasks

		# Verify each part has 18 tasks
		for item in [item1, item2, item3]:
			item_tasks = frappe.get_all(
				"Task",
				filters={
					"project": project.name,
					"part_number": item.item_code,
					"iteration_number": 0,
				},
			)
			self.assertEqual(len(item_tasks), 18)

		# Verify item project fields set
		for item in [item1, item2, item3]:
			item_project = frappe.db.get_value("Item", item.item_code, "project")
			self.assertEqual(item_project, project.name)

	def test_iteration_workflow(self):
		"""Test complete iteration workflow: create iteration, verify tasks, dependencies."""
		item = make_test_item("_Test Integration Iter Part")
		self.test_items.append(item)

		project = make_test_project_with_parts("_Test Integration Iter Project", [item.item_code])
		self.test_projects.append(project.project_name)

		# Create initial iteration
		part_numbers_data = [{"part_number": item.item_code, "iteration_number": 0}]
		handle_project_save(project.name, part_numbers_data, is_new=True)

		# Verify iteration 0 tasks
		tasks_iter_0 = frappe.get_all(
			"Task",
			filters={
				"project": project.name,
				"part_number": item.item_code,
				"iteration_number": 0,
			},
		)
		self.assertEqual(len(tasks_iter_0), 18)

		# Mark some tasks as completed and cancel one task (not RFQ Data)
		tasks = frappe.get_all(
			"Task",
			filters={
				"project": project.name,
				"part_number": item.item_code,
				"iteration_number": 0,
			},
			order_by="creation",
		)
		completed_tasks = []
		if len(tasks) > 2:
			# Mark task 1 as completed
			frappe.db.set_value("Task", tasks[1]["name"], "status", "Completed")
			completed_tasks.append(tasks[1]["name"])
			# Cancel task 2
			frappe.db.set_value("Task", tasks[2]["name"], "status", "Cancelled")
			frappe.db.commit()

		# Get RFQ Data task (first task)
		rfq_task = tasks[0] if tasks else None

		# Create new iteration
		result = create_new_iteration(project.name, item.item_code)
		self.assertTrue(result["success"])
		self.assertEqual(result["new_iteration_number"], 1)
		self.assertEqual(len(result["tasks_created"]), 17)  # Starts from 2nd stage
		self.assertGreater(result["tasks_cancelled"], 0)  # Should have cancelled tasks
		self.assertGreater(result["tasks_preserved"], 0)  # Should have preserved tasks (completed + RFQ Data)

		# Verify completed tasks are preserved
		for task_name in completed_tasks:
			task_doc = frappe.get_doc("Task", task_name)
			self.assertEqual(task_doc.status, "Completed", f"Task {task_name} should remain Completed")

		# Verify RFQ Data is not cancelled
		if rfq_task:
			rfq_task_doc = frappe.get_doc("Task", rfq_task["name"])
			self.assertNotEqual(rfq_task_doc.status, "Cancelled", "RFQ Data should not be cancelled")

		# Verify iteration 1 tasks
		tasks_iter_1 = frappe.get_all(
			"Task",
			filters={
				"project": project.name,
				"part_number": item.item_code,
				"iteration_number": 1,
			},
		)
		self.assertEqual(len(tasks_iter_1), 17)

		# Verify dependencies within iteration 1
		tasks_iter_1_ordered = frappe.get_all(
			"Task",
			filters={
				"project": project.name,
				"part_number": item.item_code,
				"iteration_number": 1,
			},
			order_by="creation",
		)
		for i in range(1, len(tasks_iter_1_ordered)):
			task = frappe.get_doc("Task", tasks_iter_1_ordered[i]["name"])
			self.assertGreater(len(task.depends_on), 0)
			self.assertEqual(task.depends_on[0].task, tasks_iter_1_ordered[i - 1]["name"])

	def test_part_removal_workflow(self):
		"""Test removing a part from project: verify tasks deleted, item field cleared."""
		item1 = make_test_item("_Test Integration Remove Part 1")
		item2 = make_test_item("_Test Integration Remove Part 2")
		self.test_items.extend([item1, item2])

		project = make_test_project_with_parts(
			"_Test Integration Remove Project", [item1.item_code, item2.item_code]
		)
		self.test_projects.append(project.project_name)

		# Create tasks for both parts
		part_numbers_data = [
			{"part_number": item1.item_code, "iteration_number": 0},
			{"part_number": item2.item_code, "iteration_number": 0},
		]
		handle_project_save(project.name, part_numbers_data, is_new=True)

		# Verify tasks exist - filter by part_number and iteration_number
		tasks_before = frappe.get_all(
			"Task",
			filters={
				"project": project.name,
				"part_number": ["in", [item1.item_code, item2.item_code]],
				"iteration_number": 0,
			},
		)
		self.assertEqual(len(tasks_before), 36)

		# Remove second part
		part_numbers_data = [{"part_number": item1.item_code, "iteration_number": 0}]
		handle_project_save(project.name, part_numbers_data, is_new=False)

		# Verify tasks for removed part deleted
		tasks_item2 = frappe.get_all(
			"Task", filters={"project": project.name, "part_number": item2.item_code}
		)
		self.assertEqual(len(tasks_item2), 0)

		# Verify item2 project field cleared
		item2_project = frappe.db.get_value("Item", item2.item_code, "project")
		self.assertIsNone(item2_project)

		# Verify item1 still has tasks - filter by iteration_number
		tasks_item1 = frappe.get_all(
			"Task",
			filters={
				"project": project.name,
				"part_number": item1.item_code,
				"iteration_number": 0,
			},
		)
		self.assertEqual(len(tasks_item1), 18)

	def test_sequential_dependency_enforcement(self):
		"""Test that tasks cannot be completed out of order within same iteration."""
		item = make_test_item("_Test Integration Seq Dep")
		self.test_items.append(item)

		project = make_test_project_with_parts("_Test Integration Seq Dep Project", [item.item_code])
		self.test_projects.append(project.project_name)

		# Create tasks
		part_numbers_data = [{"part_number": item.item_code, "iteration_number": 0}]
		handle_project_save(project.name, part_numbers_data, is_new=True)

		# Get tasks in order
		tasks = frappe.get_all(
			"Task",
			filters={
				"project": project.name,
				"part_number": item.item_code,
				"iteration_number": 0,
			},
			order_by="creation",
		)

		if len(tasks) > 1:
			# Try to complete second task before first
			from npd_project_module.utils.task_utils import validate_task_dependencies

			task2 = frappe.get_doc("Task", tasks[1]["name"])
			result = validate_task_dependencies(
				task_name=task2.name,
				part_number=item.item_code,
				iteration_number=0,
				status="Completed",
			)
			self.assertFalse(result["valid"])

			# Complete first task
			task1 = frappe.get_doc("Task", tasks[0]["name"])
			frappe.db.set_value("Task", task1.name, "status", "Completed")
			frappe.db.commit()

			# Now should be able to complete second task
			result = validate_task_dependencies(
				task_name=task2.name,
				part_number=item.item_code,
				iteration_number=0,
				status="Completed",
			)
			self.assertTrue(result["valid"])

	def test_rfq_data_protection(self):
		"""Test that RFQ Data (1st stage) cannot be cancelled."""
		item = make_test_item("_Test Integration RFQ Protect")
		self.test_items.append(item)

		project = make_test_project_with_parts("_Test Integration RFQ Protect Project", [item.item_code])
		self.test_projects.append(project.project_name)

		# Create tasks
		part_numbers_data = [{"part_number": item.item_code, "iteration_number": 0}]
		handle_project_save(project.name, part_numbers_data, is_new=True)

		# Get RFQ Data task (first task)
		tasks = frappe.get_all(
			"Task",
			filters={
				"project": project.name,
				"part_number": item.item_code,
				"iteration_number": 0,
			},
			order_by="creation",
			limit=1,
		)

		if tasks:
			from npd_project_module.utils.task_utils import validate_task_cancellation

			task = frappe.get_doc("Task", tasks[0]["name"])
			result = validate_task_cancellation(
				task_name=task.name,
				part_number=item.item_code,
				subject=task.subject,
			)
			self.assertFalse(result["valid"])
			self.assertIn("RFQ Data", result["message"])

	def test_iteration_limit_enforcement(self):
		"""Test that iteration limit (10) is enforced."""
		item = make_test_item("_Test Integration Limit")
		self.test_items.append(item)

		project = make_test_project_with_parts("_Test Integration Limit Project", [item.item_code])
		self.test_projects.append(project.project_name)

		# Create 10 iterations
		from npd_project_module.utils.task_generation import generate_tasks_for_part

		for i in range(10):
			generate_tasks_for_part(
				project_name=project.name,
				part_number=item.item_code,
				iteration_number=i,
			)
			# Cancel a task in each iteration (except last)
			if i < 9:
				tasks = frappe.get_all(
					"Task",
					filters={
						"project": project.name,
						"part_number": item.item_code,
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
				"project": project.name,
				"part_number": item.item_code,
				"iteration_number": 9,
			},
			order_by="creation",
		)
		if len(tasks) > 1:
			frappe.db.set_value("Task", tasks[1]["name"], "status", "Cancelled")
			frappe.db.commit()

		# Try to create 11th iteration - should fail
		with self.assertRaises(frappe.ValidationError):
			create_new_iteration(project.name, item.item_code)

	def test_new_iteration_always_starts_from_second_stage(self):
		"""Test that new iterations always start from 2nd stage regardless of cancelled task."""
		item = make_test_item("_Test Integration Start Stage")
		self.test_items.append(item)

		project = make_test_project_with_parts("_Test Integration Start Stage Project", [item.item_code])
		self.test_projects.append(project.project_name)

		# Create initial iteration
		part_numbers_data = [{"part_number": item.item_code, "iteration_number": 0}]
		handle_project_save(project.name, part_numbers_data, is_new=True)

		# Cancel a task in the middle (e.g., task 5)
		tasks = frappe.get_all(
			"Task",
			filters={
				"project": project.name,
				"part_number": item.item_code,
				"iteration_number": 0,
			},
			order_by="creation",
		)
		if len(tasks) > 5:
			frappe.db.set_value("Task", tasks[5]["name"], "status", "Cancelled")
			frappe.db.commit()

		# Create new iteration
		result = create_new_iteration(project.name, item.item_code)
		self.assertTrue(result["success"])

		# Verify new iteration starts from 2nd stage (17 tasks, not 13)
		tasks_iter_1 = frappe.get_all(
			"Task",
			filters={
				"project": project.name,
				"part_number": item.item_code,
				"iteration_number": 1,
			},
		)
		self.assertEqual(len(tasks_iter_1), 17)  # Starts from 2nd stage

		# Verify first task in iteration 1 is "Internal Team Technical Feasibility"
		tasks_iter_1_ordered = frappe.get_all(
			"Task",
			filters={
				"project": project.name,
				"part_number": item.item_code,
				"iteration_number": 1,
			},
			order_by="creation",
			limit=1,
		)
		if tasks_iter_1_ordered:
			task = frappe.get_doc("Task", tasks_iter_1_ordered[0]["name"])
			self.assertIn("Internal Team Technical Feasibility", task.subject)
