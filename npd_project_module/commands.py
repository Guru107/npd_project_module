# Copyright (c) 2025, Guru107 and contributors
# For license information, please see license.txt

"""
Bench commands for NPD Project Module
"""

import click
import frappe
from frappe.commands import pass_context, get_site


@click.command("create-npd-template")
@click.option("--site", help="Site name")
@pass_context
def create_npd_template_command(context, site=None):
	"""Create or update the NPD Template with 18 tasks"""
	from npd_project_module.install.after_install import create_npd_template

	site = site or get_site(context)
	if not site:
		click.echo("Please specify a site with --site or use --site all")
		return

	frappe.init(site=site)
	frappe.connect()

	try:
		create_npd_template()
		frappe.db.commit()
		click.echo("✓ NPD Template created/updated successfully")
	except Exception as e:
		frappe.db.rollback()
		click.echo(f"✗ Error creating NPD Template: {e}", err=True)
		raise
	finally:
		frappe.destroy()


commands = [create_npd_template_command]

