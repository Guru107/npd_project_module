# Copyright (c) 2025, Guru107 and contributors
# For license information, please see license.txt

"""
Test dependencies declaration
"""
import frappe
def before_tests():
    """
    Before tests hook
    """
    # create transit warehouse type
    if not frappe.db.exists("Warehouse Type", "Transit"):
        frappe.get_doc({
            "doctype": "Warehouse Type",
            "warehouse_type": "Transit"
        }).insert()

global_test_dependencies = ["Warehouse Type", "User", "Company", "Item", "Project Template"]
