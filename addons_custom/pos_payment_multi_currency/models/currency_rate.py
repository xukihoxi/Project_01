# -*- coding: utf-8 -*-

from odoo import models, fields, api


class IziCurrencyRate(models.Model):
    _inherit = "res.currency.rate"

    rate = fields.Float(digits=(30, 14), help='The rate of the currency to the currency of rate 1')
    rate_vn = fields.Float(digits=(30, 3), help='The rate of the currency to the currency of rate 1')

    @api.onchange('rate_vn')
    def _onchange_res_currency(self):
        if self.rate_vn != 0:
            self.rate = 1/self.rate_vn


class IziResCurrency(models.Model):
    _inherit = "res.currency"

    rate = fields.Float(compute='_compute_current_rate', string='Current Rate', digits=(30, 14),
                        help='The rate of the currency to the currency of rate 1.')