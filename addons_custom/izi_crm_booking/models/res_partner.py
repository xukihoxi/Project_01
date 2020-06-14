# -*- coding: utf-8 -*-

from odoo import api, fields, models, _



class InheritPartner(models.Model):
    _inherit = 'res.partner'

    x_service_booking_ids = fields.One2many('service.booking', 'customer_id', "Service Booking")

    x_service_booking_count = fields.Integer(string='Delivery Orders', compute='_compute_service_booking_ids')

    @api.multi
    def action_view_service_booking(self):
        action = self.env.ref('izi_crm_booking.action_customer_general').read()[0]

        service_bookings = self.mapped('x_service_booking_ids')
        if len(service_bookings) > 1:
            action['domain'] = [('id', 'in', service_bookings.ids)]
        elif service_bookings:
            action['views'] = [(self.env.ref('izi_crm_booking.service_booking_form_view').id, 'form')]
            action['res_id'] = service_bookings.id
        return action

    @api.depends('x_service_booking_ids')
    def _compute_service_booking_ids(self):
        for lead in self:
            lead.x_service_booking_count = len(lead.x_service_booking_ids)

    @api.multi
    def action_booking(self):
        return self.__get_view('service')

    @api.multi
    def action_meeting(self):
        return self.__get_view('meeting')

    def __get_view(self, type):
        view_id = self.env.ref('izi_crm_booking.service_booking_form_view').id
        ctx = {
            'default_type': type,
            'default_customer_id': self.id,

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