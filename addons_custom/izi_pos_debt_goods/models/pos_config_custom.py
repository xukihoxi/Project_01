# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import except_orm

class InheritPosConfig(models.Model):
    _inherit = 'pos.config'

    x_card_picking_type_id = fields.Many2one('stock.picking.type', "Card Picking Type")