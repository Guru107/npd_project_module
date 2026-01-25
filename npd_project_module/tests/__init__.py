# Copyright (c) 2025, Guru107 and contributors
# For license information, please see license.txt

"""
Test dependencies declaration
"""
import frappe

test_records = [
    {
        "doctype": "Warehouse Type",
        "name": "Transit"
    }
]

global_test_dependencies = ["Warehouse Type", "User", "Company", "Item", "Project Template"]
