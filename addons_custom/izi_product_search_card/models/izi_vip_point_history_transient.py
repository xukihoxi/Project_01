# -*- coding: utf-8 -*-

from odoo import models, fields, api
from datetime import datetime
from odoo.exceptions import UserError, MissingError, ValidationError
from datetime import date, datetime
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT


class VipPoint(models.TransientModel):
    _name = 'izi.vip.point.history.transient'

    x_search_id = fields.Many2one('izi.product.search.card')
    order_id = fields.Many2one('pos.order', string='Order')
    date = fields.Datetime('Date')
    point = fields.Float('Point')
    exchange_id = fields.Many2one('izi.vip.exchange.point', string='Exchange')

