# -*- coding: utf-8 -*-

from odoo import api, fields, models, SUPERUSER_ID, _
from datetime import date
from odoo.exceptions import except_orm, ValidationError, MissingError


class PosSession(models.Model):
    _inherit = 'pos.session'

    @api.multi
    def action_pos_session_close(self):
        pos_order_ids = self.env['pos.order'].search([('session_id','=',self.id), ('x_status', '=', 'change')])
        for order in pos_order_ids:
            raise except_orm('Cảnh báo!', (
                'Đơn hàng "%s" chưa đóng thanh toán. Vui lòng dóng thanh toán trước khi đóng phiên' %order.name))
        return super(PosSession,self).action_pos_session_close()
