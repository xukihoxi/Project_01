# -*- coding: utf-8 -*-

from odoo import models, fields, api
from datetime import datetime
from odoo.exceptions import UserError, MissingError, ValidationError
from datetime import date, datetime
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT


class UseServiceCardDetail(models.TransientModel):
    _name = 'izi.use.card.detail.history.transient'

    x_search_id = fields.Many2one('izi.product.search.card')
    redeem_date = fields.Datetime("Redeem Date")
    service_id = fields.Many2one('product.product', "Service")
    quantity = fields.Float("Quantity")
    uom_id = fields.Many2one('product.uom')
    employee = fields.Char("Employee")
    using_id = fields.Many2one('izi.service.card.using', "Using")
    serial_id = fields.Many2one('stock.production.lot', "Serial")
    price_unit = fields.Float("Price Unit")
    order_id = fields.Many2one('pos.order')
    state=fields.Char()
    customer_sign = fields.Binary('Customer Sign')
    note = fields.Char("Note")
    type = fields.Selection([('service', "Service"), ('card', "Card"), ('guarantee', "Guarantee")])
