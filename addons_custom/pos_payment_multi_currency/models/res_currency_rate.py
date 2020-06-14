# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import except_orm

class ResCurrencyRate(models.Model):
    _inherit = 'res.currency.rate'


    @api.multi
    def name_get(self):
        result = []
        for rate in self:
            result.append((rate.id, str(rate.rate_vn) + ' (' + rate.name + ')'))
        res = result

        return res

    @api.model
    def name_search(self, name='', args=None, operator='ilike', limit=100):
        context = self._context
        rates = False
        print("context: " + str(context))
        if 'izi_x_currency_id' in context:
            currency_rate = self.env['res.currency.rate'].search([('currency_id', '=', context['izi_x_currency_id'])])
            if currency_rate:
                ids = []
                for r in currency_rate:
                    ids.append(r['id'])
                rates = self.sudo().search([('id', 'in', ids)])
            else:
                rates = self.sudo().search([('id', '=', 0)])
        else:
            rates = self.sudo().search([('name', 'ilike', name)], limit=10)
        result = []
        for rate in rates:
            result.append((rate.id, str(rate.rate_vn) + ' (' + rate.name + ')'))
        res = result

        return res














