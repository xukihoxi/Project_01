# -*- coding: utf-8 -*-

from odoo import models, fields, api
from datetime import datetime
from odoo.exceptions import UserError, MissingError, ValidationError
from datetime import date, datetime
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT


class StockProductionLotPmh(models.TransientModel):
    _name = 'izi.pmh.service.lot.transient'

    x_search_id = fields.Many2one('izi.product.search.card')
    name = fields.Char(string='name')
    product_id = fields.Many2one('product.product',string='Product')
    life_date = fields.Datetime('Life date')
    x_status = fields.Selection(
        [('new', 'New'), ('actived', 'Actived'), ('using', 'Using'), ('used', 'Used'), ('destroy', 'Destroy')],
        string='Status')
    x_customer_id = fields.Many2one('res.partner', string='Customer')
    x_user_id = fields.Many2one('res.partner')
    x_amount = fields.Float('Amount')
    x_discount = fields.Float('Discount')
    order_id = fields.Many2one('pos.order')
    order_payment_id = fields.Many2one('pos.order')
    date_today = fields.Datetime("Date Today", default=fields.Datetime.now)
