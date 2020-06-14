# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.tools import float_compare


class StockScrapInherit(models.Model):
    _inherit = 'stock.scrap'

    x_note = fields.Text(string ='Reason')