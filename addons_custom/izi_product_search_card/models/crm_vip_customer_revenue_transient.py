# -*- coding: utf-8 -*-

from odoo import models, fields, api
from datetime import datetime
from odoo.exceptions import UserError, MissingError, ValidationError
from datetime import date, datetime
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT


class Revenue(models.TransientModel):
    _name = 'crm.vip.customer.revenue.transient'

    x_search_id = fields.Many2one('izi.product.search.card')
    order_id = fields.Many2one('pos.order')
    journal_id = fields.Many2one('account.journal')
    amount = fields.Float(u'Doanh thu')
    date = fields.Date(u'Ngày ghi nhận')
