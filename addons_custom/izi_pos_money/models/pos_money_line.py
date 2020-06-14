# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import except_orm


class PosMoneyLine(models.Model):
    _name = 'pos.money.line'

    name = fields.Char("Name")
    pos_session_id = fields.Many2one('pos.session', 'Pos Session')
    amount = fields.Float("Amount")
    amount_currency = fields.Float(string="Amount currency")
    note = fields.Text("Note")
    balance_start = fields.Float("Balance Start", store=True)
    balance_end_real = fields.Float("Balance End Real")
    pos_money_id = fields.Many2one('pos.money', "Pos Money", ondelete='cascade')
    attachment_ids = fields.Many2many('ir.attachment', string="Attachments", required=True, ondelete='cascade')
    payment_method_id = fields.Many2one('account.journal', string="Payment method" , domain=[('type', '=', 'cash')])

    _sql_constraints = [('pos_money_line_uniq', 'unique (pos_money_id,payment_method_id,pos_session_id)', 'Một phiên không thể nộp tiền 2 lần với cùng hình thức thanh toán!')]

    @api.onchange('pos_session_id')
    def onchange_pos_session(self):
        session_ids = []
        payment_methods = []
        sessions = self.env['pos.session'].search([('config_id', '=', self.pos_money_id.pos_config_id.id),('state', '=', 'closed')])
        for session in sessions:
            for statement in session.statement_ids:
                if statement.journal_id.type == 'cash':
                    # pos_money_line = self.env['pos.money.line'].search([('pos_session_id', '=', session.id), ('payment_method_id', '=', statement.journal_id.id)])
                    # amount = 0
                    # for tmp in pos_money_line:
                    #     amount += tmp.amount
                    # amount -= self.amount
                    if (statement.total_entry_encoding - statement.x_cash_posted) > 0:
                        session_ids.append(session.id)
                        payment_methods.append(statement.journal_id.id)
        return {
            'domain': {
                'pos_session_id': [('id', 'in', session_ids)],
                'payment_method_id': [('id', 'in', payment_methods)]
            }
        }

    @api.onchange('pos_session_id', 'payment_method_id', 'pos_money_id')
    def _onchange_pos_session_payment_method(self):
        if self.pos_session_id and self.payment_method_id:
            pos_money_line = self.env['pos.money.line'].search([('pos_session_id', '=', self.pos_session_id.id), ('payment_method_id', '=', self.payment_method_id.id)])
            pos_bank_statement = self.env['account.bank.statement'].search([('pos_session_id', '=', self.pos_session_id.id), ('journal_id', '=', self.payment_method_id.id)])
            amount = 0
            for tmp in pos_money_line:
                amount += tmp.amount
            amount -= self.amount
            self.balance_start = pos_bank_statement.total_entry_encoding - amount

    @api.onchange('amount')
    def onchange_amount(self):
        if self.amount > self.balance_start:
            raise except_orm('Thông báo', 'Không thể nộp số tiền nhiều hơn trong Pos')
        self.balance_end_real = self.balance_start - self.amount
        if self.amount < 0:
            raise except_orm('Thông báo', 'Số tiền nộp phải > 0')

