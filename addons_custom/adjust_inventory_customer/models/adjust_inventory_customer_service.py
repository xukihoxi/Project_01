# -*- coding: utf-8 -*-

from odoo import models, fields, api
from datetime import datetime
from odoo.exceptions import UserError, MissingError, ValidationError
from datetime import date, datetime
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT


class AdjustServiceCardDetail(models.Model):
    _name = 'adjust.inventory.customer.service'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    x_search_id = fields.Many2one('adjust.inventory.customer')
    lot_id = fields.Many2one('stock.production.lot', string='Lot/Serial')
    product_id = fields.Many2one('product.product', string='Service')
    total_qty = fields.Integer('Total',track_visibility='onchange')
    qty_hand = fields.Integer('Hand',track_visibility='onchange')
    qty_use = fields.Integer('Qty used',track_visibility='onchange')
    remain_amount = fields.Float('Remain amount',track_visibility='onchange')
    amount_total = fields.Float('Amount Total',track_visibility='onchange')
    price_unit = fields.Float('Price Unit',track_visibility='onchange')