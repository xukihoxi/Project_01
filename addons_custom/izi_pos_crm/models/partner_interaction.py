from odoo import models, fields, api


class PartnerInteraction(models.Model):
    _inherit = 'partner.interaction'

    lead_id = fields.Many2one('crm.lead')


