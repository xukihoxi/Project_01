# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import except_orm

class PosSession(models.Model):
    _inherit = 'pos.session'

    @api.multi
    def action_pos_session_close(self):
        destroy_service_ids = self.env['pos.destroy.service'].search([('session_id', '=', self.id)])
        for destroy in destroy_service_ids:
            if destroy.state not in ('done', 'cancel'):
                raise except_orm('Cảnh báo!', (
                        'Đơn hủy dịch vụ "%s" chưa được hoàn thiện. Vui lòng hoàn thành trước khi đóng phiên' % destroy.name))
        return super(PosSession, self).action_pos_session_close()