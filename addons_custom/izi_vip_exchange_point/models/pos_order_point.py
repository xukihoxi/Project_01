# -*- coding: utf-8 -*-

from odoo import models, fields, api
from datetime import datetime


class ResPartner(models.Model):
    _inherit = 'res.partner'

    x_point_history_ids = fields.One2many('izi.vip.point.history','partner_id',string='Point')

class PointHistory(models.Model):
    _name = 'izi.vip.point.history'

    partner_id = fields.Many2one('res.partner',string='Customer')
    order_id = fields.Many2one('pos.order',string='Order')
    date = fields.Datetime('Date')
    point = fields.Float('Point')
    exchange_id = fields.Many2one('izi.vip.exchange.point',string='Exchange')

class PosOrder(models.Model):
    _inherit = 'pos.order'

    @api.multi
    def action_order_complete(self):
        res = super(PosOrder, self).action_order_complete()
        # if self.x_point_bonus != 0:
        #     vals={
        #         'partner_id': self.partner_id.id,
        #         'order_id' : self.id,
        #         'date': self.date_order,
        #         'point':self.x_point_bonus,
        #     }
        #     point_history_id = self.env['izi.vip.point.history'].sudo().create(vals)
        return res

