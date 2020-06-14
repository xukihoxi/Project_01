# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import except_orm


class PosMoney(models.Model):
    _name = 'pos.money'

    name = fields.Char("Name", default='/')
    pos_config_id = fields.Many2one('pos.config', "Pos Config")
    date = fields.Datetime("Date", default=fields.Datetime.now)
    user_id = fields.Many2one('res.users', 'User', default=lambda self: self.env.uid)
    type = fields.Selection([('cash', "Cash"), ('bank', "Bank")], default='cash')
    journal_id = fields.Many2one('account.journal', "Journal")
    branch_id = fields.Many2one('res.branch', "Branch")
    fee_account_id = fields.Many2one('account.account', "Fee Journal")
    # transfer_account_id = fields.Many2one('account.account', "Transfer Journal") # tạm thời bỏ trung gian
    description = fields.Text("Description")
    state = fields.Selection([('draft', "Draft"),('confirm', 'Confirm') ,('done', "Done")], default='draft')
    move_id = fields.Many2one('account.move', string="Move")
    # account_move_ids = fields.Many2many('account.move', string="Account Move")
    balance_start = fields.Float("Balance Start")
    amount_fee = fields.Float("Amount Fee")
    amount = fields.Float("Amount", compute='_compute_amount', store=True)
    balance_end_real = fields.Float("Balance End Real")
    pos_money_line_ids = fields.One2many('pos.money.line', 'pos_money_id', "Pos Money", ondelete='cascade')


    # @api.constrains('pos_money_line_ids')
    # def _check_pos_money_ids(self):
    #     for pm in self:
    #         for a in range(len(pm.pos_money_line_ids)):
    #             for b in range(len(pm.pos_money_line_ids)):
    #                 if a != b:
    #                     if pm.pos_money_line_ids[a].pos_session_id.id == pm.pos_money_line_ids[b].pos_session_id.id and \
    #                             self.pos_money_line_ids[a].payment_method_id.id == pm.pos_money_line_ids[
    #                         b].payment_method_id.id:
    #                         pm.pos_money_line_ids = (2, pm.pos_money_line_ids[b].id, _)
    #                         raise except_orm('Thông báo!',
    #                                          ('Một phiên không thể nộp tiền 2 lần với cùng hình thức thanh toán!'))

    @api.multi
    def action_back_to_draft(self):
        self.state = 'draft'

    # @api.multi
    # def send_money(self):
    #     self.state = 'confirm'

    @api.onchange('type')
    def _onchange_type(self):
        self.journal_id = False
        journal_ids = []
        if self.type == 'cash':
            journals = self.env['account.journal'].search([('type', '=', 'cash'), ('company_id', '=', self.env.user.company_id.id)])
            for id in journals:
                journal_ids.append(id.id)
        elif self.type == 'bank':
            journals = self.env['account.journal'].search([('type', '=', 'bank'), ('company_id', '=', self.env.user.company_id.id)])
            for id in journals:
                journal_ids.append(id.id)

        return {
            'domain': {
                'journal_id': [('id', 'in', journal_ids)]
            }
        }

    @api.model
    def create(self, vals):
        res = super(PosMoney, self).create(vals)
        name = 'P/' + res.pos_config_id.pos_branch_id.code
        sequence = self.env['ir.sequence'].next_by_code('pos.money') or _('New')
        res.name = name + '/' + sequence
        return res

    @api.multi
    def unlink(self):
        for line in self:
            if line.state != 'draft':
                raise except_orm('Thông báo', ('Không thể xóa bản ghi ở trạng thái khác mới'))
        super(PosMoney, self).unlink()


    @api.depends('pos_money_line_ids.amount')
    def _compute_amount(self):
        for s in self:
            for pos_money_line in s.pos_money_line_ids:
                s.amount += pos_money_line.amount

    @api.onchange('pos_config_id')
    def onchange_pos_config(self):
        pos_money = self.env['pos.money'].search([('pos_config_id', '=', self.pos_config_id.id)], order="date desc",limit=1)
        self.balance_start = pos_money.balance_end_real

    @api.multi
    def action_confirm(self):
        move_lines = []
        pos_bank_statement = False
        for pos_money_line in self.pos_money_line_ids:
            pos_bank_statement = self.env['account.bank.statement'].search([('pos_session_id', '=', pos_money_line.pos_session_id.id), ('journal_id', '=', pos_money_line.payment_method_id.id)], limit=1)
            if not pos_bank_statement: raise except_orm('Thông báo', 'Không tìm thấy pos_bank_statement!')
            if pos_bank_statement.total_entry_encoding < pos_money_line.amount:
                raise except_orm('Thông báo', ("Số tiền còn lại của phiên %s ít hơn số tiền nộp " % (pos_money_line.pos_session_id.name, )))
            pos_bank_statement.write({
                'x_cash_posted': pos_bank_statement.x_cash_posted + pos_money_line.amount
            })

        # Nợ
        debit_move_vals = {
            'ref': self.name,
            'account_id': self.journal_id.default_credit_account_id.id,
            'credit': 0.0,
            'debit': self.amount,
            'branch_id': self.branch_id.id,
        }
        move_lines.append((0, 0, debit_move_vals))
        if not self.pos_money_line_ids:
            raise except_orm('Cảnh bao!', "Bạn cần chọn điền số tiền cần nộp")
        # # Có
        for i in self.pos_money_line_ids:
            credit_move_vals = {
                'ref': self.name,
                'account_id': i.payment_method_id.default_debit_account_id.id,
                'credit': i.amount,
                'debit': 0.0,
                'branch_id': self.pos_config_id.pos_branch_id.id,
            }
            move_lines.append((0, 0, credit_move_vals))
        self.state = 'done'
        move_vals = {
            'ref': self.name,
            'journal_id': pos_bank_statement.journal_id.id,
            'line_ids': move_lines
        }
        move_id = self.env['account.move'].create(move_vals)
        move_id.post()
        self.write({'move_id': move_id.id})



    @api.multi
    def close_action_window(self):
        return {'type': 'ir.actions.act_window_close'}

    @api.multi
    def cancel_close_action_window(self):
        self.fee_account_id = False
        self.amount_fee = 0
        return {'type': 'ir.actions.act_window_close'}