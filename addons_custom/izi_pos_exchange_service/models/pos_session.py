# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import except_orm
from datetime import datetime, date

class PosSession(models.Model):
    _inherit = 'pos.session'

    @api.multi
    def action_pos_session_close(self):
        pos_exchange_service_ids = self.env['izi.pos.exchange.service'].search([('session_id', '=', self.id)])
        for exchange in pos_exchange_service_ids:
            if exchange.state not in ('done', 'refunded', 'cancel'):
                raise except_orm('Cảnh báo!', (
                    'Đơn đổi dịch vụ "%s" chưa được hoàn thiện. Vui lòng hoàn thành trước khi đóng phiên' % exchange.name))
        return super(PosSession, self).action_pos_session_close()