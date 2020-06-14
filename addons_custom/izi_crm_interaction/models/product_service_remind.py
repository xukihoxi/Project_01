# -*- coding: utf-8 -*-

from odoo import models, fields, api


class ProductServiceRemind(models.Model):
    _name = 'product.service.remind'

    name = fields.Char(string="Name")
    type = fields.Selection([('remind', 'Remind'), ('taking_care_after_do_service', 'Taking care after do service'), ('remind_guarantee', 'Remind guarantee')], string='Type')
    value = fields.Float(string="Value")
    product_id = fields.Many2one('product.product', string="Product")

    @api.onchange('product_id', 'type')
    def _onchange_product_id_type(self):
        if self.product_id and self.type:
            self.name = '%s %s' % (str(self.type), str(self.product_id.name))
