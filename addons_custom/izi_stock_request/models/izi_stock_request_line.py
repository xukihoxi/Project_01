# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo import time
from odoo.exceptions import ValidationError, except_orm

class IziStockRequestLine(models.Model):
    _name = 'izi.stock.request.line'

    request_id = fields.Many2one('izi.stock.request', string='Request')
    product_id = fields.Many2one('product.product', string='Product')
    uom_id = fields.Many2one('product.uom', string='Uom')
    qty = fields.Float('Quantity')
    reserved_availability = fields.Float('Reserved')
    qty_confirm = fields.Float('Quantity Confirm')
    note = fields.Text('Note')

    @api.onchange('product_id')
    def _onchange_product_id(self):
        if self.product_id:
            self.uom_id = self.product_id.product_tmpl_id.uom_id.id


