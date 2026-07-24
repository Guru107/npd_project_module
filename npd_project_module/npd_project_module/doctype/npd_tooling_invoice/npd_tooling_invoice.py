# Copyright (c) 2026, Guru107 and contributors
# For license information, please see license.txt

from frappe.model.document import Document


class NPDToolingInvoice(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		invoiced_amount: DF.Currency
		outstanding_amount: DF.Currency
		posting_date: DF.Date | None
		sales_invoice: DF.Link
	# end: auto-generated types

	pass
