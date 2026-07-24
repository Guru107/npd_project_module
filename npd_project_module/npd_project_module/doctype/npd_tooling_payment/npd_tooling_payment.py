# Copyright (c) 2026, Guru107 and contributors
# For license information, please see license.txt

from frappe.model.document import Document


class NPDToolingPayment(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		allocated_amount: DF.Currency
		paid_amount: DF.Currency
		payment_entry: DF.Link
		posting_date: DF.Date | None
		reference_milestone: DF.Data | None
	# end: auto-generated types

	pass
