# -*- coding: utf-8 -*-

from odoo import models, fields, api
from datetime import datetime
from odoo.exceptions import UserError, MissingError, ValidationError
from datetime import date, datetime
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT


class Orders(models.TransientModel):
    _name = 'izi.pos.order.line.transient'

    x_search_id = fields.Many2one('izi.product.search.card')
    product_id = fields.Many2one('product.product', string='Product')
    lot_name = fields.Char('Lot name')
    qty = fields.Float('Qty')
    price_unit = fields.Float('Price unit')
    discount = fields.Float('Discount')
    x_discount = fields.Float('XDiscount')
    price_subtotal_incl = fields.Float('Total')
    order_id = fields.Many2one('pos.order')
    date_order = fields.Datetime('Date')
    user_id = fields.Many2one('res.users')
    state = fields.Selection(
        [('draft', 'New'), ('to_confirm', 'To confirm'), ('to_approve', 'To approve'),
         ('customer_comment', "Customer Comment"),
         ('cancel', 'Cancelled'), ('paid', 'Paid'), ('done', 'Posted'), ('invoiced', 'Invoiced'), ('to_payment', "To Payment")],
        'Status')
    x_type = fields.Selection([('1', 'Default'), ('2', 'Thẻ tiền'),('3', 'Service'), ('4', 'Destroy Service'), ('5', 'Exchange Service')])