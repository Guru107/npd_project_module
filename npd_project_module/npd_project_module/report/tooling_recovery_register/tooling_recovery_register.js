// Copyright (c) 2026, Guru107 and contributors
// For license information, please see license.txt

frappe.query_reports["Tooling Recovery Register"] = {
	filters: [
		{
			fieldname: "project",
			label: __("Project"),
			fieldtype: "Link",
			options: "Project",
		},
		{
			fieldname: "customer",
			label: __("Customer"),
			fieldtype: "Link",
			options: "Customer",
		},
		{
			fieldname: "supplier",
			label: __("Supplier"),
			fieldtype: "Link",
			options: "Supplier",
		},
		{
			fieldname: "recovery_status",
			label: __("Recovery Status"),
			fieldtype: "Select",
			options: ["", "Not Invoiced", "Pending", "Partially Recovered", "Fully Recovered"],
		},
	],

	formatter: function (value, row, column, data, default_formatter) {
		if (column.fieldname === "recovery_status") {
			const status = value || "";
			let color = "";
			let bg_color = "";
			if (status === "Fully Recovered") {
				color = "#28a745";
				bg_color = "#d4edda";
			} else if (status === "Partially Recovered") {
				color = "#ffc107";
				bg_color = "#fff3cd";
			} else if (status === "Pending") {
				color = "#dc3545";
				bg_color = "#f8d7da";
			} else if (status === "Not Invoiced") {
				color = "#6c757d";
				bg_color = "#e2e3e5";
			} else {
				return default_formatter(value, row, column, data);
			}
			return `<span style="color: ${color}; background-color: ${bg_color}; padding: 4px 8px; border-radius: 4px; font-weight: 500; display: inline-block; min-width: 120px; text-align: center;">${status}</span>`;
		}

		// Highlight ageing over 60 days in red for outstanding recoveries.
		if (
			column.fieldname === "ageing_days" &&
			data &&
			data.recovery_status !== "Fully Recovered" &&
			data.recovery_status !== "Not Invoiced" &&
			flt(value) > 60
		) {
			return `<span style="color: #dc3545; font-weight: 600;">${value}</span>`;
		}

		return default_formatter(value, row, column, data);
	},
};

function flt(v) {
	const n = parseFloat(v);
	return isNaN(n) ? 0 : n;
}
