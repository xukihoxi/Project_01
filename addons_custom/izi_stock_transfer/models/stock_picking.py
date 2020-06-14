# -*- coding: utf-8 -*-

from odoo import api, fields, models, _

class StockMove(models.Model):
    _inherit = "stock.move"


    x_transfer_line_id = fields.Many2one('izi.stock.transfer.line','Transfer line')
    x_transfer_from_id = fields.Many2one('izi.stock.transfer','Transfer')
    x_transfer_to_id = fields.Many2one('izi.stock.transfer','Transfer')


