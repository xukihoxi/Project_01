# -*- coding: utf-8 -*-

from odoo import api, fields, models, _



class InheritProduct(models.Model):
    _inherit = 'product.template'

    x_duration = fields.Float(string='Duration', default=0)



class InheritProductProdcut(models.Model):
    _inherit = 'product.product'

    x_duration = fields.Float(string='Duration', related='product_tmpl_id.x_duration', store=True)