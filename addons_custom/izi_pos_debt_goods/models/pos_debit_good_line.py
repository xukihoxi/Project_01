# -*- coding: utf-8 -*-
from werkzeug._internal import _log
from odoo import models, fields, api
from odoo.exceptions import ValidationError
from odoo.tools.translate import _
from odoo.exceptions import except_orm, Warning as UserError


class DebitGoodsLine(models.Model):
    _name = "pos.debit.good.line"

    debit_id = fields.Many2one('pos.debit.good')

    order_id = fields.Many2one('pos.order', string="Order")
    product_id = fields.Many2one('product.product', string="Product")
    qty = fields.Float(string='Quantity')
    qty_depot = fields.Float(string='Quantity depot')
    qty_debit = fields.Float(string='Quantity debit')
    qty_transfer = fields.Float(string='Quantity transfer')
    amount_payment = fields.Float(string='Amount')
    date = fields.Date(string='Date')
    note = fields.Text('Note')

    #Sanangsla thêm này 6/4/2019 đơn giá và số tiên cần thanh toán cho sác sản phẩm còn nợ
    price_unit = fields.Float("Price Unit")
    price_subtotal_incl = fields.Float("Price Subtotal")




