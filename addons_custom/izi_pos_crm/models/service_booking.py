from odoo import models, fields, api
from odoo.exceptions import except_orm, ValidationError


class ServiceBooking(models.Model):
    _inherit = 'service.booking'

    _order = 'time_from DESC'
    reception_id = fields.Many2one('reception.customer')
    lead_id = fields.Many2one('crm.lead')

    @api.onchange('name')
    def onchange_name_by_tdv(self):
        if not self.name:
            if not self.lead_id.partner_id:
                vals = {
                    'name': self.lead_id.partner_name,
                    'street': self.lead_id.street,
                    'street2': self.lead_id.street2,
                    'city': self.lead_id.city,
                    'country_id': self.lead_id.country_id.id,
                    'email': self.lead_id.email_from,
                    'phone': self.lead_id.phone,
                    'mobile': self.lead_id.mobile,
                    'zip': self.lead_id.zip,
                    'website': self.lead_id.website,
                    'customer': True,
                    'x_birthday': self.lead_id.x_birthday,
                    'type': '',
                    'x_manage_user_id': self.lead_id.user_id.id,
                    'x_crm_team_id': self.lead_id.team_id.id,
                    'x_brand_id': self.lead_id.team_id.x_branch_id.brand_id.id,
                }
                partner_obj = self.env['res.partner'].search([('phone', '=', vals['phone'])])
                if not partner_obj:
                    partner_id = self.env['res.partner'].create(vals)
                    self.customer_id = partner_id.id
                else:
                # self.lead_id.partner_id = partner_id.id
                    self.customer_id = partner_obj.id
