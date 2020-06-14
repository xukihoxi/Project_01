# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import UserError


class PosMakePayment(models.TransientModel):
    _inherit = 'pos.make.payment'

    def _default_journal_vm(self):
        journal_ids = self.env.context.get('izi_journal_ids_vm')
        if journal_ids:
            return journal_ids or ''
        return False

    x_vm_journal_ids = fields.Char('Journal vm', store=False, default=_default_journal_vm)

    def launch_payment(self):
        if self._context.get('izi_coin_payment', False):
            return {
                'name': _('Payment'),
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'pos.make.payment',
                'view_id': self.env.ref('izi_virtual_money.izi_view_pos_payment_vm').id,
                'target': 'new',
                'views': False,
                'type': 'ir.actions.act_window',
                'context': self.env.context,
            }
        return super(PosMakePayment, self).launch_payment()
