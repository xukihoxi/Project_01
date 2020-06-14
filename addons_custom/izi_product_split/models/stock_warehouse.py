# -*- coding: utf-8 -*-

from odoo import models, fields, api,_


class Warehouse(models.Model):
    _inherit = "stock.warehouse"

    x_outgoing_split_id = fields.Many2one('stock.picking.type', 'Split out Type')
    x_incoming_split_id = fields.Many2one('stock.picking.type', 'Split in Type')





