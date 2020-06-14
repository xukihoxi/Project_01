# -*- coding: utf-8 -*-

from odoo import models, fields, api
from datetime import datetime, timedelta

class IziServiceCardDetail(models.Model):
    _name = 'izi.service.card.detail'

    lot_id = fields.Many2one('stock.production.lot', string='Lot/Serial')
    product_id = fields.Many2one('product.product',string='Service')
    total_qty = fields.Integer('Total')
    qty_hand = fields.Integer('Hand',compute='_compute_qty_hand')
    qty_use = fields.Integer('Qty used')
    remain_amount = fields.Float('Remain amount')
    amount_total = fields.Float('Amount Total')
    price_unit = fields.Float('Price Unit')
    state = fields.Selection([('ready', "Ready"), ('cancel', "Cancel")], default='ready')
    note = fields.Char("Note")
    partner_id = fields.Many2one('res.partner', 'Partner')

    @api.depends('total_qty','qty_use')
    def _compute_qty_hand(self):
        for line in self:
            line.qty_hand = line.total_qty - line.qty_use
