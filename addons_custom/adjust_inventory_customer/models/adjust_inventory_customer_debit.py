# -*- coding: utf-8 -*-
from werkzeug._internal import _log
from odoo import models, fields, api
from odoo.exceptions import ValidationError
from odoo.tools.translate import _
from odoo.exceptions import except_orm, Warning as UserError


class AdjustDebitGoods(models.Model):
    _name = 'adjust.inventory.customer.debit'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    debit_id = fields.Many2one('pos.debit.good.line')
    x_search_id = fields.Many2one('adjust.inventory.customer')
    order_id = fields.Many2one('pos.order', string="Order")
    product_id = fields.Many2one('product.product', string="Product")
    qty = fields.Float(string='Quantity',track_visibility='onchange')
    qty_depot = fields.Float(string='Quantity depot',track_visibility='onchange')
    qty_debit = fields.Float(string='Quantity debit',track_visibility='onchange')
    qty_transfer = fields.Float(string='Quantity transfer',track_visibility='onchange')
    amount_payment = fields.Float(string='Amount')
    date = fields.Date(string='Date')
    note = fields.Text('Note')


