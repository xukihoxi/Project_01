# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _


class ResBranch(models.Model):
    _name = 'res.branch'
    _description = 'Branch'

    name = fields.Char(required=True)
    company_id = fields.Many2one('res.company', required=True)
    telephone = fields.Char(string='Telephone No')
    address = fields.Text('Address')
    code = fields.Char("Code")
    brand_id = fields.Many2one('res.brand', string="Brand")

    _sql_constraints = [
        ('code_uniq', 'unique(code)', 'Code is unique'),
    ]