# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import except_orm
from datetime import datetime, date

class PosSession(models.Model):
    _inherit = 'pos.session'

    @api.multi
    def action_pos_session_close(self):
        use_service_ids = self.env['izi.service.card.using'].search([('pos_session_id', '=', self.id)])
        for use in use_service_ids:
            if use.state not in ('done', 'cancel'):
                raise except_orm('Cảnh báo!', (
                    'Đơn sử dụng dịch vụ "%s" chưa được hoàn thiện. Vui lòng hoàn thành trước khi đóng phiên' % use.name))
        return super(PosSession, self).action_pos_session_close()