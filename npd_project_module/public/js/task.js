// Copyright (c) 2025, Guru107 and contributors
// For license information, please see license.txt

frappe.ui.form.on("Task", {
	onload: function (frm) {
		// Set up part_number query to filter Items based on project
		frm.set_query("part_number", function () {
			// In form context, use the project from the form
			if (frm.doc.project) {
				return {
					filters: {
						project: frm.doc.project,
					},
				};
			}
			// If no project selected, show all items (or none)
			return {
				filters: {},
			};
		});
	},

	project: function (frm) {
		// When project changes, update part_number query and validate
		if (frm.doc.part_number) {
			// Clear part_number if it doesn't belong to the new project
			frappe.db.get_value("Item", frm.doc.part_number, "project", function (r) {
				if (r && r.message && r.message.project && r.message.project !== frm.doc.project) {
					frm.set_value("part_number", "");
				}
			});
		}
		// Update part_number query filter
		frm.set_query("part_number", function () {
			if (frm.doc.project) {
				return {
					filters: {
						project: frm.doc.project,
					},
				};
			}
			return {
				filters: {},
			};
		});
	},

	validate: function (frm) {
		// Validate dependencies before allowing status change
		if (
			!frm.doc.part_number ||
			frm.doc.iteration_number === null ||
			frm.doc.iteration_number === undefined
		) {
			return;
		}

		if (frm.is_new()) {
			return;
		}

		// Get old status
		const old_status = frm.doc._doc_before_save ? frm.doc._doc_before_save.status : null;

		// Prevent cancelling RFQ Data (first task)
		if (frm.doc.status === "Cancelled" && old_status && old_status !== "Cancelled") {
			return frappe.call({
				method: "npd_project_module.utils.task_utils.validate_task_cancellation",
				args: {
					task_name: frm.doc.name,
					part_number: frm.doc.part_number,
					subject: frm.doc.subject,
				},
				async: false,
				callback: function (r) {
					if (r.message && !r.message.valid) {
						frappe.throw(r.message.message);
					}
				},
			});
		}

		// Only validate if status is changing to Working or Completed
		if (frm.doc.status && (frm.doc.status === "Working" || frm.doc.status === "Completed")) {
			if (!old_status || (old_status !== "Working" && old_status !== "Completed")) {
				return frappe.call({
					method: "npd_project_module.utils.task_utils.validate_task_dependencies",
					args: {
						task_name: frm.doc.name,
						part_number: frm.doc.part_number,
						iteration_number: frm.doc.iteration_number,
						status: frm.doc.status,
					},
					async: false,
					callback: function (r) {
						if (r.message && !r.message.valid) {
							frappe.throw(r.message.message);
						}
					},
				});
			}
		}
	},

	after_save: function (frm) {
		// Handle automatic cancellation of subsequent tasks
		if (
			!frm.doc.part_number ||
			frm.doc.iteration_number === null ||
			frm.doc.iteration_number === undefined
		) {
			return;
		}

		if (frm.is_new()) {
			return;
		}

		// Skip if this is being inserted during task generation
		if (frappe.flags && frappe.flags.in_task_generation) {
			return;
		}

		// Skip if we're already in a cancellation cascade
		if (frappe.flags && frappe.flags.in_cancellation_cascade) {
			return;
		}

		// Get old status
		const old_status = frm.doc._doc_before_save ? frm.doc._doc_before_save.status : null;

		// If task was cancelled, cancel subsequent tasks
		if (frm.doc.status === "Cancelled" && old_status && old_status !== "Cancelled") {
			frappe.call({
				method: "npd_project_module.utils.task_utils.handle_task_cancellation",
				args: {
					task_name: frm.doc.name,
					part_number: frm.doc.part_number,
					iteration_number: frm.doc.iteration_number,
					project_name: frm.doc.project,
				},
				callback: function (r) {
					if (r.message && r.message.success && r.message.cancelled_count > 0) {
						frappe.show_alert({
							message: r.message.message,
							indicator: "orange",
						});
						// Reload to show updated task statuses
						frm.reload_doc();
					}
				},
			});
		}
	},
});
