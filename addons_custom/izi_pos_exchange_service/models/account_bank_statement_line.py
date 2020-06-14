# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from datetime import datetime
from odoo.exceptions import except_orm

class PosPaymentService(models.Model):
    _inherit = 'account.bank.statement.line'

    x_exchange_id = fields.Many2one('izi.pos.exchange.service')

class PosMakePayment(models.TransientModel):
    _inherit = 'pos.make.payment'

    @api.multi
    def check(self):
        res = super(PosMakePayment,self).check()
        if self.env.context.get('exchange_id', False):
            order = self.env['pos.order'].browse(self.env.context.get('active_id', False))
            for line in order.statement_ids:
                line.x_exchange_id = self.env.context.get('exchange_id', False)
            exchange_id = self.env['izi.pos.exchange.service'].search([('id','=',self.env.context.get('exchange_id', False))])
            if order.state == 'draft':
                exchange_id.state = 'to_payment'
            if order.state == 'customer_comment':
                exchange_id.state = 'customer_comment'
        return res

