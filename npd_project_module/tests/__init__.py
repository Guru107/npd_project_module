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
    },
	{
		"doctype": "UOM",
		"name": "Nos"
	},
	{
		"doctype": "Warehouse",
		"name": "Stores"
	}
]
EXTRA_TEST_RECORD_DEPENDENCIES = ["Warehouse Type","UOM","Warehouse","Company", "User","Item","Project Template"]

