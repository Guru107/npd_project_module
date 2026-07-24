# Copyright (c) 2026, Guru107 and contributors
# For license information, please see license.txt

"""
Create the "Tooling" Item Group on existing installs.

The NPD Tooling doctype and Tooling Recovery Register report sync automatically via
`bench migrate`; this patch only seeds the supporting Item Group for sites that were
installed before the tooling feature shipped. It reuses the idempotent setup helper
from after_install so behaviour stays consistent with a fresh install.
"""

from npd_project_module.install.after_install import create_tooling_setup


def execute():
	create_tooling_setup()
