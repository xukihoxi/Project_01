# -*- coding: utf-8 -*-

from odoo import models, fields, api
from datetime import datetime
from odoo.exceptions import UserError, MissingError, ValidationError
from datetime import date, datetime
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT


class VipHistory(models.TransientModel):
    _name = 'crm.vip.customer.history.transient'
    _description = u'Lịch sử lên hạng'
    _order = 'create_date desc'

    x_search_id = fields.Many2one('izi.product.search.card')
    rank_current = fields.Many2one('crm.vip.rank', string=u'Hạng hiện tại', readonly=True)
    rank_request = fields.Many2one('crm.vip.rank', string=u'Hạng yêu cầu', readonly=True)
    state = fields.Selection([('pending', u'Chờ duyệt'), ('approved', u'Đã duyệt'), ('cancel', u'Đã từ chối')], u'Trạng thái', default='pending')
    approved_date = fields.Date('Ngày duyệt')
    date = fields.Datetime('Create date')
    approved_uid = fields.Many2one('res.users', u'Người duyệt')
