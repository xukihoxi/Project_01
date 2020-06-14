# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import except_orm
from datetime import datetime, timedelta


class InhertUseServiceLine(models.Model):
    _inherit = 'izi.service.card.using.line'


    # def _domain_bed(self):
    #     ids = []
    #     branch_id = self.using_id.pos_session_id.config_id.pos_branch_id
    #     room_service_obj = self.env['pos.service.room'].search(
    #         [('branch_id', '=', branch_id.id), ('active', '=', True)])
    #     for line in room_service_obj:
    #         bed_service_obj = self.env['pos.service.bed'].search(
    #             [('room_id', '=', line.id), ('active', '=', True), ('state', '=', 'ready')])
    #         for id in bed_service_obj:
    #             ids.append(id.id)
    #     return [('id', 'in', ids)]

    # bed_id = fields.Many2one('pos.service.bed', "Bed")
    bed_ids = fields.Many2many('pos.service.bed', string="Bed")
    state = fields.Selection([('new', "New"), ('working', "Working"), ('done', "Done")], default='new')
    partner_id = fields.Many2one('res.partner', related='using_id.customer_id', string='Partner')

    @api.onchange('quantity', 'service_id')
    def onchange_bed(self):
        ids = []
        branch_id = self.using_id.pos_session_id.config_id.pos_branch_id
        room_service_obj = self.env['pos.service.room'].search([('branch_id', '=', branch_id.id), ('active', '=', True)])
        for line in room_service_obj:
            bed_service_obj = self.env['pos.service.bed'].search([('room_id', '=', line.id),('active', '=', True), ('state', '=', 'ready')])
            for id in bed_service_obj:
                ids.append(id.id)
        return {
            'domain': {
                'bed_ids': [('id', 'in', ids)]
            }
        }

    @api.multi
    def action_choose_bed(self):
        view_id = self.env.ref('izi_manage_room.izi_service_card_choose_bed_view').id
        return {
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'name': 'Choose bed',
            'res_id': self.id,
            'res_model': 'izi.service.card.using.line',
            'views' : [(view_id, 'form')],
            'target': 'new',
            'flags': {'form': {'action_buttons': True, 'options': {'mode': 'edit'}}}
        }

    @api.multi
    def action_confirm_bed(self):
        if self.state != 'new':
            raise except_orm("Thông báo!", ("Trạng thái đã thay đổi vui lòng load lại"))
        self.write({
            'state': 'working'
        })
        for line in self.bed_ids:
            line.date_start = datetime.now()
            date1 = datetime.strptime(line.date_start, '%Y-%m-%d %H:%M:%S') + timedelta(hours=7)
            line.hour = date1.hour
            line.minutes = date1.minute
            line.seconds = date1.second
            line.write({
                'state': 'busy'
            })

    @api.multi
    def action_back(self):
        if not self.state:
            self.state = 'working'
            for line in self.bed_ids:
                line.state = 'ready'
        if self.sudo().using_id.state == 'done':
            raise except_orm("Thông báo!", ("Đơn sử dụng đã đóng bạn không thể thay dổi trạng thái"))
        if self.state not in('working', 'done'):
            raise except_orm("Thông báo!", ("Trạng thái đã thay đổi vui lòng load lại"))
        if self.state == 'working':
            self.state = 'new'
            for line in self.bed_ids:
                line.state = 'ready'
        if self.state == 'done':
            self.state = 'working'
            for line in self.bed_ids:
                line.state = 'busy'

    @api.multi
    def action_choose_doctor(self):
        view_id = self.env.ref('izi_manage_room.izi_service_card_choose_doctor_view').id
        return {
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'name': 'Choose doctor',
            'res_id': self.id,
            'res_model': 'izi.service.card.using.line',
            'views': [(view_id, 'form')],
            'target': 'new',
            'flags': {'form': {'action_buttons': True, 'options': {'mode': 'edit'}}}
        }

    @api.multi
    def action_done(self):
        if self.state != 'working':
            raise except_orm("Thông báo!", ("Trạng thái đã thay đổi vui lòng load lại"))
        if self.service_id.x_use_doctor and not self.doctor_ids:
            raise except_orm('Thông báo', 'Dịch vụ [%s]%s phải chọn bác sĩ!' % (str(self.service_id.default_code), str(self.service_id.name)))
        self.write({
          'state': 'done'
        })
        for line in self.bed_ids:
            line.write({
              'state': 'ready'
            })
        # self.bed_id.state = 'ready'


class InhertUseService(models.Model):
    _inherit = 'izi.service.card.using'

    @api.multi
    def action_done(self):
        res = super(InhertUseService, self).action_done()
        for line in self.service_card_ids:
            if line.state != 'done':
                raise except_orm("Cảnh báo!", ("Vui lòng cập nhật trạng thái giường trước khi đóng đơn sử dụng"))
        for line in self.service_card1_ids:
            if line.state != 'done':
                raise except_orm("Cảnh báo!", ("Vui lòng cập nhật trạng thái giường trước khi đóng đơn sử dụng"))

    @api.multi
    def action_cancel(self):
        for line in self.service_card_ids:
            line.state = 'done'
            for tmp in line.bed_ids:
                tmp.state = 'ready'
        for line in self.service_card1_ids:
            line.state = 'done'
            for tmp in line.bed_ids:
                tmp.state = 'ready'
        return super(InhertUseService, self).action_cancel()