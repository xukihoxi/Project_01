# -*- coding: utf-8 -*-

from odoo import models, fields, api

class StockInventoryCustomerUpdateMoney(models.Model):
    _name = 'stock.inventory.customer.update.money'

    inventory_id = fields.Many2one('stock.inventory.customer.update',string='Update Inventory')
    partner_id = fields.Many2one('res.partner', 'Customer')
    x_amount = fields.Float('Amount total')






