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
		},
	],

	onload: function (report) {
		// Set up event listener for project change
		// Note: This might not be needed as MultiSelectList should handle it automatically
		console.log("report onload");
		console.log("report", report);
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

		// In Frappe v16, use the report container element for event delegation
		// The datatable is rendered inside frappe.query_report.$report
		console.log("after_datatable_render");

		console.log(datatable.options.onClick);
	},
};
