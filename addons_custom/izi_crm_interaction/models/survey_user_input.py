# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import ValidationError, except_orm
from datetime import datetime


class SurveyUserInput(models.Model):
    _inherit = 'survey.user_input'

    x_partner_interaction_id = fields.Many2one('partner.interaction', string="Partner interaction")
    x_partner_interaction_date = fields.Date(related='x_partner_interaction_id.date', string="Partner interaction date", store=True)
    x_user_id = fields.Many2one('res.users', string="User")


class SurveyUserInputLine(models.Model):
    _inherit = 'survey.user_input_line'

    x_partner_interaction_id = fields.Many2one('partner.interaction', related='user_input_id.x_partner_interaction_id', string="Partner interaction", store=True)
    x_partner_interaction_date = fields.Date(related='user_input_id.x_partner_interaction_date', string="Partner interaction date", store=True)
    x_user_id = fields.Many2one(related='user_input_id.x_user_id', string="User", store=True)
    x_partner_id = fields.Many2one(related='user_input_id.partner_id', string="Partner", store=True)

    @api.model
    def create(self, vals):
        if 'user_input_id' in vals and vals['user_input_id']:
            user_input_id = self.env['survey.user_input'].search([('id', '=', vals['user_input_id'])], limit=1)
            if not user_input_id: raise except_orm("Đang tạo survey.user_input_line không tìm thấy user_input_id(%s)!" % (str(vals['user_input_id'])))
            if user_input_id.x_partner_interaction_id and user_input_id.x_partner_interaction_id.service_booking_id:
                service_booking_id = user_input_id.x_partner_interaction_id.service_booking_id
                service_booking_id.write({
                    'survey_label_id': vals['value_suggested']
                })
        return super(SurveyUserInputLine, self).create(vals)