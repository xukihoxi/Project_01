# -*- coding: utf-8 -*-

from odoo import api, fields, models, SUPERUSER_ID, _
from datetime import date
from odoo.exceptions import except_orm, ValidationError, MissingError


class PosSession(models.Model):
    _inherit = 'pos.session'

    @api.multi
    def action_pos_session_close(self):
        deposit_line_ids = self.env['pos.customer.deposit.line'].search([('state','not in',('done','cancel')),('session_id','=',self.id)])
        for line in deposit_line_ids:
            raise except_orm('Cảnh báo!', (
                'Đơn đặt cọc hoặc hoàn tiền "%s" chưa được xử lý. Vui lòng xử lý trước khi đóng phiên' %line.name))
        return super(PosSession,self).action_pos_session_close()

