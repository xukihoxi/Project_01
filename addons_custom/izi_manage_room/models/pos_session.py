# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import except_orm
from datetime import datetime, date

class PosSession(models.Model):
    _inherit = 'pos.session'

    @api.multi
    def action_pos_session_close(self):
        user_obj = self.env['res.users']
        user_id = self.env['res.users'].search([('id', '=', self._uid)])
        room_obj = self.env['pos.service.room'].search([('branch_id', '=', user_id.branch_id.id)])
        for line in room_obj:
            bed_obj = self.env['pos.service.bed'].search([('room_id', '=', line.id)])
            for x in bed_obj:
                if x.state == 'busy':
                    x.state == ''
                    # raise except_orm("Cảnh báo!", ("Trạng thái của giường chưa cập nhật hết. Vui lòng kiểm tra lại trạng thái giường"))
        return super(PosSession, self).action_pos_session_close()