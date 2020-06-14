# -*- coding: utf-8 -*-

from odoo import models, fields, api
from datetime import datetime
from odoo.exceptions import except_orm, ValidationError, UserError



class NewExchangeService(models.Model):
    _name = 'izi.new.exchange.service'

    service_id = fields.Many2one('product.product',string='Service')
    new_count = fields.Integer('New qty')
    exchange_id = fields.Many2one('izi.pos.exchange.service')
    price_unit = fields.Float('Price unit')
    amount_total = fields.Float(compute='_compute_amount_line_all',string='Amount Total')
    pricelist_id = fields.Many2one('product.pricelist', related='exchange_id.pricelist_id', string='Pricelist')
    partner_id = fields.Many2one('res.partner', related='exchange_id.partner_id', string='Customer')

    @api.onchange('service_id')
    def _onchange_service_id(self):
        if self.service_id:
            self.price_unit = self.pricelist_id.get_product_price(self.service_id, self.new_count or 1.0, self.partner_id)
        else:
            self.price_unit = 0

    @api.onchange('new_count')
    def _onchange_new_count(self):
        if self.new_count < 0:
            self.new_count = 0

    @api.depends('new_count', 'service_id', 'price_unit')
    def _compute_amount_line_all(self):
        for line in self:
            line.amount_total = line.new_count * line.price_unit


