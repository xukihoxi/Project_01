# -*- coding: utf-8 -*-

from odoo import models, fields, api

class AdjustUpdateMoney(models.Model):
    _name = 'adjust.inventory.customer.deposit'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    partner_id = fields.Many2one('res.partner', 'Customer')
    x_amount = fields.Float('Amount total',track_visibility='onchange')
    x_search_id = fields.Many2one('adjust.inventory.customer')
    deposit_line = fields.Many2one('pos.customer.deposit.line')







