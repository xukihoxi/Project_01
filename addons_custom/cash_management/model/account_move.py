# -*- coding: utf-8 -*-
from odoo import models, fields, api, _


class AccountMove(models.Model):
    _inherit = 'account.move'

    x_products_str = fields.Char('Mã chi phí/Sản phẩm')

    @api.model
    def create(self, vals_list):
        if 'line_ids' in vals_list:
            product_ids = []
            for line in vals_list['line_ids']:
                if 'product_id' in line[2]:
                    product_ids.append(line[2]['product_id'])
            if len(product_ids):
                product_str = ''
                for p in self.env['product.product'].browse(list(set(product_ids))):
                    product_str += '%s %s ' % (p.default_code, p.name)
                vals_list['x_products_str'] = product_str

        return super(AccountMove, self).create(vals_list)
