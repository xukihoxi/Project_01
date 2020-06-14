# -*- coding: utf-8 -*-

from odoo import models, fields, api

class StockInventoryCustomerUpdateProduct(models.Model):
    _name = 'stock.inventory.customer.update.product'

    inventory_id = fields.Many2one('stock.inventory.customer.update',string='Update Inventory')
    partner_id = fields.Many2one('res.partner', 'Customer')
    product_id = fields.Many2one('product.product','Service')
    lot_id = fields.Many2one('stock.production.lot', 'Lot')
    total_qty = fields.Integer('Qty total')
    qty_hand = fields.Integer('Qty hand')
    qty_use = fields.Integer('Qty used')
    x_amount = fields.Float('Amount total')
    x_payment_amount = fields.Float('Amount payment')
    debt = fields.Float('Amount debt')
    order_id = fields.Many2one('pos.order')
    note = fields.Char("Note")







