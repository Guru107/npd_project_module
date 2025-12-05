# Copyright (c) 2025, Guru107 and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class ProjectPartNumber(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		iteration_number: DF.Int
		part_number: DF.Data
	# end: auto-generated types

	pass

