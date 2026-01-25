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
			options: "Item",
			get_data: function (txt) {
				return frappe.db.get_link_options("Item", txt, {
					project: frappe.query_report.get_filter_value("project"),
				});
			},
			on_change: function () {
				// Show/hide "Show All Iterations" checkbox based on part selection
				const part_numbers = frappe.query_report.get_filter_value("part_number");
				const show_all_iterations_filter =
					frappe.query_report.get_filter("show_all_iterations");

				if (show_all_iterations_filter) {
					if (part_numbers && part_numbers.length > 0) {
						show_all_iterations_filter.df.hidden = 0;
						show_all_iterations_filter.refresh();
					} else {
						show_all_iterations_filter.df.hidden = 1;
						show_all_iterations_filter.set_value(0);
						show_all_iterations_filter.refresh();
					}
				}
			},
		},
		{
			fieldname: "show_all_iterations",
			label: __("Show All Iterations"),
			fieldtype: "Check",
			default: 0,
			hidden: 1, // Hidden by default, shown when part_number has values
			depends_on:
				"eval:frappe.query_report.get_filter_value('part_number') && frappe.query_report.get_filter_value('part_number').length > 0",
		},
	],

	formatter: function (value, row, column, data, default_formatter) {
		// Apply color coding based on status
		if (column.fieldname === "stage") {
			// Stage column - no special formatting
			return default_formatter(value, row, column, data);
		}

		// Status columns - apply color coding
		const status = value || "";

		// Extract base status from strings like "Completed (Iter 0)" or "Not Started (Iter 1)"
		let baseStatus = status;
		if (status.includes("(")) {
			baseStatus = status.split("(")[0].trim();
		}

		let color = "";
		let bg_color = "";

		// Determine color based on base status (keeping original color scheme)
		if (baseStatus === "Completed") {
			color = "#28a745"; // Green
			bg_color = "#d4edda";
		} else if (baseStatus === "In Progress" || baseStatus === "Working") {
			color = "#ffc107"; // Yellow/Orange
			bg_color = "#fff3cd";
		} else if (baseStatus === "Cancelled" || baseStatus === "Rejected") {
			color = "#dc3545"; // Red
			bg_color = "#f8d7da";
		} else if (baseStatus === "Blocked") {
			color = "#6c757d"; // Gray
			bg_color = "#e2e3e5";
		} else if (baseStatus === "Overdue") {
			color = "#dc3545"; // Red
			bg_color = "#f8d7da";
		} else if (baseStatus === "Not Started") {
			color = "#6c757d"; // Gray
			bg_color = "#f8f9fa";
		} else if (baseStatus === "No Tasks") {
			color = "#6c757d"; // Gray
			bg_color = "#f8f9fa";
		} else {
			// Unknown status - use default formatting
			return default_formatter(value, row, column, data);
		}

		// Apply background color to the cell with padding and border radius
		return `<span style="color: ${color}; background-color: ${bg_color}; padding: 4px 8px; border-radius: 4px; font-weight: 500; display: inline-block; min-width: 100px; text-align: center;">${status}</span>`;
	},
};
