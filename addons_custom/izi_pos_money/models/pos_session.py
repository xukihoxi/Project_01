# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import except_orm


class PosSession(models.Model):
    _inherit = 'pos.session'

    @api.one
    def _compute_x_cash_posted(self):
        cash_posted = 0
        if self.statement_ids:
            for statement in self.statement_ids:
                if statement.journal_id.type == 'cash':
                    cash_posted += statement.x_cash_posted
        self.x_cash_posted = cash_posted

    x_cash_posted = fields.Float(default=0, string="Cash posted", compute="_compute_x_cash_posted", readonly=1)


class AccountBankStatement(models.Model):
    _inherit = 'account.bank.statement'

    x_cash_posted = fields.Float(default=0, string="Cash posted")