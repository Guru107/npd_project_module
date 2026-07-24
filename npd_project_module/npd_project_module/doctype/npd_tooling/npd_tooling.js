// Copyright (c) 2026, Guru107 and contributors
// For license information, please see license.txt

frappe.ui.form.on("NPD Tooling", {
	setup: function (frm) {
		// Restrict each tool line's Part Number to Items belonging to this order's project.
		frm.set_query("part_number", "tools", function () {
			return { filters: { project: frm.doc.project || "" } };
		});

		// Restrict each tool line's Supplier PO to submitted Purchase Orders of that line's supplier.
		frm.set_query("supplier_po", "tools", function (doc, cdt, cdn) {
			const row = locals[cdt][cdn];
			const filters = { docstatus: 1 };
			if (row.supplier) {
				filters.supplier = row.supplier;
			}
			return { filters: filters };
		});

		// Restrict linked Sales Invoices to submitted invoices of this order's customer.
		frm.set_query("sales_invoice", "invoices", function () {
			const filters = { docstatus: 1 };
			if (frm.doc.customer) {
				filters.customer = frm.doc.customer;
			}
			return { filters: filters };
		});

		// Restrict linked Payment Entries to submitted customer receipts of this order's customer.
		frm.set_query("payment_entry", "payments", function () {
			const filters = { docstatus: 1, payment_type: "Receive", party_type: "Customer" };
			if (frm.doc.customer) {
				filters.party = frm.doc.customer;
			}
			return { filters: filters };
		});
	},

	refresh: function (frm) {
		if (frm.is_new()) {
			return;
		}

		// Recovery figures are computed live from the linked Sales Invoices; reload to refresh.
		frm.add_custom_button(__("Refresh Recovery"), function () {
			frm.reload_doc();
			frappe.show_alert({ message: __("Recovery figures refreshed."), indicator: "green" });
		});
	},
});

// Live amount = qty × rate on each tool line, and keep the order total in sync.
frappe.ui.form.on("NPD Tooling Item", {
	qty: function (frm, cdt, cdn) {
		recalc_line(frm, cdt, cdn);
	},
	rate: function (frm, cdt, cdn) {
		recalc_line(frm, cdt, cdn);
	},
	tools_remove: function (frm) {
		recalc_total(frm);
	},
	tool_item: function (frm, cdt, cdn) {
		// Default the description from the tool Item name when empty.
		const row = locals[cdt][cdn];
		if (row.tool_item && !row.description) {
			frappe.db.get_value("Item", row.tool_item, "item_name", function (r) {
				if (r && r.item_name) {
					frappe.model.set_value(cdt, cdn, "description", r.item_name);
				}
			});
		}
	},
});

function recalc_line(frm, cdt, cdn) {
	const row = locals[cdt][cdn];
	frappe.model.set_value(cdt, cdn, "amount", flt(row.qty) * flt(row.rate));
	recalc_total(frm);
}

function recalc_total(frm) {
	let total = 0;
	(frm.doc.tools || []).forEach((row) => {
		total += flt(row.amount);
	});
	frm.set_value("total_tooling_amount", total);
}

function flt(v) {
	const n = parseFloat(v);
	return isNaN(n) ? 0 : n;
}
