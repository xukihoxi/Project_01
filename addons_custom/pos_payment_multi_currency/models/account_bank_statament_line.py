# -*- coding: utf-8 -*-

from odoo import models, fields, api

class AccountBankStatementLine(models.Model):
    _inherit = 'account.bank.statement.line'

    # Số tiền thanh toán bằng tiền tệ khác
    x_amount_currency = fields.Float('Amount Currency')
    x_currency_id = fields.Many2one('res.currency', "Currency")
    x_currency_rate_id = fields.Many2one('res.currency.rate', "Currency Rate")
    x_rate_vn = fields.Float("Rate VN")

