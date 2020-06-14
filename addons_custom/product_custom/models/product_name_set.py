# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, except_orm
from . import utils


class ProductNameSet(models.Model):
    _name = 'product.name.set'

    name = fields.Char(string="Name")
    product_id = fields.Many2one('product.product', string="Product")





