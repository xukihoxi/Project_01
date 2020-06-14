# -*- coding: utf-8 -*-

from odoo import models, fields, api

class PosDestroyServiceLine(models.Model):
    _name = 'pos.destroy.service.line'

    service_id = fields.Many2one('product.product', string='Service')
    total_count = fields.Integer('Total qty')
    hand_count = fields.Integer('Hand qty')
    used_count = fields.Integer('Used qty')
    price_unit = fields.Float('Price unit')
    amount_subtract = fields.Float(string='Subtract')
    pos_destroy_service_id = fields.Many2one('pos.destroy.service', "POs Destroy Service")
    card_id = fields.Many2one('izi.service.card.detail')
    destroy_service = fields.Boolean("Destroy Service", default=False)
    amount_total = fields.Float("Amount Total")
    remain_amount = fields.Float("Remain Amount")


class ServiceDestroy(models.Model):
    _name = 'pos.destroy.service.line.detail'

    service_id = fields.Many2one('product.product', string='Service')
    quantity = fields.Float('Quantity')
    price_unit = fields.Float('Price unit')
    discount = fields.Float("Discount")
    x_discount = fields.Float("X Discount")
    subtotal_wo_discount = fields.Float("Subtotal WO Discount", compute='_compute_subtotal', store=True)
    price_subtotal_incl = fields.Float(string='Price Subtotal', compute='_compute_subtotal', store=True)
    pos_destroy_service_id = fields.Many2one('pos.destroy.service', "POs Destroy Service")
    change_fee = fields.Float("Change Fee")

    @api.depends('quantity', 'price_unit', 'discount', 'x_discount', 'change_fee')
    def _compute_subtotal(self):
        for line in self:
            line.subtotal_wo_discount = line.quantity*line.price_unit+line.change_fee
            if line.discount == 100:
                line.price_subtotal_incl = 0
            else:
                line.price_subtotal_incl = line.quantity*line.price_unit - line.x_discount - ((line.quantity*line.price_unit - line.x_discount)*line.discount)/100 +line.change_fee

    @api.onchange('service_id')
    def onchange_service(self):
        ids = []
        # for line in self.pos_destroy_service_id.session_id.config_id.x_charge_refund_id:
        #     ids.append(line.id)
        service_ids = self.env['izi.service.card.detail'].search(
            [('lot_id', '=', self.pos_destroy_service_id.product_lot_id.id)])
        for line in service_ids:
            ids.append(line.product_id.id)
        return {
            'domain': {
                'service_id': [('id', 'in', ids)]
            }
        }

    @api.onchange('service_id')
    def onchange_price_service(self):
        self.price_unit = self.service_id.product_tmpl_id.list_price