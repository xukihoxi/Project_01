# -*- coding: utf-8 -*-

from odoo import models, fields, api



class ExchangeServiceCardDetail(models.TransientModel):
    _name = 'izi.exchange.card.detail.history.transient'

    x_search_id = fields.Many2one('izi.product.search.card')
    exchange_id = fields.Many2one('izi.pos.exchange.service')
    exchange_date = fields.Date("Exchange date", required=True)
    session_id = fields.Many2one('pos.session', string='Session')
    current_detail_line_ids = fields.One2many('izi.current.exchange.service.transient', 'exchange_id', 'Curent exchange')
    new_service_detail_line_ids = fields.One2many('izi.new.exchange.service.transient', 'exchange_id', 'New exchange')

class ExchangeServiceCardDetailCurrent(models.TransientModel):
    _name = 'izi.current.exchange.service.transient'

    service_id = fields.Many2one('product.product',string='Service')
    total_count = fields.Integer('Total qty')
    hand_count = fields.Integer('Hand qty')
    used_count = fields.Integer('Used qty')
    to_subtract_count = fields.Integer('Exchange qty')
    price_unit = fields.Float('Price unit')
    amount_subtract = fields.Float(string='Subtract')
    exchange_id = fields.Many2one('izi.exchange.card.detail.history.transient')
    x_search_id = fields.Many2one('izi.product.search.card')
    exchange_detail_id = fields.Many2one('izi.pos.exchange.service')
    date = fields.Datetime("Date")
    lot_id = fields.Many2one('stock.production.lot')


class ExchangeServiceCardDetailNew(models.TransientModel):
    _name = 'izi.new.exchange.service.transient'

    service_id = fields.Many2one('product.product',string='Service')
    new_count = fields.Integer('New qty')
    exchange_id = fields.Many2one('izi.exchange.card.detail.history.transient')
    price_unit = fields.Float('Price unit')
    amount_total = fields.Float(string='Amount Total')
