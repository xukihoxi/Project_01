# -*- coding: utf-8 -*-

from odoo import models, fields, api



class DestroyServiceCardDetail(models.TransientModel):
    _name = 'izi.destroy.card.detail.history.transient'

    x_search_id = fields.Many2one('izi.product.search.card')
    destroy_id = fields.Many2one('pos.destroy.service')
    destroy_date = fields.Date("Destroy date", required=True)
    session_id = fields.Many2one('pos.session', string='Session')
    destroy_detail_line_ids = fields.One2many('izi.pos.destroy.service.transient', 'destroy_id', 'Curent exchange')
    new_destroy_detail_line_ids = fields.One2many('izi.pos.destroy.service.line.transient', 'destroy_id', 'New exchange')

class DestroyServiceCardDetail(models.TransientModel):
    _name = 'izi.pos.destroy.service.transient'

    service_id = fields.Many2one('product.product',string='Service')
    total_count = fields.Integer('Total qty')
    hand_count = fields.Integer('Hand qty')
    used_count = fields.Integer('Used qty')
    to_subtract_count = fields.Integer('Exchange qty')
    price_unit = fields.Float('Price unit')
    amount_total = fields.Float(string='Subtract')
    destroy_id = fields.Many2one('izi.exchange.card.detail.history.transient')
    x_search_id = fields.Many2one('izi.product.search.card')


class DestroyServiceCardDetailLine(models.TransientModel):
    _name = 'izi.pos.destroy.service.line.transient'

    service_id = fields.Many2one('product.product',string='Service')
    new_count = fields.Integer('New qty')
    destroy_id = fields.Many2one('izi.destroy.card.detail.history.transient')
    price_unit = fields.Float('Price unit')
    amount_total = fields.Float(string='Amount Total')
    pos_destroy_service_id = fields.Many2one('pos.destroy.service', "Destroy Service")
    x_search_id = fields.Many2one('izi.product.search.card')
    date = fields.Date("Date")
    lot_id = fields.Many2one('stock.production.lot')