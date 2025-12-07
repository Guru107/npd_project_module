// Copyright (c) 2025, Guru107 and contributors
// For license information, please see license.txt

frappe.ui.form.on("Project", {
	validate: function (frm) {
		// Validate that items don't already belong to another project
		if (!frm.doc.part_numbers || frm.doc.part_numbers.length === 0) {
			return;
		}

		const part_numbers = frm.doc.part_numbers.map((row) => row.part_number).filter(Boolean);

		if (part_numbers.length === 0) {
			return;
		}

		return frappe.call({
			method: "npd_project_module.utils.project_utils.validate_project_parts",
			args: {
				project_name: frm.doc.name || "New Project",
				part_numbers: part_numbers,
			},
			async: false,
			callback: function (r) {
				if (r.message && !r.message.valid) {
					frappe.throw(r.message.message);
				}
			},
		});
	},

	after_save: function (frm) {
		// Handle task generation and project assignment
		if (!frm.doc.part_numbers || frm.doc.part_numbers.length === 0) {
			return;
		}

		// Map part_numbers child table to array of objects
		// Handle both object rows and potential edge cases
		const part_numbers_data = frm.doc.part_numbers
			.map((row) => {
				// Ensure row is an object
				if (typeof row !== "object" || row === null) {
					return null;
				}
				// Extract part_number - handle both direct property and potential string values
				const part_number =
					typeof row.part_number === "string"
						? row.part_number
						: row.part_number || null;
				if (!part_number) {
					return null;
				}
				return {
					part_number: part_number,
					iteration_number:
						typeof row.iteration_number === "number"
							? row.iteration_number
							: parseInt(row.iteration_number) || 0,
				};
			})
			.filter((row) => row !== null && row.part_number);

		if (part_numbers_data.length === 0) {
			return;
		}

		// Check if this is a new document
		// After save, __islocal should be false, but we can also check if name was just assigned
		const is_new = frm.doc.__islocal || !frm.doc.name || frm.is_new();

		frappe.call({
			method: "npd_project_module.utils.project_utils.handle_project_save",
			args: {
				project_name: frm.doc.name,
				part_numbers_data: part_numbers_data,
				is_new: is_new,
			},
			callback: function (r) {
				if (r.message && r.message.success) {
					if (r.message.message) {
						frappe.show_alert({
							message: r.message.message,
							indicator: "green",
						});
					}
					// Reload to show updated iteration numbers
					frm.reload_doc();
				} else if (r.message && !r.message.success) {
					frappe.msgprint({
						message: r.message.message || __("Error saving project"),
						indicator: "red",
					});
				}
			},
		});
	},

	onload: function (frm) {
		// Store original on_trash if it exists
		if (!frm._npd_original_on_trash) {
			frm._npd_original_on_trash = frm.on_trash;
		}
	},

	refresh: function (frm) {
		// Only show button for saved documents with parts
		try {
			if (!frm || !frm.doc || typeof frm.is_new !== "function") {
				return;
			}

			if (frm.is_new()) {
				return;
			}

			let part_numbers = frm.doc.part_numbers;
			if (part_numbers) {
				if (!Array.isArray(part_numbers) && part_numbers.length !== undefined) {
					part_numbers = Array.from(part_numbers);
				}

				if (Array.isArray(part_numbers) && part_numbers.length > 0) {
				if (typeof frm.add_custom_button === "function") {
					frm.add_custom_button(
						__("Create New Iteration"),
						function () {
							show_iteration_dialog(frm);
						},
						__("Actions")
					);

					// Add button to view Part Stage Matrix report
					frm.add_custom_button(
						__("Part Stage Matrix"),
						function () {
							frappe.set_route("query-report", "Part Stage Matrix", {
								project: frm.doc.name,
							});
						},
						__("View Reports")
					);
				}
				}
			}
		} catch (e) {
			console.error("Error in Project refresh hook:", e);
			if (frappe.boot.developer_mode) {
				frappe.msgprint(
					__(
						"An error occurred in the Project refresh hook. Check console for details."
					),
					"red"
				);
			}
		}
	},
});

function show_iteration_dialog(frm) {
	// Get parts from the project
	let parts = [];
	if (frm.doc.part_numbers) {
		if (Array.isArray(frm.doc.part_numbers)) {
			parts = frm.doc.part_numbers;
		} else if (frm.doc.part_numbers.length !== undefined) {
			parts = Array.from(frm.doc.part_numbers);
		}
	}

	if (parts.length === 0) {
		frappe.msgprint(__("No parts found in this project. Please add parts first."));
		return;
	}

	const part_numbers = parts
		.map((p) => {
			if (typeof p === "object" && p.part_number) {
				return p.part_number;
			}
			return p;
		})
		.filter(Boolean);

	const dialog = new frappe.ui.Dialog({
		title: __("Create New Iteration"),
		fields: [
			{
				fieldtype: "Link",
				fieldname: "part_number",
				label: __("Part Number"),
				options: "Item",
				reqd: 1,
				get_query: function () {
					return {
						filters: {
							name: ["in", part_numbers],
						},
					};
				},
				onchange: function () {
					const part_number = dialog.get_value("part_number");
					if (part_number) {
						update_iteration_info(frm.doc.name, part_number, dialog);
					}
				},
			},
			{
				fieldtype: "Section Break",
				fieldname: "info_section",
			},
			{
				fieldtype: "HTML",
				fieldname: "iteration_info",
				options:
					'<div id="iteration-info-placeholder"><p class="text-muted">' +
					__("Select a part number to view iteration information.") +
					"</p></div>",
			},
			{
				fieldtype: "Section Break",
				fieldname: "warning_section",
			},
			{
				fieldtype: "HTML",
				fieldname: "warning_message",
				options: '<div id="warning-message-placeholder"></div>',
			},
		],
		primary_action_label: __("Create Iteration"),
		primary_action: function () {
			create_iteration(frm, dialog);
		},
	});

	dialog.show();
}

function update_iteration_info(project_name, part_number, dialog) {
	if (dialog.fields_dict.iteration_info && dialog.fields_dict.iteration_info.$wrapper) {
		dialog.fields_dict.iteration_info.$wrapper.html(
			'<p class="text-muted">' + __("Loading iteration information...") + "</p>"
		);
	}

	frappe.call({
		method: "npd_project_module.utils.iteration_management.get_iteration_info",
		args: {
			project_name: project_name,
			part_number: part_number,
		},
		callback: function (r) {
			if (r.exc) {
				console.error("Error fetching iteration info:", r.exc);
				if (
					dialog.fields_dict.iteration_info &&
					dialog.fields_dict.iteration_info.$wrapper
				) {
					dialog.fields_dict.iteration_info.$wrapper.html(
						'<div class="alert alert-danger">' +
							__("Error loading iteration information. Please try again.") +
							"</div>"
					);
				}
				return;
			}

			if (r.message) {
				const info = r.message;

				frappe.db.get_value("Item", part_number, "item_name", function (item_r) {
					const item_name =
						(item_r && item_r.message && item_r.message.item_name) || part_number;

					let infoHTML = '<div class="alert alert-info">';
					infoHTML += `<h6>${__("Iteration Information")}</h6>`;

					if (info.latest_iteration !== null && info.latest_iteration !== undefined) {
						infoHTML += `<p><strong>${__("Latest Iteration")}:</strong> ${
							info.latest_iteration
						}</p>`;

						if (info.cancelled_task) {
							infoHTML += `<p><strong>${__("Cancelled Task")}:</strong> ${
								info.cancelled_task.task_subject || info.cancelled_task.task_name
							}</p>`;
						} else {
							infoHTML += `<p class="text-warning">${__(
								"No cancelled task found in latest iteration. Cannot create new iteration."
							)}</p>`;
						}

						// New iteration always starts from the 2nd stage: "Internal Team Technical Feasibility"
						// RFQ Data (1st stage) is never cancelled and will always be completed
						if (info.new_iteration_start_task) {
							infoHTML += `<p><strong>${__(
								"New Iteration Will Start From"
							)}:</strong> ${
								info.new_iteration_start_task.task_subject ||
								info.new_iteration_start_task.task_name
							}</p>`;
							infoHTML += `<p class="text-info"><em>${__(
								"Note: RFQ Data (1st stage) is always completed and will not be regenerated."
							)}</em></p>`;
						}

						if (info.incomplete_tasks_count > 0) {
							infoHTML += `<p class="text-warning"><strong>${__(
								"Warning"
							)}:</strong> ${info.incomplete_tasks_count} ${__(
								"incomplete task(s) in previous iteration will be marked as obsolete."
							)}</p>`;
						}
					} else {
						infoHTML += `<p>${__("No previous iterations found.")}</p>`;
					}

					if (!info.can_create_new) {
						infoHTML += `<p class="text-danger"><strong>${__("Error")}:</strong> ${__(
							"Maximum iteration limit (10) reached. Cannot create new iteration."
						)}</p>`;
					}

					infoHTML += "</div>";

					let warningHTML = "";
					if (info.incomplete_tasks_count > 0) {
						warningHTML = `<div class="alert alert-warning">
							<strong>${__("Warning")}:</strong> ${__(
							"The previous iteration has {0} incomplete task(s). These will be marked as obsolete when you create the new iteration.",
							[info.incomplete_tasks_count]
						)}
						</div>`;
					}

					if (
						dialog.fields_dict.iteration_info &&
						dialog.fields_dict.iteration_info.$wrapper
					) {
						dialog.fields_dict.iteration_info.$wrapper.html(infoHTML);
					}
					if (
						dialog.fields_dict.warning_message &&
						dialog.fields_dict.warning_message.$wrapper
					) {
						dialog.fields_dict.warning_message.$wrapper.html(warningHTML);
					}
				});
			}
		},
		error: function (r) {
			console.error("Error in frappe.call:", r);
			if (dialog.fields_dict.iteration_info && dialog.fields_dict.iteration_info.$wrapper) {
				dialog.fields_dict.iteration_info.$wrapper.html(
					'<div class="alert alert-danger">' +
						__("Error loading iteration information. Please try again.") +
						"</div>"
				);
			}
		},
	});
}

function create_iteration(frm, dialog) {
	const part_number = dialog.get_value("part_number");

	if (!part_number) {
		frappe.msgprint(__("Please select a part number."));
		return;
	}

	frappe.show_alert({
		message: __("Creating new iteration..."),
		indicator: "blue",
	});

	frappe.call({
		method: "npd_project_module.utils.iteration_management.create_new_iteration",
		args: {
			project_name: frm.doc.name,
			part_number: part_number,
		},
		callback: function (r) {
			if (r.message && r.message.success) {
				dialog.hide();
				frappe.show_alert({
					message: r.message.message,
					indicator: "green",
				});
				frm.reload_doc();
			} else {
				frappe.show_alert({
					message: __("Error creating iteration. Please check the error message."),
					indicator: "red",
				});
			}
		},
		error: function (r) {
			frappe.show_alert({
				message: __("Error creating iteration. Please try again."),
				indicator: "red",
			});
		},
	});
}
