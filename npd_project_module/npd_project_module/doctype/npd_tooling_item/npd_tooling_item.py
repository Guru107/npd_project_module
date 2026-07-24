# Copyright (c) 2026, Guru107 and contributors
# For license information, please see license.txt

from frappe.model.document import Document


class NPDToolingItem(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		amount: DF.Currency
		description: DF.Data | None
		part_number: DF.Link
		qty: DF.Float
		rate: DF.Currency
		supplier: DF.Link | None
		supplier_po: DF.Link | None
		tool_item: DF.Link
		tool_status: DF.Literal["Draft", "PO Issued", "In Development", "Received", "Cancelled"]
	# end: auto-generated types

	pass
