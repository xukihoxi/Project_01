# -*- coding: utf-8 -*-

from odoo import models, fields, api

class PosOrder(models.Model):
    _inherit = 'pos.order'


    def _prepare_bank_statement_line_payment_values(self, data):
        args = super(PosOrder, self)._prepare_bank_statement_line_payment_values(data)
        if self._context.get('izi_currency_id', False):
            args['x_currency_id'] = self._context.get('izi_currency_id', False)
            args['x_amount_currency'] = self._context.get('izi_money_multi', 0)
            args['x_currency_rate_id'] = self._context.get('izi_currency_rate_id', False)
        return args


