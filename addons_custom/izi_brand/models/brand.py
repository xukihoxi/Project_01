# -*- coding: utf-8 -*-

import base64
import os
import re

from odoo import models, fields, api,tools, _
from odoo.exceptions import except_orm


class Brand(models.Model):
    _name = 'res.brand'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    def _get_logo(self):
        return base64.b64encode(open(os.path.join(tools.config['root_path'], 'addons', 'base', 'res', 'res_company_logo.png'), 'rb') .read())

    name = fields.Char("Name", track_visibility='onchange')
    code = fields.Char("Code", track_visibility='onchange')
    description = fields.Text("Description", track_visibility='onchange')
    ir_sequence_id = fields.Many2one('ir.sequence', "Sequence")
    street = fields.Char()
    state_id = fields.Many2one('res.country.state', string="Fed. State")
    street2 = fields.Char()
    zip = fields.Char()
    city = fields.Char()
    country_id = fields.Many2one('res.country', string='Country')
    logo = fields.Binary(string='Logo', default=_get_logo)

    _sql_constraints = [
        ('code_uniq', 'unique(code)', 'Code is unique'),
    ]

    @api.model
    def create(self, vals):
        SequenceObj = self.env['ir.sequence']

        new = super(Brand, self).create(vals)
        # tạo sequence cho brand
        new.ir_sequence_id = SequenceObj.create({'name': 'Brand sequence [%s]%s' % (new.code, new.name,),
                                                 'prefix': new.code + '/' , 'padding': 4 }).id
        return new

    def get_brand_ids_by_branches(self, branch_ids):
        brand_ids = []
        branches = self.env['res.branch'].search([('id', 'in', branch_ids)])
        for branch in branches:
            if branch.brand_id.id not in brand_ids:
                brand_ids.append(branch.brand_id.id)
        return brand_ids
