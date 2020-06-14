# -*- coding: utf-8 -*-

from odoo import models, fields, api
from datetime import datetime
from odoo.exceptions import UserError, MissingError, ValidationError
from datetime import date, datetime
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT


class DebitProduct(models.TransientModel):
    _name = 'debit.product.transient'

    x_search_id = fields.Many2one('izi.product.search.card')
    debit_id = fields.Many2one('pos.debit.good', 'Debit')
    state = fields.Selection(
        [('debit', 'Debited'),
         ('waiting', 'Waiting'),
         ('rate', 'Rate'),
         ('done', 'Done'), ('approved', 'Approved') ],
        'Status')

    # Sangla themem này 5/3/2019
    # Lấy ra chi tiết đơn nợ hàng. Nợ những gì
    product_id = fields.Many2one('product.product', "Product")
    qty = fields.Float("Qty")
    qty_depot = fields.Float('Qty Depot')
    qty_debit = fields.Float("Qty Debit")
    qty_transfer = fields.Float("Qty Transfer")
    order_id = fields.Many2one('pos.order', "Order")
    date = fields.Date("Date")
    note = fields.Text("Note")