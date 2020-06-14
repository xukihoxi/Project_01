# -*- coding: utf-8 -*-

from odoo import models, fields, api
from datetime import datetime
from odoo.exceptions import UserError, MissingError, ValidationError
from datetime import date, datetime
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT


class ServiceCardDetail(models.TransientModel):
    _name = 'izi.service.card.detail.transient'

    x_search_id = fields.Many2one('izi.product.search.card')
    lot_id = fields.Many2one('stock.production.lot', string='Lot/Serial')
    product_id = fields.Many2one('product.product', string='Service')
    total_qty = fields.Integer('Total')
    qty_hand = fields.Integer('Hand')
    qty_use = fields.Integer('Qty used')
    remain_amount = fields.Float('Remain amount')
    amount_total = fields.Float('Amount Total')
    price_unit = fields.Float('Price Unit')
    state = fields.Selection([('ready', "Ready"), ('cancel', "Cancel"), ('expired', "Expired")])
    # payment_amount = fields.Float("Payment Amount")
    life_date = fields.Datetime("Life date")
    date_today = fields.Datetime("Date Today", default=fields.Datetime.now)
    debit = fields.Boolean("Debit")
    note = fields.Char("Note")
