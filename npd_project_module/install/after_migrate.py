# Copyright (c) 2026, Guru107 and contributors
# For license information, please see license.txt

from npd_project_module.install.after_install import add_project_tooling_connection


def after_migrate():
	"""
	Re-assert this app's customizations on the core Project doctype after every migrate.

	The Project → NPD Tooling connection is a DocType Link row parented to Project.
	`custom=1` protects it from Customize Form rewrites, but not from a doctype
	re-import: when `project.json` changes (any ERPNext upgrade that touches Project),
	Frappe reloads it via `delete_doc(..., for_reload=True)`, which drops *every*
	DocType Link row on Project, custom ones included. A one-shot patch cannot recover
	from that, so the connection is re-created here on each `bench migrate` instead.

	Runs after doctype sync and after patches, and the helper is idempotent, so this is
	a no-op on the migrates where nothing was dropped. No manual commit: migrate calls
	these hooks from its `@atomic` post_schema_updates, which commits on success and
	rolls back if anything in the phase raises.
	"""
	add_project_tooling_connection()
