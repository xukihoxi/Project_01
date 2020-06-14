# -*- coding: utf-8 -*-

from odoo import models, fields, api

class AccountJounal(models.Model):
    _inherit = 'account.journal'

    x_pos_multi_currency_id = fields.Many2one('res.currency', "Pos Multi Currency")
