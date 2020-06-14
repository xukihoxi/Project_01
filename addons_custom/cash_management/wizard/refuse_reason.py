# -*- coding: utf-8 -*-
from odoo import api, fields, models


class CashManagementRefuseWizard(models.TransientModel):
    _name = "cash.management.refuse.wizard"
    _description = "Refuse Reason wizard"

    reason = fields.Char(string='Reason', required=True)
    cash_id = fields.Many2one('account.cash')

    @api.multi
    def refuse_reason(self):
        self.ensure_one()
        if self.cash_id:
            self.cash_id.refuse(self.reason)
        return {'type': 'ir.actions.act_window_close'}
