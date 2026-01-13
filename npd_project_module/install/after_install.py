# Copyright (c) 2025, Guru107 and contributors
# For license information, please see license.txt

import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields


def after_install():
	"""
	Setup custom fields and configurations after app installation.
	This function is idempotent - it checks for existing resources before creating.
	"""
	create_task_custom_fields()
	create_project_custom_fields()
	create_item_custom_fields()
	create_npd_template()
	frappe.db.commit()
	print("NPD Project Module: Custom fields and configurations created successfully")


def create_task_custom_fields():
	"""
	Create custom fields for Task doctype to support part-based iteration management.
	"""
	custom_fields = {
		"Task": [
			{
				"fieldname": "part_number",
				"label": "Part Number",
				"fieldtype": "Link",
				"options": "Item",
				"insert_after": "project",
				"in_list_view": 1,
				"in_standard_filter": 1,
				"in_global_search": 1,
				"translatable": 0,
				"description": "Item (part) associated with this task",
			},
			{
				"fieldname": "iteration_number",
				"label": "Iteration Number",
				"fieldtype": "Int",
				"insert_after": "part_number",
				"in_list_view": 1,
				"in_standard_filter": 1,
				"read_only": 1,
				"default": "0",
				"non_negative": 1,
				"description": "Iteration number for this task (system-managed)",
			},
			{
				"fieldname": "stage_type",
				"label": "Stage Type",
				"fieldtype": "Data",
				"insert_after": "iteration_number",
				"in_list_view": 1,
				"in_standard_filter": 1,
				"read_only": 1,
				"translatable": 0,
				"description": "Stage name from NPD Template (e.g., 'RFQ Data', 'Comparison of TKO & RFQ Data'). Used to classify tasks by stage type.",
			},
		]
	}

	# Create custom fields (function is idempotent - checks for existing fields)
	create_custom_fields(custom_fields, update=True)
	print("  ✓ Custom fields for Task doctype created")


def create_project_custom_fields():
	"""
	Create child table field in Project doctype for Part Numbers.
	"""
	custom_fields = {
		"Project": [
			{
				"fieldname": "part_numbers_section",
				"label": "Part Numbers",
				"fieldtype": "Section Break",
				"insert_after": "project_template",
				"collapsible": 0,
			},
			{
				"fieldname": "part_numbers",
				"label": "Part Numbers",
				"fieldtype": "Table",
				"insert_after": "part_numbers_section",
				"options": "Project Part Number",
				"description": "Add part numbers to track multiple parts in this project",
			},
		]
	}

	# Create custom fields (function is idempotent - checks for existing fields)
	create_custom_fields(custom_fields, update=True)
	print("  ✓ Child table field for Project doctype created")


def create_item_custom_fields():
	"""
	Create custom field in Item doctype to link items to projects.
	"""
	custom_fields = {
		"Item": [
			{
				"fieldname": "project",
				"label": "Project",
				"fieldtype": "Link",
				"options": "Project",
				"insert_after": "is_fixed_asset",
				"in_list_view": 1,
				"in_standard_filter": 1,
				"in_global_search": 1,
				"translatable": 0,
				"description": "Project this item (part) belongs to",
			}
		]
	}

	# Create custom fields (function is idempotent - checks for existing fields)
	create_custom_fields(custom_fields, update=True)
	print("  ✓ Custom field for Item doctype created")


def hsl_to_rgb(h, s, l):
	"""
	Convert HSL (Hue, Saturation, Lightness) color space to RGB.

	Args:
		h (float): Hue in range [0, 1]
		s (float): Saturation in range [0, 1]
		l (float): Lightness in range [0, 1]

	Returns:
		tuple: (R, G, B) values in range [0, 1]
	"""
	if s == 0:
		# Achromatic (gray)
		return (l, l, l)

	def hue_to_rgb(p, q, t):
		if t < 0:
			t += 1
		if t > 1:
			t -= 1
		if t < 1 / 6:
			return p + (q - p) * 6 * t
		if t < 1 / 2:
			return q
		if t < 2 / 3:
			return p + (q - p) * (2 / 3 - t) * 6
		return p

	q = l * (1 + s) if l < 0.5 else l + s - l * s
	p = 2 * l - q
	r = hue_to_rgb(p, q, h + 1 / 3)
	g = hue_to_rgb(p, q, h)
	b = hue_to_rgb(p, q, h - 1 / 3)

	return (r, g, b)


def generate_unique_colors(count, saturation=0.75, lightness=0.5):
	"""
	Generate a set of unique, visually distinct colors using HSL color space.

	This function implements a color generation algorithm based on graph coloring principles:
	1. Distributes colors evenly across the hue spectrum (0-360 degrees)
	2. Uses optimal saturation and lightness values for visibility
	3. Ensures maximum perceptual distance between adjacent colors
	4. For many colors, uses golden ratio spacing for better distribution

	Args:
		count (int): Number of colors to generate
		saturation (float): Color saturation (0.0-1.0), default 0.75 for vibrant colors
		lightness (float): Color lightness (0.0-1.0), default 0.5 for balanced contrast

	Returns:
		list: List of hex color codes (e.g., ["#FF6B6B", "#4ECDC4", ...])
	"""
	if count <= 0:
		return []

	colors = []

	if count <= 20:
		# For up to 20 colors, use evenly distributed hues
		# This ensures maximum visual distinction with predictable spacing
		# 360 degrees / count gives optimal hue spacing
		hue_step = 360.0 / count
		for i in range(count):
			hue = (i * hue_step) % 360.0
			# Convert HSL to RGB, then to hex
			rgb = hsl_to_rgb(hue / 360.0, saturation, lightness)
			hex_color = "#{:02X}{:02X}{:02X}".format(int(rgb[0] * 255), int(rgb[1] * 255), int(rgb[2] * 255))
			colors.append(hex_color)
	else:
		# For more colors, use golden ratio spacing for optimal distribution
		# Golden ratio: φ = (1 + √5) / 2 ≈ 0.618 when used multiplicatively
		golden_ratio = 0.618033988749895
		for i in range(count):
			# Use golden ratio to create evenly distributed, non-repeating hues
			hue = (i * golden_ratio * 360.0) % 360.0

			# Vary saturation and lightness slightly for better distinction with many colors
			# This creates a more diverse and visually appealing palette
			variant_saturation = saturation if i % 2 == 0 else saturation * 0.85
			# Vary lightness in three levels for maximum distinction
			if i % 3 == 0:
				variant_lightness = lightness
			elif i % 3 == 1:
				variant_lightness = max(0.35, lightness * 0.85)  # Darker
			else:
				variant_lightness = min(0.65, lightness * 1.15)  # Lighter

			# Convert HSL to RGB, then to hex
			rgb = hsl_to_rgb(hue / 360.0, variant_saturation, variant_lightness)
			hex_color = "#{:02X}{:02X}{:02X}".format(int(rgb[0] * 255), int(rgb[1] * 255), int(rgb[2] * 255))
			colors.append(hex_color)

	return colors


def create_npd_template():
	"""
	Create default NPD Project Template with 18 tasks.
	This template will be used to fetch the task sequence for new projects.
	Each task is assigned a unique color for visual distinction.
	"""
	template_name = "NPD Template"

	# List of 18 tasks in sequential order for New Part Development Process
	task_names = [
		"RFQ Data",
		"Internal Team Technical Feasibility",
		"Supplier Quote & Tooling Sequence",
		"Technical Sign Off",
		"Commercial with M&M",
		"VOB or LOBA",
		"TKO Data",
		"Comparison of TKO & RFQ Data",
		"Commercial with Supplier",
		"Time Plan",
		"Design Approval Process",
		"Buy Off",
		"HLTO",
		"IPTR",
		"PPAP",
		"JPTR",
		"APQP",
		"Handover to Production",
	]

	# Generate unique colors using HSL color space algorithm
	# This ensures maximum visual distinction between tasks
	# Using saturation=0.75 and lightness=0.5 for vibrant, professional colors
	task_colors = generate_unique_colors(len(task_names), saturation=0.75, lightness=0.5)

	# Check if template already exists and handle accordingly
	needs_update = False
	template_exists = frappe.db.exists("Project Template", template_name)
	existing_template_tasks_map = {}

	if template_exists:
		template = frappe.get_doc("Project Template", template_name)
		if template.tasks and len(template.tasks) == len(task_names):
			# Template exists with correct number of tasks
			# Create a map of existing tasks by subject for quick lookup
			for template_task_row in template.tasks:
				if template_task_row.task:
					task_doc = frappe.get_doc("Task", template_task_row.task)
					existing_template_tasks_map[task_doc.subject] = template_task_row.task
		else:
			# Template exists but needs updating (wrong number of tasks)
			needs_update = True

	# Create template Task documents (these are just templates, not real tasks)
	# We need to create them in sequence and add dependencies
	template_tasks = []
	previous_task_name = None

	for index, task_name in enumerate(task_names):
		# Get unique color for this task
		task_color = task_colors[index] if index < len(task_colors) else "#808080"  # Default gray if missing

		# Check if this task already exists in the template (if template exists)
		existing_task_name = None
		if task_name in existing_template_tasks_map:
			existing_task_name = existing_template_tasks_map[task_name]
		else:
			# Check if template task already exists by subject (without project)
			existing_tasks = frappe.get_all(
				"Task", filters={"subject": task_name, "project": ["is", "not set"]}, fields=["name"], limit=1
			)
			if existing_tasks:
				existing_task_name = existing_tasks[0].name

		if existing_task_name:
			# Task already exists - update it to ensure correct color and dependencies
			template_tasks.append(existing_task_name)

			# Ensure existing template task has is_template set and reset dependencies to sequential order
			existing_task_doc = frappe.get_doc("Task", existing_task_name)
			needs_save = False

			# Set is_template and status if not already set
			if not existing_task_doc.is_template:
				existing_task_doc.is_template = 1
				needs_save = True
			# Ensure status is "Template" for template tasks
			if existing_task_doc.is_template and existing_task_doc.status != "Template":
				existing_task_doc.status = "Template"
				needs_save = True
			# Assign unique color to this task
			if existing_task_doc.color != task_color:
				existing_task_doc.color = task_color
				needs_save = True

			# Reset dependencies to only have the sequential dependency
			# This ensures all dependencies are in the template_tasks list
			if previous_task_name:
				# Clear existing dependencies and set only the sequential one
				existing_task_doc.depends_on = []
				existing_task_doc.append("depends_on", {"task": previous_task_name})
				needs_save = True
			else:
				# First task should have no dependencies
				if existing_task_doc.depends_on:
					existing_task_doc.depends_on = []
					needs_save = True

			# Save once if any changes were made
			if needs_save:
				existing_task_doc.save(ignore_permissions=True)
				frappe.db.commit()

			previous_task_name = existing_task_name
		else:
			# Create new template task
			template_task = frappe.get_doc(
				{
					"doctype": "Task",
					"subject": task_name,
					"status": "Template",
					"is_group": 0,
					"is_template": 1,
					"color": task_color,  # Assign unique color to each task
				}
			)

			# Add dependency on previous task if it exists
			if previous_task_name:
				template_task.append("depends_on", {"task": previous_task_name})

			template_task.insert(ignore_permissions=True)
			frappe.db.commit()
			template_tasks.append(template_task.name)
			previous_task_name = template_task.name

	# Create or update Project Template
	template_needs_save = False
	if frappe.db.exists("Project Template", template_name):
		template = frappe.get_doc("Project Template", template_name)
		# Clear existing tasks if we're updating (to avoid duplication)
		if needs_update:
			template.tasks = []
			template_needs_save = True
			# Add tasks to template in sequence (only if we cleared them)
			for task_name in template_tasks:
				template.append("tasks", {"task": task_name})
		else:
			# Template exists with correct number of tasks
			# We've already updated task colors/dependencies in the loop above
			# Verify tasks are in correct order and match expected sequence
			current_task_ids = [row.task for row in template.tasks] if template.tasks else []
			if current_task_ids != template_tasks:
				# Tasks are out of order or don't match expected sequence, need to reorder
				template.tasks = []
				for task_id in template_tasks:
					template.append("tasks", {"task": task_id})
				template_needs_save = True
	else:
		# Create new Project Template with name "NPD Template"
		template = frappe.get_doc(
			{
				"doctype": "Project Template",
				"name": template_name,  # "NPD Template"
				"project_type": None,  # Can be set later if needed
				"disabled": 0,
			}
		)
		# Explicitly set the name for doctypes with autoname "Prompt"
		template.name = template_name

		# Add tasks to template in sequence
		for task_name in template_tasks:
			template.append("tasks", {"task": task_name})
		template_needs_save = True

	# Save template if needed
	if template_needs_save:
		if frappe.db.exists("Project Template", template_name):
			template.save(ignore_permissions=True)
		else:
			template.insert(ignore_permissions=True)
		frappe.db.commit()

	print(f"  ✓ Created/Updated NPD Template with {len(task_names)} tasks")
