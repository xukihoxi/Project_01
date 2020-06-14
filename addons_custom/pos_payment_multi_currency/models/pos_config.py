# -*- coding: utf-8 -*-
from odoo import fields, models


class PosConfig(models.Model):
    _inherit = 'pos.config'

    # Các phương thức tiền tệ khác
    x_journal_currency_ids = fields.Many2many('account.journal', 'pos_config_journal_currency_rel', 'config_id',
                                           'journal_id',
                                           domain="[('journal_user', '=', True )]",
                                           string='Các phương thức thanh toán bằng tiền tệ khác',
                                           help='Các phương thức thanh toán bằng tiền tệ khác')