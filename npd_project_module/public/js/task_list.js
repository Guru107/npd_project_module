// Copyright (c) 2025, Guru107 and contributors
// For license information, please see license.txt

/**
 * Client-side script to extend Task list view functionality.
 * Extends ERPNext's Task listview_settings with NPD Project Module features.
 *
 * Features:
 * - Adds part_number and iteration_number fields to list view
 * - Hides cancelled tasks by default (status != Cancelled)
 * - Adds menu items to show/hide cancelled tasks
 * - Preserves all ERPNext functionality (bulk status updates, indicators, Gantt popup)
 */

// Store original ERPNext settings if they exist
const original_settings = frappe.listview_settings["Task"] || {};

// Extend ERPNext's Task listview_settings
frappe.listview_settings["Task"] = {
	// Add NPD-specific fields to the fields list
	add_fields: [
		...(original_settings.add_fields || [
			"project",
			"status",
			"priority",
			"exp_start_date",
			"exp_end_date",
			"subject",
			"progress",
			"depends_on_tasks",
		]),
		"part_number",
		"iteration_number",
	],

	// Default filter: Hide cancelled tasks (instead of ERPNext's "status = Open")
	filters: [["status", "!=", "Cancelled"]],

	// Extend onload to add NPD-specific menu items while preserving ERPNext functionality
	onload: function (listview) {
		// Call original ERPNext onload if it exists
		if (original_settings.onload) {
			original_settings.onload.call(this, listview);
		}

		// Add NPD-specific menu items
		// Only add if not already added (check for existing menu items)
		if (!listview._npd_menu_items_added) {
			// Add menu item to show cancelled tasks
			listview.page.add_menu_item(__("Show Cancelled Tasks"), function () {
				// Show only cancelled tasks by setting status = Cancelled filter
				// First, remove any existing status filters
				console.log("Show Cancelled Tasks");
				const filters = listview.filter_area.get();
				console.log("filters", filters);
				const new_filters = filters.filter((f) => {
					return !f.includes("status");
				});
				new_filters.push(["Task", "status", "in", ["Cancelled,"], false]);
				listview.filter_area
					.clear(false)
					.then(function () {
						return listview.filter_area.set(new_filters);
					})
					.then(function () {
						listview.refresh();
					});
			});

			// Add menu item to hide cancelled tasks (restore default)
			listview.page.add_menu_item(__("Hide Cancelled Tasks"), function () {
				// Hide cancelled tasks by setting status != Cancelled filter
				// First, remove any existing status filters
				console.log("Hide Cancelled Tasks");
				const filters = listview.filter_area.get();
				console.log("filters", filters);
				const new_filters = filters.filter((f) => {
					console.log("f", f);
					return !f.includes("status");
				});
				new_filters.push(["Task", "status", "not in", ["Cancelled,"], false]);
				console.log("new_filters", new_filters);
				listview.filter_area
					.clear(false)
					.then(function () {
						return listview.filter_area.set(new_filters);
					})
					.then(function () {
						listview.refresh();
					});
			});

			// Add quick filter menu items
			// Quick filter: All Open tasks (includes Overdue)
			listview.page.add_menu_item(__("All Open Tasks"), function () {
				// Clear existing filters first, then set the new status filter
				// Use "in" operator to include both "Open" and "Overdue" statuses
				// Format: [doctype, field, operator, value]
				let existing_filters = listview.filter_area.get();
				let new_filters = existing_filters.filter((f) => !f.includes("status"));
				new_filters.push(["Task", "status", "in", ["Open", "Overdue"]]);
				listview.filter_area
					.clear(false)
					.then(function () {
						return listview.filter_area.set(new_filters);
					})
					.then(function () {
						listview.refresh();
					});
			});

			// Quick filter: All Working tasks
			listview.page.add_menu_item(__("All Working Tasks"), function () {
				// Clear existing filters first, then set the new status filter
				// Use 4-element format: [doctype, field, operator, value]
				let existing_filters = listview.filter_area.get();
				let new_filters = existing_filters.filter((f) => !f.includes("status"));
				new_filters.push(["Task", "status", "=", "Working"]);
				listview.filter_area
					.clear(false)
					.then(function () {
						return listview.filter_area.set(new_filters);
					})
					.then(function () {
						listview.refresh();
					});
			});

			// Quick filter: All Completed tasks
			listview.page.add_menu_item(__("All Completed Tasks"), function () {
				// Clear existing filters first, then set the new status filter
				// Use 4-element format: [doctype, field, operator, value]
				let existing_filters = listview.filter_area.get();
				let new_filters = existing_filters.filter((f) => !f.includes("status"));
				new_filters.push(["Task", "status", "=", "Completed"]);
				listview.filter_area
					.clear(false)
					.then(function () {
						return listview.filter_area.set(new_filters);
					})
					.then(function () {
						listview.refresh();
					});
			});

			listview.page.add_menu_item(__("All Overdue Tasks"), function () {
				// Clear existing filters first, then set the new status filter
				// Use 4-element format: [doctype, field, operator, value]
				let existing_filters = listview.filter_area.get();
				let new_filters = existing_filters.filter((f) => !f.includes("status"));
				new_filters.push(["Task", "status", "=", "Overdue"]);
				listview.filter_area
					.clear(false)
					.then(function () {
						return listview.filter_area.set(new_filters);
					})
					.then(function () {
						listview.refresh();
					});
			});

			listview._npd_menu_items_added = true;
		}
	},

	// Extend get_indicator to preserve ERPNext colors and add iteration info
	get_indicator: function (doc) {
		// Use original ERPNext indicator if available
		if (original_settings.get_indicator) {
			const indicator = original_settings.get_indicator.call(this, doc);
			// Enhance indicator with iteration info if available
			if (
				doc.iteration_number !== undefined &&
				doc.iteration_number !== null &&
				doc.iteration_number > 0
			) {
				// Add iteration number to the indicator label
				return [
					indicator[0] + ` (Iteration ${doc.iteration_number})`,
					indicator[1],
					indicator[2],
				];
			}
			return indicator;
		}

		// Fallback to default colors if original not available
		var colors = {
			Open: "orange",
			Overdue: "red",
			"Pending Review": "orange",
			Working: "orange",
			Completed: "green",
			Cancelled: "dark grey",
			Template: "blue",
		};
		var status_label = __(doc.status);
		if (
			doc.iteration_number !== undefined &&
			doc.iteration_number !== null &&
			doc.iteration_number > 0
		) {
			status_label += ` (Iteration ${doc.iteration_number})`;
		}
		return [status_label, colors[doc.status] || "grey", "status,=," + doc.status];
	},

	// Enhance documents before rendering to check blocked status
	before_render: function () {
		// Call original before_render if it exists
		if (original_settings.before_render) {
			original_settings.before_render.call(this);
		}

		// Check blocked status for tasks with dependencies (only once per page load)
		// Use 'this' instead of 'listview' parameter since before_render is called with 'this' context
		const listview = this;

		// Ensure data exists and is an array before accessing
		if (
			listview &&
			listview.data &&
			Array.isArray(listview.data) &&
			listview.data.length > 0 &&
			!listview._blocked_status_checked
		) {
			const tasks_with_deps = listview.data.filter(
				(doc) =>
					doc &&
					doc.depends_on_tasks &&
					doc.depends_on_tasks.length > 0 &&
					doc.status !== "Completed" &&
					doc.status !== "Cancelled" &&
					doc.part_number &&
					doc.iteration_number !== undefined
			);

			if (tasks_with_deps.length > 0) {
				const task_names = tasks_with_deps.map((doc) => doc.name).filter((name) => name);
				if (task_names.length > 0) {
					frappe.call({
						method: "npd_project_module.utils.task_utils.check_task_blocked_status",
						args: {
							task_names: task_names,
						},
						callback: function (r) {
							if (r.message && listview.data) {
								// Store blocked status in document
								listview.data.forEach((doc) => {
									if (doc && doc.name && r.message[doc.name]) {
										doc._is_blocked = true;
									}
								});
								listview._blocked_status_checked = true;
								// Refresh the list to show indicators
								if (listview.render) {
									listview.render();
								}
							}
						},
					});
				} else {
					listview._blocked_status_checked = true;
				}
			} else {
				listview._blocked_status_checked = true;
			}
		}
	},

	// Add formatter to show visual indicators for blocked tasks
	formatters: {
		...original_settings.formatters,
		subject: function (value, doc) {
			// Show blocked indicator if task has unmet dependencies
			if (doc._is_blocked) {
				return (
					value +
					' <span class="text-danger" title="Blocked: Dependencies not met">🔒</span>'
				);
			}
			if (
				doc.depends_on_tasks &&
				doc.depends_on_tasks.length > 0 &&
				doc.status !== "Completed" &&
				doc.status !== "Cancelled"
			) {
				return value + ' <span class="text-muted" title="Has dependencies">🔗</span>';
			}
			return value;
		},
		status: function (value, doc) {
			// Add visual indicator for blocked tasks
			if (doc._is_blocked) {
				return (
					value +
					' <span class="text-danger" title="Blocked: Dependencies not met">⚠️</span>'
				);
			}
			return value;
		},
	},

	// Preserve ERPNext's Gantt custom popup
	gantt_custom_popup_html:
		original_settings.gantt_custom_popup_html ||
		function (ganttobj, task) {
			let html = `
			<a class="text-white mb-2 inline-block cursor-pointer"
				href="/app/task/${ganttobj.id}">
				${ganttobj.name}
			</a>
		`;

			if (task.project) {
				html += `<p class="mb-1">${__("Project")}:
				<a class="text-white inline-block"
					href="/app/project/${task.project}">
					${task.project}
				</a>
			</p>`;
			}

			// Add part number and iteration info if available
			if (task.part_number) {
				html += `<p class="mb-1">${__("Part Number")}:
				<span class="text-white">${task.part_number}</span>
			</p>`;
			}
			if (task.iteration_number !== undefined && task.iteration_number !== null) {
				html += `<p class="mb-1">${__("Iteration")}:
				<span class="text-white">${task.iteration_number}</span>
			</p>`;
			}

			html += `<p class="mb-1">
			${__("Progress")}:
			<span class="text-white">${ganttobj.progress}%</span>
		</p>`;

			if (task._assign) {
				const assign_list = JSON.parse(task._assign);
				const assignment_wrapper = `
				<span>Assigned to:</span>
				<span class="text-white">
					${assign_list.map((user) => frappe.user_info(user).fullname).join(", ")}
				</span>
			`;
				html += assignment_wrapper;
			}

			return `<div class="p-3" style="min-width: 220px">${html}</div>`;
		},
};
