# -*- coding: utf-8 -*-

from odoo import api, fields, models, _


class CrmLead(models.Model):
    _inherit = 'crm.lead'

    service_booking_ids = fields.One2many('service.booking', 'crm_lead_id', "Service Booking")
    service_booking_count = fields.Integer(string='Delivery Orders', compute='_compute_service_booking_ids')
    #todo create to use in pos_crm
    time_booking = fields.Datetime(string='Time Booking', compute='get_time_booking')

    @api.multi
    def action_view_service_booking(self):
        action = self.env.ref('izi_crm_booking.action_customer_general').read()[0]

        service_bookings = self.mapped('service_booking_ids')
        if len(service_bookings) > 1:
            action['domain'] = [('id', 'in', service_bookings.ids)]
        elif service_bookings:
            action['views'] = [(self.env.ref('izi_crm_booking.service_booking_form_view').id, 'form')]
            action['res_id'] = service_bookings.id
        return action

    @api.depends('service_booking_ids')
    def _compute_service_booking_ids(self):
        for lead in self:
            lead.service_booking_count = len(lead.service_booking_ids)

    @api.multi
    def action_booking(self):
        return self.__get_view('service')

    @api.multi
    def action_meeting(self):
        return self.__get_view('meeting')

    def __get_view(self, type):
        view_id = self.env.ref('izi_crm_booking.service_booking_form_view').id
        if not self.partner_id:
            vals = {
                'name': self.partner_name,
                'street': self.street,
                'street2': self.street2,
                'city': self.city,
                'country_id': self.country_id.id,
                'email': self.email_from,
                'phone': self.phone,
                'mobile': self.mobile,
                'zip': self.zip,
                'website': self.website,
                'customer': True,
                'x_birthday': self.x_birthday,
                'type': '',
                'x_manage_user_id': self.user_id.id,
                'x_crm_team_id': self.team_id.id,
                'x_brand_id': self.team_id.x_branch_id.brand_id.id,
            }
            partner_id = self.env['res.partner'].create(vals)
            self.partner_id = partner_id.id

        products = self.__get_service_booking_products()

        ctx = {
            'default_crm_lead_id': self.id,
            'default_type': type,
            'default_customer_id': self.partner_id.id,
            'default_product_ids': products,
            'default_team_id': self.team_id.id if self.team_id else False,
            'default_user_id': self.user_id.id if self.user_id else False,
        }
        return {
            'name': type[0].upper() + type[1:],
            'type': 'ir.actions.act_window',
            'res_model': 'service.booking',
            'view_type': 'form',
            'view_mode': 'form',
            'views': [(view_id, 'form')],
            'target': 'current',
            'context': ctx,
        }

    def __get_service_booking_products(self):
        if not self.x_lines:
            return []

        products = [(0, 0, {'product_id': line.product_id.id,
                            'qty': line.qty,
                            'amount_total': line.total_amount})
                    for line in self.x_lines]
        return products

    @api.depends('service_booking_ids')
    def get_time_booking(self):
        for s in self:
            have_booking = False
            for service_booking in s.service_booking_ids:
                if service_booking.state == 'ready':
                    s.time_booking = service_booking.time_from
                    have_booking = True
                    break
            if not have_booking: s.time_booking = False
