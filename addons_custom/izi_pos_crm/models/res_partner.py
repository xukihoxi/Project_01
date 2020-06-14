from odoo import models, fields, api

class ResPartner(models.Model):
    _inherit = 'res.partner'

    reception_id = fields.Many2one('reception.customer')
