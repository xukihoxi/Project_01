# -*- coding: utf-8 -*-
from odoo import fields, models, api, _
from odoo.exceptions import UserError, ValidationError
import time


class AccountBankStatement(models.Model):
    _inherit = 'account.bank.statement'

    @api.multi
    def button_confirm_bank(self):
        self._balance_check()
        statements = self.filtered(lambda r: r.state == 'open')
        for statement in statements:
            moves = self.env['account.move']
            for st_line in statement.line_ids:
                if st_line.name != 'Deposit':
                    if st_line.account_id and not st_line.journal_entry_ids.ids:
                        st_line.fast_counterpart_creation()
                    elif not st_line.journal_entry_ids.ids and not statement.currency_id.is_zero(st_line.amount):
                        raise UserError(
                            _('All the account entries lines must be processed in order to close the statement.'))
                    for aml in st_line.journal_entry_ids:
                        moves |= aml.move_id
            if moves:
                moves.filtered(lambda m: m.state != 'posted').post()
            statement.message_post(body=_('Statement %s confirmed, journal items were created.') % (statement.name,))
        statements.link_bank_to_partner()
        statements.write({'state': 'confirm', 'date_done': time.strftime("%Y-%m-%d %H:%M:%S")})
