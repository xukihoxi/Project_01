# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError


class AccountBankStatementLine(models.Model):
    _inherit = "account.bank.statement.line"

    x_vc_id = fields.Many2one('stock.production.lot', 'Coupon ID', readonly=True)
    x_vc_name = fields.Char(related='x_vc_id.name', readonly=True, store=False)
    x_ignore_reconcile = fields.Boolean('Ignore reconcile', default=False)
    x_payment_id = fields.Many2one('account.payment', "Payment")

    def fast_counterpart_creation(self):
        if len(self) == 1 and self.x_ignore_reconcile:
            return
        return super(AccountBankStatementLine, self).fast_counterpart_creation()
