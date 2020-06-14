# -*- coding: utf-8 -*-

from odoo import models, fields, api


class StockInventoryCustomerUpdateProduct(models.Model):
    _name = 'stock.inventory.customer.update.coin'

    def _default_product(self):
        return self.env['product.product'].search([('default_code', '=', 'COIN')], limit=1).id

    inventory_id = fields.Many2one('stock.inventory.customer.update',string='Update Inventory')
    partner_id = fields.Many2one('res.partner', 'Customer')
    product_id = fields.Many2one('product.product', string='Service', default=_default_product)
    total_amount_tkc = fields.Float('Amount tkc')
    use_amount_tkc = fields.Float('Use amount tkc')
    total_amount_km = fields.Float('Amount km')
    use_amount_km = fields.Float('Use amount km')
    x_amount = fields.Float('Amount total')
    x_payment_amount = fields.Float('Amount payment')
    debt = fields.Float('Amount debt')
    order_id = fields.Many2one('pos.order')






