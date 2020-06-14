# -*- coding: utf-8 -*-
from odoo import models, api, fields


class ProductProduct(models.Model):
    _inherit = 'product.product'

    x_name_set_ids = fields.One2many('product.name.set', 'product_id', string="Name sets")

    @api.model
    def search(self, args, offset=0, limit=None, order=None, count=False):
        context = self._context or {}
        if context.get('izi_pos_product_search'):
            args += [('product_tmpl_id.default_code', 'not in', ['COIN', 'PDDV', 'PHOI', 'DISCOUNT', 'VDISCOUNT'])]
        return super(ProductProduct, self).search(args, offset, limit, order, count=count)
