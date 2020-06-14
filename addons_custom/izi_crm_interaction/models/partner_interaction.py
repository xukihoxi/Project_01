# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import ValidationError, except_orm


class PartnerInteraction(models.Model):
    _name = 'partner.interaction'

    name = fields.Char(related='partner_id.name', string='Name', readonly=1, store=True)
    partner_id = fields.Many2one('res.partner', string='Partner', track_visibility='onchange')
    type_id = fields.Many2one('partner.interaction.type', oldname='type', string='Type', track_visibility='onchange')
    type_name = fields.Char(related='type_id.name', readonly=1, string="Type name")
    date = fields.Date(string="Date", default=fields.Date.context_today)
    user_id = fields.Many2one('res.users', default=lambda self: self.env.uid, string='User')
    service_booking_id = fields.Many2one('service.booking', string="Booking/Meeting")
    using_id = fields.Many2one('izi.service.card.using', string="Service card using")
    using_line_id = fields.Many2one('izi.service.card.using.line', string="Service card using line")
    note = fields.Text(string="Note", track_visibility='onchange')
    survey_id = fields.Many2one('survey.survey', related='type_id.survey_id', string="Survey", store=True, readonly=1)
    survey_user_input_id = fields.Many2one('survey.user_input', string="Survey user input")
    x_user_input_line_ids = fields.One2many('survey.user_input_line', 'x_partner_interaction_id', string='User input line')
    x_user_input_line_count = fields.Integer(string='Count user input line', compute='_compute_user_input_line_count')
    state = fields.Selection([('draft', 'Draft'), ('done', 'Done'), ('cancel', 'Cancel')], default='draft', string="State",
                             track_visibility='onchange')
    partner_interaction_image_ids = fields.One2many('partner.interaction.images', 'partner_interaction_id', string='Image', copy=False)

    @api.multi
    def action_view_user_input_line(self):
        action = self.env.ref('izi_crm_interaction.result_interaction_action_window').read()[0]
        user_input_lines = self.mapped('x_user_input_line_ids')
        if user_input_lines:
            action['domain'] = [('id', 'in', user_input_lines.ids)]
        else:
            action['domain'] = [('id', '=', 0)]
        return action

    @api.depends('x_user_input_line_ids')
    def _compute_user_input_line_count(self):
        for s in self:
            s.x_user_input_line_count = len(s.x_user_input_line_ids)

    @api.multi
    def unlink(self):
        for line in self:
            if line.state != 'draft':
                raise except_orm('Cảnh báo!', ('Chỉ xóa bản ghi ở trạng thái nháp'))
        super(PartnerInteraction, self).unlink()

    @api.multi
    def action_done(self):
        if self.state != 'draft':
            raise except_orm('Thông báo', 'Bản ghi đã thay đổi trạng thái, tải lại trang để cập nhật')
        if not self.survey_user_input_id:
            raise except_orm('Thông báo', 'Chưa nhập kết quả tương tác không thể hoàn thành.')
        if not self.survey_user_input_id.user_input_line_ids:
            raise except_orm('Thông báo', 'Chưa nhập câu trả lời không thể hoàn thành.')

        self.state = 'done'

    @api.multi
    def action_cancel(self):
        if self.state != 'draft':
            raise except_orm('Thông báo', 'Bản ghi đã thay đổi trạng thái, tải lại trang để cập nhật')
        self.state = 'cancel'

    @api.multi
    def action_create_service_booking(self):
        view_id = self.env.ref('izi_crm_booking.service_booking_form_view').id
        ctx = {
            'default_customer_id': self.partner_id.id,
            'default_contact_number': self.partner_id.phone,
            'default_user_id': False,
        }
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'service.booking',
            'view_type': 'form',
            'view_mode': 'form',
            'views': [(view_id, 'form')],
            'target': 'current',
            'context': ctx,
        }

    @api.multi
    def action_input_result_interaction(self):
        if not self.survey_id:
            raise except_orm('Thông báo', 'Chưa có mẫu đánh giá!')
        """ Open the website page with the survey form """
        self.ensure_one()
        user_inputs = self.env['survey.user_input'].search([('x_partner_interaction_id', '=', self.id)])
        if user_inputs:
            for user_input in user_inputs:
                user_input.unlink()

        user_input = self.env['survey.user_input'].create({
            'survey_id': self.survey_id.id,
            'test_entry': False,
            'partner_id': self.partner_id.id,
            'x_user_id': self._uid,
            'x_partner_interaction_id': self.id,
            'type': 'manually'
        })
        token = user_input.token
        self.survey_user_input_id = user_input.id

        return {
            "type": "ir.actions.client",
            'name': 'Start Survey',
            'tag': 'BirtViewerAction',
            'target': 'new',
            'context': {'birt_link': self.survey_id.with_context(relative_url=True).public_url.replace('start', 'fill') +'/'+ token}
        }