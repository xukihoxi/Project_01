# -*- coding: utf-8 -*-
from odoo import api, fields, models, _


class AccountJournal(models.Model):
    _inherit = "account.journal"

    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=100):
        args = args or []
        if name:
            args += [('name', 'ilike', name)]
        if self._context.get('izi_journal_pay_debt', False):
            session_id = self.env['pos.session'].sudo().browse(self._context['izi_session_id'])
            invoice_id = self.env['account.invoice'].browse(self._context['izi_invoice_id'])
            args = [('id', 'in', session_id.config_id.journal_pay_debt_ids.ids if session_id else [])] + args
            if invoice_id.sudo().x_pos_order_id and invoice_id.sudo().x_pos_order_id.x_type not in ('1','3'):
                args = [('id', '!=', session_id.config_id.journal_vm_id.id)] + args
        res = self.search(args, limit=limit)
        return res.name_get()
