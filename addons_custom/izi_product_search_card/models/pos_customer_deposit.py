# -*- coding: utf-8 -*-

from odoo import models, fields, api
from datetime import datetime
from odoo.exceptions import UserError, MissingError, ValidationError
from datetime import date, datetime
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT


class PosCustomerDeposit(models.TransientModel):
    _name = 'pos.customer.deposit.transient'

    x_search_id = fields.Many2one('izi.product.search.card')

    deposit_id = fields.Many2one('pos.customer.deposit.line', 'Deposit ID')
    order_id = fields.Many2one('pos.order', 'Order ref', readonly=True)
    amount = fields.Float('Amount', readonly=True)
    date = fields.Date("Date")
    session_id = fields.Many2one('pos.session', 'Session')
    note = fields.Text('Note')
    type = fields.Selection([('deposit', 'Deposit'), ('payment', 'Payment'), ('cash', 'Cash')], 'Type')