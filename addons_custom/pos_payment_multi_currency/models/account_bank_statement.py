# -*- coding: utf-8 -*-

from odoo import models, fields, api

class AccountBankStatement(models.Model):
    _inherit = 'account.bank.statement'

    @api.one
    @api.depends('line_ids', 'line_ids.x_amount_currency')
    def _x_total_multi_currency(self):
        self.x_total_multi_currency = sum([line.x_amount_currency for line in self.line_ids])

    def _default_currency_id(self):
        print(1)

    x_total_multi_currency = fields.Float('Total Multi Subtotal', compute='_x_total_multi_currency', store=True,
                                           help="Total of multi lines.")
    x_currency_id = fields.Many2one('res.currency', "Currency", related='journal_id.x_pos_multi_currency_id')




