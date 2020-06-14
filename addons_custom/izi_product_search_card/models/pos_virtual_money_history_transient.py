# -*- coding: utf-8 -*-

from odoo import models, fields, api
from datetime import datetime
from odoo.exceptions import UserError, MissingError, ValidationError
from datetime import date, datetime
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT


class VirturalMoney(models.TransientModel):
    _name = 'pos.virtual.money.history.transient'

    x_search_id = fields.Many2one('izi.product.search.card')

    vm_id = fields.Many2one('pos.virtual.money', 'Virtual money ID')
    order_id = fields.Many2one('pos.order', 'Order ref', readonly=True)
    # partner_id = fields.Many2one('res.partner', 'Partner', related='order_id.partner_id', readonly=True)
    statement_id = fields.Many2one('account.bank.statement.line', 'Statement ref', readonly=True)
    amount = fields.Float('Amount', readonly=True)
    date = fields.Date()
    service = fields.Char("Service")