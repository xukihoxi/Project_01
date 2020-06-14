# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from datetime import datetime, date
from odoo.exceptions import except_orm, ValidationError, UserError


class PosOrder(models.Model):
    _inherit = 'pos.order'

    x_type = fields.Selection(selection_add=[('5', 'Exchange_service')])

    @api.multi
    def send_refund(self):
        res = super(PosOrder, self).send_refund()
        exchange_id = self.env['izi.pos.exchange.service'].search([('pos_rf_order_id', '=', self.id)], limit=1)
        if exchange_id:
            self.confirm_refund()
        return res

    @api.multi
    def process_customer_signature(self):
        res = super(PosOrder,self).process_customer_signature()
        exchange_id = self.env['izi.pos.exchange.service'].search([('pos_rf_order_id','=', self.id)],limit=1)
        if exchange_id:
            exchange_id.get_refund()
        return res
