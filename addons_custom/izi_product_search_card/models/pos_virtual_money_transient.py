# -*- coding: utf-8 -*-

from odoo import models, fields, api
from datetime import datetime
from odoo.exceptions import UserError, MissingError, ValidationError
from datetime import date, datetime
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT


class VirturalMoney(models.TransientModel):
    _name = 'pos.virtual.money.transient'

    x_search_id = fields.Many2one('izi.product.search.card')
    money = fields.Float('Amount')
    money_order =  fields.Float('Amount Order')
    debt_amount = fields.Float('Debt amount')
    order_id = fields.Many2one('pos.order', 'Order ref')
    expired = fields.Date('Expired')
    money_used = fields.Float('Used amount')
    payment_amount = fields.Float("Payment Amount")
    typex = fields.Selection([('1', u'Tài khoản chính'), ('2', u'Tài khoản khuyến mại')], u"Loại tài khoản",
                             default='2')
    state = fields.Selection([('ready', "Ready"), ('cancel', "Cancel")], default='ready')