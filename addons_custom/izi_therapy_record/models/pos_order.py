# -*- coding: utf-8 -*-
from odoo import api, fields, models, SUPERUSER_ID, _
from datetime import date
from odoo.exceptions import UserError, ValidationError, MissingError


class PosOrder(models.Model):
    _inherit = 'pos.order'

    @api.model
    def default_get(self, fields):
        res = super(PosOrder, self).default_get(fields)
        if not self._context.get('default_partner_id', False):
            self.partner_id = self._context.get('default_partner_id')
        return res
