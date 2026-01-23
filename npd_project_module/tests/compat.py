# Copyright (c) 2025, Guru107 and contributors
# For license information, please see license.txt

"""
Compatibility layer for Frappe v15 and v16.
Handles differences between versions.
"""

import frappe
from frappe.tests.utils import FrappeTestCase

# Check Frappe version
def get_frappe_version():
	"""Get Frappe version as tuple (major, minor, patch)."""
	version_str = getattr(frappe, "__version__", "0.0.0")
	parts = version_str.split(".")
	try:
		return (int(parts[0]), int(parts[1]), int(parts[2]) if len(parts) > 2 else 0)
	except (ValueError, IndexError):
		return (0, 0, 0)

# In Frappe v15, IntegrationTestCase doesn't exist, use FrappeTestCase
# In Frappe v16+, IntegrationTestCase might exist
try:
	from frappe.tests import IntegrationTestCase
except ImportError:
	# Frappe v15 compatibility: IntegrationTestCase is just FrappeTestCase
	IntegrationTestCase = FrappeTestCase

__all__ = ["IntegrationTestCase", "get_frappe_version"]
