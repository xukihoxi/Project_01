# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.addons import decimal_precision as dp
from odoo.exceptions import UserError
from odoo.tools import float_utils


class Inventory(models.Model):
    _inherit = "stock.inventory"


    @api.multi
    def run_stock_inventory(self):
        inventory_ids = self.search([('state','=', 'confirm')])
        for inventory_id in inventory_ids:
            inventory_id.action_done()