# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from datetime import datetime, timedelta

class ScStockCardLine(models.TransientModel):
    _name = 'scstock.card.line'
    stock_card_id = fields.Many2one('scstock.card')
    move_id = fields.Many2one('stock.move', "Stock move")
    date = fields.Datetime("Move date", related='move_id.date')
    date_time = fields.Date("Date")
    reference = fields.Char("Reference")
    note = fields.Char("Note")
    quant_in = fields.Float("Quantity in")
    quant_in_exchange = fields.Char("Quantity in exchange")
    quant_out = fields.Float("Quantity out")
    quant_out_exchange = fields.Char("Quantity out exchange")
    inventory = fields.Float("Inventory")
    inventory_exchange = fields.Char("Inventory Exchange")
