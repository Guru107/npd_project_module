# Copyright (c) 2025, Guru107 and contributors
# For license information, please see license.txt

"""
Test utilities and fixtures for NPD Project Module tests.
"""

import frappe
from frappe.utils import nowdate

from npd_project_module.tests.compat import IntegrationTestCase


def ensure_test_fixtures():
	"""
	Ensure required test fixtures exist for creating Items and Projects.
	Creates Item Group, UOM, and Company if they don't exist.
	"""
	# Ensure root Item Group "All Item Groups" exists first
	if not frappe.db.exists("Item Group", "All Item Groups"):
		root_item_group = frappe.get_doc(
			{
				"doctype": "Item Group",
				"item_group_name": "All Item Groups",
				"is_group": 1,
			}
		)
		root_item_group.insert(ignore_permissions=True)

	# Ensure Item Group "Products" exists
	if not frappe.db.exists("Item Group", "Products"):
		item_group = frappe.get_doc(
			{
				"doctype": "Item Group",
				"item_group_name": "Products",
				"parent_item_group": "All Item Groups",
				"is_group": 0,
			}
		)
		item_group.insert(ignore_permissions=True)

	# Ensure UOM "Nos" exists
	if not frappe.db.exists("UOM", "Nos"):
		uom = frappe.get_doc(
			{
				"doctype": "UOM",
				"uom_name": "Nos",
			}
		)
		uom.insert(ignore_permissions=True)

	# Ensure "_Test Company" exists
	if not frappe.db.exists("Company", "_Test Company"):
		company = frappe.get_doc(
			{
				"doctype": "Company",
				"company_name": "_Test Company",
				"abbr": "_TC",
				"country": "India",
				"default_currency": "INR",
			}
		)
		company.insert(ignore_permissions=True)

	# add warehouse type "Transit"
	if not frappe.db.exists("Warehouse Type", "Transit"):
		warehouse_type = frappe.get_doc({
			"doctype": "Warehouse Type",
			"name": "Transit"
		})
		warehouse_type.insert(ignore_permissions=True)
		# add warehouse "All Warehouses"
	if not frappe.db.exists("Warehouse", "All Warehouses"):
		warehouse = frappe.get_doc({
			"doctype": "Warehouse",
			"warehouse_name": "All Warehouses",
			"is_group": 1,
		})
		warehouse.insert(ignore_permissions=True)

	# add warehouse "Stores"
	if not frappe.db.exists("Warehouse", "Stores"):
		warehouse = frappe.get_doc({
			"doctype": "Warehouse",
			"warehouse_name": "Stores",
			"parent_warehouse": "All Warehouses",
		})
		warehouse.insert(ignore_permissions=True)

	# add warehouse "Work In Progress"
	if not frappe.db.exists("Warehouse", "Work In Progress"):
		warehouse = frappe.get_doc({
			"doctype": "Warehouse",
			"warehouse_name": "Work In Progress",
			"parent_warehouse": "All Warehouses",
		})
		warehouse.insert(ignore_permissions=True)

	# add warehouse "Finished Goods"
	if not frappe.db.exists("Warehouse", "Finished Goods"):
		warehouse = frappe.get_doc({
			"doctype": "Warehouse",
			"warehouse_name": "Finished Goods",
			"parent_warehouse": "All Warehouses",
		})
		warehouse.insert(ignore_permissions=True)

	# add warehouse "Goods In Transit"
	if not frappe.db.exists("Warehouse", "Goods In Transit"):
		warehouse = frappe.get_doc({
			"doctype": "Warehouse",
			"warehouse_name": "Goods In Transit",
			"warehouse_type": "Transit",
			"parent_warehouse": "All Warehouses",
		})
		warehouse.insert(ignore_permissions=True)


	frappe.db.commit()


def make_test_item(item_code, item_name=None, **kwargs):
	"""
	Create a test Item (part) for testing.

	Args:
		item_code (str): Item code
		item_name (str, optional): Item name
		**kwargs: Additional fields for Item

	Returns:
		Item: Created Item document
	"""
	if frappe.db.exists("Item", item_code):
		return frappe.get_doc("Item", item_code)

	# Ensure required fixtures exist
	ensure_test_fixtures()

	item_data = {
		"doctype": "Item",
		"item_code": item_code,
		"item_name": item_code,
		"item_group": kwargs.get("item_group", "Products"),
		"stock_uom": kwargs.get("stock_uom", "Nos"),
		"is_stock_item": kwargs.get("is_stock_item", 0),
		"include_item_in_manufacturing": kwargs.get("include_item_in_manufacturing", 0),
	}

	# Override with any provided kwargs
	item_data.update(kwargs)

	item = frappe.get_doc(item_data)
	item.insert(ignore_permissions=True)
	frappe.db.commit()

	return item


def make_test_project(project_name, **kwargs):
	"""
	Create a test Project for testing.

	Args:
		project_name (str): Project name
		**kwargs: Additional fields for Project

	Returns:
		Project: Created Project document
	"""
	# Check if project exists by project_name field
	existing = frappe.get_all("Project", filters={"project_name": project_name}, fields=["name"])
	if existing:
		return frappe.get_doc("Project", existing[0]["name"])

	# Ensure required fixtures exist
	ensure_test_fixtures()

	project_data = {
		"doctype": "Project",
		"project_name": project_name,
		"status": kwargs.get("status", "Open"),
		"expected_start_date": kwargs.get("expected_start_date", nowdate()),
		"company": kwargs.get("company", "_Test Company"),
	}

	project_data.update(kwargs)

	project = frappe.get_doc(project_data)
	project.insert(ignore_permissions=True)
	frappe.db.commit()

	return project


def make_test_project_with_parts(project_name, part_numbers, **kwargs):
	"""
	Create a test Project with parts added to Part Numbers table.

	Args:
		project_name (str): Project name
		part_numbers (list): List of item codes to add as parts
		**kwargs: Additional fields for Project

	Returns:
		Project: Created Project document with parts added
	"""
	project = make_test_project(project_name, **kwargs)

	# Add parts to project
	for part_number in part_numbers:
		# Ensure item exists
		if not frappe.db.exists("Item", part_number):
			make_test_item(part_number)

		project.append("part_numbers", {"part_number": part_number, "iteration_number": 0})

	project.save(ignore_permissions=True)
	frappe.db.commit()

	return project


def make_test_task(subject, project=None, part_number=None, iteration_number=0, **kwargs):
	"""
	Create a test Task for testing.

	Args:
		subject (str): Task subject
		project (str, optional): Project name
		part_number (str, optional): Part number (Item code)
		iteration_number (int, optional): Iteration number
		**kwargs: Additional fields for Task

	Returns:
		Task: Created Task document
	"""
	if frappe.db.exists("Task", {"subject": subject, "project": project}):
		tasks = frappe.get_all("Task", filters={"subject": subject, "project": project}, limit=1)
		if tasks:
			return frappe.get_doc("Task", tasks[0]["name"])

	task_data = {
		"doctype": "Task",
		"subject": subject,
		"status": kwargs.get("status", "Open"),
		"project": project,
		"part_number": part_number,
		"iteration_number": iteration_number,
		"is_group": kwargs.get("is_group", 0),
	}

	task_data.update(kwargs)

	task = frappe.get_doc(task_data)
	task.insert(ignore_permissions=True)
	frappe.db.commit()

	return task


def cleanup_test_data(project_name=None, item_codes=None):
	"""
	Clean up test data created during tests.

	Args:
		project_name (str, optional): Project name to delete
		item_codes (list, optional): List of item codes to delete
	"""
	if project_name:
		# Get project document name first
		project_doc_name = None
		try:
			# In Frappe v15/v16, get_doc doesn't accept dict filters directly
			# Need to get the name first using get_all or get_value
			project_docs = frappe.get_all(
				"Project", filters={"project_name": project_name}, fields=["name"], limit=1
			)
			if project_docs:
				project_doc_name = project_docs[0]["name"]
		except Exception:
			pass

		# Delete all tasks for the project
		if project_doc_name:
			tasks = frappe.get_all("Task", filters={"project": project_doc_name}, fields=["name"])
			for task in tasks:
				try:
					frappe.delete_doc("Task", task.name, force=True, ignore_permissions=True)
				except Exception:
					pass

		# Delete project
		if project_doc_name:
			try:
				frappe.delete_doc("Project", project_doc_name, force=True, ignore_permissions=True)
			except Exception:
				pass

	if item_codes:
		for item_code in item_codes:
			try:
				if frappe.db.exists("Item", item_code):
					# Clear project field first
					frappe.db.set_value("Item", item_code, "project", None)
					frappe.delete_doc("Item", item_code, force=True, ignore_permissions=True)
			except Exception:
				pass

	frappe.db.commit()


class NPDProjectModuleTestSuite(IntegrationTestCase):
	"""
	Base test suite for NPD Project Module tests.
	Provides common setup and utilities.
	"""

	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		# Ensure NPD Template exists
		cls.ensure_npd_template()

	@classmethod
	def tearDownClass(cls):
		super().tearDownClass()

	@classmethod
	def ensure_npd_template(cls):
		"""Ensure NPD Template exists for tests."""
		from npd_project_module.install.after_install import create_npd_template

		if not frappe.db.exists("Project Template", "NPD Template"):
			create_npd_template()
			frappe.db.commit()

	def setUp(self):
		"""Set up test fixtures before each test."""
		super().setUp()
		self.test_items = []
		self.test_projects = []

	def tearDown(self):
		"""Clean up test data after each test."""
		# Clean up projects
		for project_name in self.test_projects:
			cleanup_test_data(project_name=project_name)

		# Clean up items
		item_codes = [item.item_code for item in self.test_items]
		cleanup_test_data(item_codes=item_codes)

		super().tearDown()
