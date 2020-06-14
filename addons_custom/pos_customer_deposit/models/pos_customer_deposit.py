# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import except_orm, ValidationError, UserError


class PosCustomerDeposit(models.Model):
    _name = 'pos.customer.deposit'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char("Name")
    partner_id = fields.Many2one('res.partner', string='Customer', track_visibility='onchange')
    journal_id = fields.Many2one('account.journal', string='Journal deposit', track_visibility='onchange')
    amount_total = fields.Float('Amount total', compute='_compute_amount')
    residual = fields.Float('Residual', compute='_compute_amount')
    deposit_lines = fields.One2many('pos.customer.deposit.line', 'deposit_id', string='Deposit',
                                    domain=[('type', '=', 'deposit')])
    payment_lines = fields.One2many('pos.customer.deposit.line', 'deposit_id', string='Payment',
                                    domain=[('type', '=', 'payment')])
    cash_lines = fields.One2many('pos.customer.deposit.line', 'deposit_id', string='Cash',
                                 domain=[('type', '=', 'cash')])
    account_move_ids = fields.Many2many('account.move', string="Account Move")

    def _compute_amount(self):
        for cp in self:
            total = 0
            residual = 0
            line = self.env['pos.customer.deposit.line'].search([('deposit_id','=',cp.id),('state','=','done')])
            for i in line:
                if i.type == 'deposit':
                    total = total + i.amount
                    residual = residual + i.amount
                else:
                    residual = residual - i.amount
            cp.amount_total = total
            cp.residual = residual
