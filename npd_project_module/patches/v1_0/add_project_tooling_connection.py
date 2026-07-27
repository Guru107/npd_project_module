# Copyright (c) 2026, Guru107 and contributors
# For license information, please see license.txt

"""
Add the Project → NPD Tooling connection on existing installs.

Sites that ran the earlier tooling patch before this connection existed won't get it
from that (already-applied) patch, so this dedicated patch ensures it on `bench migrate`.
Reuses the idempotent helper from after_install.
"""

from npd_project_module.install.after_install import add_project_tooling_connection


def execute():
	add_project_tooling_connection()
