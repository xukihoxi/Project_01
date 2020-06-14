# -*- coding: utf-8 -*-

from odoo import models, fields, api
from datetime import datetime, timedelta
import logging

_logger = logging.getLogger(__name__)

class IziStockProductionLot(models.Model):
    _inherit = 'stock.production.lot'

    x_status = fields.Selection(
        [('new', 'New'), ('actived', 'Actived'), ('using', 'Using'),('used', 'Used'), ('destroy', 'Destroy')],
        default='new', readonly=True, string='Status')
    x_customer_id = fields.Many2one('res.partner', string='Customer', domain=[('customer', '=', True)])
    x_user_id = fields.Many2one('res.partner', 'User', domain=[('customer', '=', True)])
    x_amount = fields.Float('Amount')
    x_discount = fields.Float('Discount', readonly=True)
    x_release_id = fields.Many2one('izi.product.release',string='Release')
    x_card_detail_ids = fields.One2many('izi.service.card.detail','lot_id',string='Detail')
    x_payment_amount = fields.Float('Payment Amount')
    x_order_id = fields.Many2one('pos.order', "Order")
    x_product__tmpl_id = fields.Many2one(
        'product.template', 'Product',
        domain=[('x_type_card', '=', 'pmh')], required=True)



