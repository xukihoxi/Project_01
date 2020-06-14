# -*- coding: utf-8 -*-

from odoo import models, fields, api


class ProductProduct(models.Model):
    _inherit = 'product.product'

    x_service_remind_ids = fields.One2many('product.service.remind', 'product_id', string="Service remind")
