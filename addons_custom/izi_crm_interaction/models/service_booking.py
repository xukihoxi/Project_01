# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import except_orm
from datetime import datetime
from dateutil.relativedelta import relativedelta

import logging

_logger = logging.getLogger(__name__)


class ServiceBooking(models.Model):
    _inherit = 'service.booking'

    partner_interaction_ids = fields.One2many('partner.interaction', 'service_booking_id', string="Partner interactions")
    survey_label_id = fields.Many2one('survey.label', string="Result confirm booking/meeting")

    @api.multi
    def action_create_interaction(self):
        type_confirm_booking_meeting = self.env['partner.interaction.type'].search([('name', '=', 'Xác nhận Booking/Meeting')])
        if not type_confirm_booking_meeting: raise except_orm('Thông báo', 'Chưa cấu hình loại tương tác khách hàng là: Xác nhận Booking/Meeting')

        interaction = self.env['partner.interaction'].search([('service_booking_id', '=', self.id)])
        if interaction: raise except_orm('Thông báo', '%s đã tạo tương tác với khách hàng %s không thể tạo thêm.' % (str(self.name), str(self.customer_id.name)))

        view_id = self.env.ref('izi_crm_interaction.partner_interaction_form_view').id
        ctx = {
            'default_partner_id': self.customer_id.id,
            'default_type_id': type_confirm_booking_meeting.id,
            'default_date': datetime.today(),
            'default_user_id': self._uid,
            'default_service_booking_id': self.id,
            'default_survey_id': type_confirm_booking_meeting.survey_id.id,
        }

        return {
            'name': 'Partner interaction',
            'type': 'ir.actions.act_window',
            'res_model': 'partner.interaction',
            'view_type': 'form',
            'view_mode': 'form',
            'views': [(view_id, 'form')],
            'target': 'current',
            'context': ctx,
        }