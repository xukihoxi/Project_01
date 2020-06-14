# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import except_orm


class IziCrmLeadQuotes(models.Model):
    _name = 'izi.crm.lead.quotes'

    name = fields.Char(string='Name', related='product_id.name', readonly=1)
    lead_id = fields.Many2one('crm.lead',string='Lead')
    product_id = fields.Many2one('product.product',string='Product')
    qty = fields.Float('Qty')
    price_unit = fields.Float('Price Unit')
    total_amount = fields.Float('Total amount')

    @api.onchange('product_id')
    def _onchange_price(self):
        if self.product_id:
            self.price_unit = self.product_id.product_tmpl_id.list_price
    

    @api.onchange('qty', 'price_unit')
    def _onchange_qty(self):
        self.total_amount = self.price_unit*self.qty

