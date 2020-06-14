# -*- coding: utf-8 -*-

from odoo import models, fields, api
from datetime import datetime
from odoo.exceptions import except_orm, ValidationError, UserError



class CurrentExchangeService(models.Model):
    _name = 'izi.current.exchange.service'

    service_id = fields.Many2one('product.product',string='Service')
    total_count = fields.Integer('Total qty')
    hand_count = fields.Integer('Hand qty')
    used_count = fields.Integer('Used qty')
    to_subtract_count = fields.Integer('Exchange qty')
    price_unit = fields.Float('Price unit')
    amount_total = fields.Float('Amount Total')
    amount_subtract = fields.Float(compute='_compute_amount_line_all',string='Subtract')
    exchange_id = fields.Many2one('izi.pos.exchange.service')
    card_id = fields.Many2one('izi.service.card.detail')

    @api.onchange('to_subtract_count')
    def _onchange_new_count(self):
        if self.to_subtract_count < 0:
            self.to_subtract_count = 0

    @api.onchange('service_id')
    def _onchange_service_id(self):
        if self.service_id:
            self.price_unit = self.amount_total/self.total_count

    @api.depends('price_unit', 'to_subtract_count','service_id')
    def _compute_amount_line_all(self):
        for line in self:
            line.amount_subtract = line.to_subtract_count * line.price_unit


