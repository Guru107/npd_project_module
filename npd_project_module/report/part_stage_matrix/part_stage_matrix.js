// Copyright (c) 2025, Guru107 and contributors
// For license information, please see license.txt

frappe.query_reports["Part Stage Matrix"] = {
	filters: [
		{
			fieldname: "project",
			label: __("Project"),
			fieldtype: "Link",
			options: "Project",
			reqd: 1,
			get_query: function () {
				return {
					filters: {
						status: ["!=", "Completed"],
					},
				};
			},
		},
		{
			fieldname: "part_number",
			label: __("Part Number (Item)"),
			fieldtype: "MultiSelectList",
			get_data: function (txt) {
				return frappe.db.get_link_options("Item", txt, {
					project: frappe.query_report.get_filter_value("project"),
				});
			},
		},
	],

	onload: function (report) {
		// Set up event listener for project change
		// Note: This might not be needed as MultiSelectList should handle it automatically
	},

	formatter: function (value, row, column, data, default_formatter) {
		// Apply color coding based on status
		if (column.fieldname === "stage") {
			// Stage column - no special formatting
			return default_formatter(value, row, column, data);
		}

		// Status columns - apply color coding
		const status = value || "";
		let color = "";
		let bg_color = "";

		switch (status) {
			case "Completed":
				color = "#28a745"; // Green
				bg_color = "#d4edda";
				break;
			case "In Progress":
			case "Working":
				color = "#ffc107"; // Yellow/Orange
				bg_color = "#fff3cd";
				break;
			case "Cancelled":
			case "Rejected":
				color = "#dc3545"; // Red
				bg_color = "#f8d7da";
				break;
			case "Blocked":
				color = "#6c757d"; // Gray
				bg_color = "#e2e3e5";
				break;
			case "Overdue":
				color = "#dc3545"; // Red
				bg_color = "#f8d7da";
				break;
			case "Not Started":
				color = "#6c757d"; // Gray
				bg_color = "#f8f9fa";
				break;
			case "No Tasks":
				color = "#6c757d"; // Gray
				bg_color = "#f8f9fa";
				break;
			default:
				return default_formatter(value, row, column, data);
		}

		return `<span style="color: ${color}; background-color: ${bg_color}; padding: 4px 8px; border-radius: 4px; font-weight: 500;">${status}</span>`;
	},

	after_datatable_render: function (datatable) {
		// Add click handler for drill-down functionality
		const report = this;
		datatable.wrapper.on("click", "td", function () {
			const $cell = $(this);
			const column = datatable.columns[$cell.index()];
			const row = datatable.rows[$cell.closest("tr").index()];

			// Skip if clicking on stage column
			if (column.fieldname === "stage") {
				return;
			}

			// Get the status value
			const status = $cell.text().trim();
			if (!status || status === "No Tasks") {
				return;
			}

			// Get part number from column fieldname (format: "part_{part_code}")
			const part_code = column.fieldname.replace("part_", "");
			const stage_name = row.stage;

			// Open drill-down dialog
			report.show_task_details(part_code, stage_name, status);
		});
	},

	show_task_details: function (part_code, stage_name, status) {
		// Get project from filters
		const project = frappe.query_report.get_filter_value("project");
		if (!project) {
			return;
		}

		const report = this;

		// Fetch task details for this part and stage
		frappe.call({
			method: "npd_project_module.report.part_stage_matrix.part_stage_matrix.get_task_details",
			args: {
				project: project,
				part_number: part_code,
				stage_name: stage_name,
			},
			callback: function (r) {
				if (r.message) {
					report.display_task_dialog(r.message, part_code, stage_name, status);
				}
			},
		});
	},

	display_task_dialog: function (tasks, part_code, stage_name, status) {
		// Create dialog to show task details
		const dialog = new frappe.ui.Dialog({
			title: __("Task Details: {0} - {1}", [part_code, stage_name]),
			fields: [
				{
					fieldtype: "HTML",
					options: `<div id="task-details-content"></div>`,
				},
			],
		});

		// Build HTML content
		let html = `<div style="padding: 20px;">`;
		html += `<h4>${__("Status")}: <span style="color: #28a745;">${status}</span></h4>`;

		if (tasks && tasks.length > 0) {
			html += `<table class="table table-bordered" style="margin-top: 15px;">`;
			html += `<thead><tr>
				<th>${__("Iteration")}</th>
				<th>${__("Task Name")}</th>
				<th>${__("Status")}</th>
				<th>${__("Actions")}</th>
			</tr></thead>`;
			html += `<tbody>`;

			for (const task of tasks) {
				const iteration = task.iteration_number || 0;
				const task_status = task.status || "Open";
				const task_name = task.name || "";
				const task_subject = task.subject || "";

				html += `<tr>
					<td>${iteration}</td>
					<td>${task_subject}</td>
					<td>${task_status}</td>
					<td><a href="/app/task/${task_name}" target="_blank">${__("Open")}</a></td>
				</tr>`;
			}

			html += `</tbody></table>`;
		} else {
			html += `<p>${__("No tasks found for this stage.")}</p>`;
		}

		html += `</div>`;

		dialog.fields_dict.task_details_content.$wrapper.html(html);
		dialog.show();
	},
};

