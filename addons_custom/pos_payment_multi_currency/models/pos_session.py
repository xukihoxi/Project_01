# -*- coding: utf-8 -*-

from odoo import models, fields, api

class PosSession(models.Model):
    _inherit = 'pos.session'

    x_cash_total_multi_currency = fields.Float(
        related='cash_register_id.x_total_multi_currency',
        string="Multi Currency",
        help="Total of opening cash currency lines.",
        readonly=True)