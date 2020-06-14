# -*- coding: utf-8 -*-

from odoo import models, fields, api
from datetime import datetime
from odoo.exceptions import UserError, MissingError, ValidationError
from datetime import date, datetime
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT


class AdjustVirturalMoney(models.Model):
    _name = 'adjust.inventory.customer.coin'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    x_search_id = fields.Many2one('adjust.inventory.customer')
    money = fields.Float('Amount',track_visibility='onchange')
    debt_amount = fields.Float('Debt amount',track_visibility='onchange')
    order_id = fields.Many2one('pos.order', 'Order ref')
    expired = fields.Date('Expired',track_visibility='onchange')
    money_used = fields.Float('Used amount',track_visibility='onchange')
    typex = fields.Selection([('1', u'Tài khoản chính'), ('2', u'Tài khoản khuyến mại')], u"Loại tài khoản",
                             default='2')
    state = fields.Selection([('ready', "Ready"), ('cancel', "Cancel")], default='ready')
    virtual_money_id = fields.Many2one('pos.virtual.money')