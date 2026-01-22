# Copyright (c) 2025, Guru107 and contributors
# For license information, please see license.txt

"""
Unit tests for Part Stage Matrix report.
"""

import frappe
from frappe.tests import IntegrationTestCase

from npd_project_module.npd_project_module.report.part_stage_matrix.part_stage_matrix import (
	PartStageMatrix,
)
from npd_project_module.tests.utils import (
	NPDProjectModuleTestSuite,
	cleanup_test_data,
	make_test_item,
	make_test_project,
)
from npd_project_module.utils.iteration_management import create_new_iteration
from npd_project_module.utils.task_generation import generate_tasks_for_part


class TestPartStageMatrix(NPDProjectModuleTestSuite):
	"""Tests for Part Stage Matrix report."""

	def setUp(self):
		super().setUp()
		self.test_items = []
		self.test_projects = []
		self._cleanup_existing_test_data()

	def tearDown(self):
		for project_name in self.test_projects:
			cleanup_test_data(project_name=project_name)
		item_codes = [item.item_code for item in self.test_items]
		cleanup_test_data(item_codes=item_codes)
		super().tearDown()

	def _cleanup_existing_test_data(self):
		"""Clean up any existing test data that might interfere with tests."""
		test_projects = frappe.get_all(
			"Project",
			filters={"project_name": ["like", "_Test Matrix%"]},
			fields=["name", "project_name"],
		)
		for proj in test_projects:
			try:
				cleanup_test_data(project_name=proj.project_name)
			except Exception:
				pass

	def test_matrix_report_shows_iteration_numbers(self):
		"""Test that default view shows iteration numbers in status strings."""
		# Create test data
		test_item = make_test_item("_Test Matrix Item 1")
		test_project = make_test_project("_Test Matrix Project 1")
		self.test_items.append(test_item)
		self.test_projects.append(test_project.name)

		# Add part to project
		project_doc = frappe.get_doc("Project", test_project.name)
		project_doc.append("part_numbers", {"part_number": test_item.item_code, "iteration_number": 0})
		project_doc.save()
		frappe.db.commit()

		# Generate tasks for iteration 0
		generate_tasks_for_part(
			project_name=test_project.name,
			part_number=test_item.item_code,
			iteration_number=0,
		)

		# Create report instance
		filters = {"project": test_project.name}
		matrix = PartStageMatrix(filters)
		matrix.run()

		# Verify that status strings include iteration numbers
		self.assertGreater(len(matrix.data), 0)
		for row in matrix.data:
			part_code = test_item.item_code
			status = row.get(f"part_{part_code}")
			if status and status != "No Tasks":
				# Status should include iteration number
				self.assertIn("(Iter", status, f"Status '{status}' should include iteration number")

	def test_matrix_report_latest_iteration_only(self):
		"""Test that default view shows only latest iteration status."""
		# Create test data
		test_item = make_test_item("_Test Matrix Item 2")
		test_project = make_test_project("_Test Matrix Project 2")
		self.test_items.append(test_item)
		self.test_projects.append(test_project.name)

		# Add part to project
		project_doc = frappe.get_doc("Project", test_project.name)
		project_doc.append("part_numbers", {"part_number": test_item.item_code, "iteration_number": 0})
		project_doc.save()
		frappe.db.commit()

		# Generate tasks for iteration 0
		generate_tasks_for_part(
			project_name=test_project.name,
			part_number=test_item.item_code,
			iteration_number=0,
		)

		# Mark some tasks as completed in iteration 0
		tasks = frappe.get_all(
			"Task",
			filters={
				"project": test_project.name,
				"part_number": test_item.item_code,
				"iteration_number": 0,
			},
			order_by="creation",
		)
		if len(tasks) > 1:
			frappe.db.set_value("Task", tasks[1]["name"], "status", "Completed")
			frappe.db.commit()

		# Create iteration 1
		create_new_iteration(test_project.name, test_item.item_code)

		# Create report instance
		filters = {"project": test_project.name}
		matrix = PartStageMatrix(filters)
		matrix.run()

		# Verify that status shows iteration 1 (latest), not iteration 0
		self.assertGreater(len(matrix.data), 0)
		for row in matrix.data:
			part_code = test_item.item_code
			status = row.get(f"part_{part_code}")
			if status and status != "No Tasks":
				# Status should show iteration 1 (latest), not iteration 0
				self.assertIn("(Iter 1)", status, f"Status '{status}' should show latest iteration (1)")

	def test_matrix_report_show_all_iterations_view(self):
		"""Test 'Show All Iterations' view functionality."""
		# Create test data
		test_item = make_test_item("_Test Matrix Item 3")
		test_project = make_test_project("_Test Matrix Project 3")
		self.test_items.append(test_item)
		self.test_projects.append(test_project.name)

		# Add part to project
		project_doc = frappe.get_doc("Project", test_project.name)
		project_doc.append("part_numbers", {"part_number": test_item.item_code, "iteration_number": 0})
		project_doc.save()
		frappe.db.commit()

		# Generate tasks for iteration 0
		generate_tasks_for_part(
			project_name=test_project.name,
			part_number=test_item.item_code,
			iteration_number=0,
		)

		# Create iteration 1
		create_new_iteration(test_project.name, test_item.item_code)

		# Create report instance with "Show All Iterations" enabled
		filters = {
			"project": test_project.name,
			"part_number": [test_item.item_code],
			"show_all_iterations": 1,
		}
		matrix = PartStageMatrix(filters)
		matrix.run()

		# Verify columns are created for each iteration
		part_code = test_item.item_code
		iteration_columns = [
			col for col in matrix.columns if col.get("fieldname", "").startswith(f"part_{part_code}_iter_")
		]
		self.assertGreater(len(iteration_columns), 0, "Should have columns for iterations")

		# Verify data has cells for each iteration
		self.assertGreater(len(matrix.data), 0)
		for row in matrix.data:
			# Should have cells for both iterations
			iter_0_cell = row.get(f"part_{part_code}_iter_0")
			iter_1_cell = row.get(f"part_{part_code}_iter_1")
			# At least one iteration should have data
			self.assertTrue(
				iter_0_cell is not None or iter_1_cell is not None,
				"Should have data for at least one iteration",
			)

	def test_matrix_report_column_structure_with_show_all_iterations(self):
		"""Test that column structure changes when 'Show All Iterations' is enabled."""
		# Create test data
		test_item = make_test_item("_Test Matrix Item 4")
		test_project = make_test_project("_Test Matrix Project 4")
		self.test_items.append(test_item)
		self.test_projects.append(test_project.name)

		# Add part to project
		project_doc = frappe.get_doc("Project", test_project.name)
		project_doc.append("part_numbers", {"part_number": test_item.item_code, "iteration_number": 0})
		project_doc.save()
		frappe.db.commit()

		# Generate tasks for iteration 0
		generate_tasks_for_part(
			project_name=test_project.name,
			part_number=test_item.item_code,
			iteration_number=0,
		)

		# Test default view (no show_all_iterations)
		filters_default = {"project": test_project.name}
		matrix_default = PartStageMatrix(filters_default)
		matrix_default.run()

		# Test "Show All Iterations" view
		filters_all = {
			"project": test_project.name,
			"part_number": [test_item.item_code],
			"show_all_iterations": 1,
		}
		matrix_all = PartStageMatrix(filters_all)
		matrix_all.run()

		# Verify column structure is different
		part_code = test_item.item_code
		default_columns = [col for col in matrix_default.columns if f"part_{part_code}" in col.get("fieldname", "")]
		all_iter_columns = [
			col for col in matrix_all.columns if col.get("fieldname", "").startswith(f"part_{part_code}_iter_")
		]

		# Default view should have one column per part
		self.assertEqual(len(default_columns), 1, "Default view should have one column per part")

		# "Show All Iterations" view should have multiple columns (one per iteration)
		self.assertGreater(
			len(all_iter_columns), 0, "Show All Iterations view should have columns for iterations"
		)

	def test_matrix_report_status_cascading(self):
		"""Test that status cascades from previous iterations when task doesn't exist."""
		# Create test data
		test_item = make_test_item("_Test Matrix Item 5")
		test_project = make_test_project("_Test Matrix Project 5")
		self.test_items.append(test_item)
		self.test_projects.append(test_project.name)

		# Add part to project
		project_doc = frappe.get_doc("Project", test_project.name)
		project_doc.append("part_numbers", {"part_number": test_item.item_code, "iteration_number": 0})
		project_doc.save()
		frappe.db.commit()

		# Generate tasks for iteration 0
		generate_tasks_for_part(
			project_name=test_project.name,
			part_number=test_item.item_code,
			iteration_number=0,
		)

		# Get tasks in order
		tasks = frappe.get_all(
			"Task",
			filters={
				"project": test_project.name,
				"part_number": test_item.item_code,
				"iteration_number": 0,
			},
			order_by="creation",
		)

		# First complete RFQ Data (first task) to unblock subsequent tasks
		if tasks:
			rfq_task_doc = None
			for t in tasks:
				task_doc = frappe.get_doc("Task", t["name"])
				if getattr(task_doc, "stage_type", None) == "RFQ Data" and getattr(task_doc, "iteration_number", None) == 0:
					rfq_task_doc = task_doc
					break
			rfq_task_doc.status = "Completed"
			rfq_task_doc.save(ignore_permissions=True)
			frappe.db.commit()
			# Verify RFQ Data is completed
			rfq_task_doc.reload()
			self.assertEqual(rfq_task_doc.status, "Completed", "RFQ Data should be completed")

		# Mark a task as completed in iteration 0 that will NOT be recreated in iteration 1
		# Iteration 1 starts from the 2nd stage, so RFQ Data (1st stage) won't be recreated
		# So we'll use RFQ Data to test cascading (it's already completed above)
		completed_task = None
		if tasks:
			# Find RFQ Data task (stage_type = "RFQ Data")
			for t in tasks:
				task_doc = frappe.get_doc("Task", t["name"])
				if getattr(task_doc, "stage_type", None) == "RFQ Data":
					completed_task = t
					# RFQ Data is already completed above, so we just need to track it
					break

		# Verify RFQ Data task was found and is completed
		if completed_task:
			completed_task_doc = frappe.get_doc("Task", completed_task["name"])
			self.assertEqual(completed_task_doc.status, "Completed", "RFQ Data should be completed")

		# Create iteration 1 (this will cancel non-completed tasks from iteration 0)
		create_new_iteration(test_project.name, test_item.item_code)

		# Verify the completed task is still completed (not cancelled)
		if completed_task:
			completed_task_after = frappe.get_doc("Task", completed_task["name"])
			self.assertEqual(
				completed_task_after.status,
				"Completed",
				f"Task {completed_task['name']} should remain Completed after iteration creation",
			)

		# Create report instance with "Show All Iterations" enabled
		filters = {
			"project": test_project.name,
			"part_number": [test_item.item_code],
			"show_all_iterations": 1,
		}
		matrix = PartStageMatrix(filters)
		matrix.run()

		# Verify that iteration 1 shows status from iteration 0 for the completed task's stage
		if completed_task:
			completed_task_doc = frappe.get_doc("Task", completed_task["name"])
			stage_type = completed_task_doc.stage_type

			# Verify the task is still in iteration 0 and completed
			tasks_in_iter_0 = frappe.get_all(
				"Task",
				filters={
					"project": test_project.name,
					"part_number": test_item.item_code,
					"iteration_number": 0,
					"stage_type": stage_type,
				},
				fields=["name", "status", "stage_type"],
			)
			self.assertGreater(len(tasks_in_iter_0), 0, "Task should exist in iteration 0")
			self.assertEqual(
				tasks_in_iter_0[0]["status"],
				"Completed",
				f"Task {tasks_in_iter_0[0]['name']} should be Completed in iteration 0",
			)

			# Find the row for this stage
			for row in matrix.data:
				if row.get("stage") == stage_type:
					# Iteration 0 should show "Completed"
					iter_0_status = row.get(f"part_{test_item.item_code}_iter_0")
					# Iteration 1 should show the status from iteration 1's task if it exists;
					# only if there is no task in iteration 1 for this stage, the status should cascade from iteration 0
					iter_1_status = row.get(f"part_{test_item.item_code}_iter_1")
					self.assertEqual(iter_0_status, "Completed", "Iteration 0 should show Completed")
					self.assertEqual(iter_1_status, "Completed", "Iteration 1 should cascade Completed status")
					return  # Found the row, exit

			# If we get here, the row wasn't found
			self.fail(f"Row for stage '{stage_type}' not found in matrix data")

	def test_matrix_report_rfq_data_iteration_0_status(self):
		"""Test that RFQ Data always shows status from iteration 0 in 'Show All Iterations' view."""
		# Create test data
		test_item = make_test_item("_Test Matrix Item 6")
		test_project = make_test_project("_Test Matrix Project 6")
		self.test_items.append(test_item)
		self.test_projects.append(test_project.name)

		# Add part to project
		project_doc = frappe.get_doc("Project", test_project.name)
		project_doc.append("part_numbers", {"part_number": test_item.item_code, "iteration_number": 0})
		project_doc.save()
		frappe.db.commit()

		# Generate tasks for iteration 0
		generate_tasks_for_part(
			project_name=test_project.name,
			part_number=test_item.item_code,
			iteration_number=0,
		)

		# Mark RFQ Data as completed in iteration 0
		tasks = frappe.get_all(
			"Task",
			filters={
				"project": test_project.name,
				"part_number": test_item.item_code,
				"iteration_number": 0,
			},
			order_by="creation",
		)
		if tasks:
			rfq_task = tasks[0]  # RFQ Data is first
			frappe.db.set_value("Task", rfq_task["name"], "status", "Completed")
			frappe.db.commit()

		# Create iteration 1
		create_new_iteration(test_project.name, test_item.item_code)

		# Create report instance with "Show All Iterations" enabled
		filters = {
			"project": test_project.name,
			"part_number": [test_item.item_code],
			"show_all_iterations": 1,
		}
		matrix = PartStageMatrix(filters)
		matrix.run()

		# Verify RFQ Data row shows "Completed" for both iterations (cascaded from iteration 0)
		rfq_row = None
		for row in matrix.data:
			if row.get("stage") == "RFQ Data":
				rfq_row = row
				break

		if rfq_row:
			iter_0_status = rfq_row.get(f"part_{test_item.item_code}_iter_0")
			iter_1_status = rfq_row.get(f"part_{test_item.item_code}_iter_1")
			self.assertEqual(iter_0_status, "Completed", "RFQ Data in iteration 0 should be Completed")
			self.assertEqual(iter_1_status, "Completed", "RFQ Data in iteration 1 should cascade from iteration 0")
