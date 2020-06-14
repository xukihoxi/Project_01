# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError


class AccountJournal(models.Model):
    _inherit = "account.journal"

    @api.model
    def name_search(self, name='', args=None, operator='ilike', limit=100):
        args = args or []
        domain = []
        # if name:
        if self._context.get('izi_vm_journal', False):
            izi_vm_journal = self._context.get('izi_vm_journal')
            domain = [('id', 'in', [int(x) for x in izi_vm_journal.split(',')])]
        journals = self.search(domain + args, limit=limit)
        return journals.name_get()
