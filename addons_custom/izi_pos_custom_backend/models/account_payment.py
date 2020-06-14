# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class AccountPayment(models.Model):
    _inherit = "account.payment"

    x_customer_sign = fields.Binary('Chữ ký khách hàng')
    x_payment_debit = fields.Boolean('Payment debit ', default=False)

    def action_validate_invoice_payment(self):
        if not self._context.get('izi_partner_debt', False):
            for record in self:
                for invoice in record.invoice_ids:
                    if invoice.x_pos_order_id:
                        raise UserError("This method should only be called to process an invoice's payment not create from PoS.")
        return super(AccountPayment, self).action_validate_invoice_payment()
