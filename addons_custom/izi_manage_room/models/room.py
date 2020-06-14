# -*- coding: utf-8 -*-

from odoo import models, fields, api

class PosServiceRoom(models.Model):
    _name = 'pos.service.room'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char("Name",track_visibility='onchange')
    code = fields.Char("Code",track_visibility='onchange', copy=False)
    branch_id = fields.Many2one('res.branch', "Branch",track_visibility='onchange')
    active = fields.Boolean("Active", default=True, track_visibility='onchange')
    color = fields.Integer("Color")
    bed_ids = fields.One2many("pos.service.bed", 'room_id', "Bed")
    count_bed = fields.Float("Count Bed")
    note = fields.Char("Note")



    _sql_constraints = [
        ('code_uniq', 'unique(code)', 'Code is unique'),
    ]

