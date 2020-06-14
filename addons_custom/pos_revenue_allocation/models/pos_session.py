# -*- coding: utf-8 -*-

from odoo import api, fields, models, SUPERUSER_ID, _
from datetime import date
from odoo.exceptions import except_orm, ValidationError, MissingError


class PosSession(models.Model):
    _inherit = 'pos.session'

    @api.multi
    def action_pos_session_close(self):
        Allocation = self.env['pos.revenue.allocation']
        pos_order_ids = self.env['pos.order'].search([('session_id','=',self.id)])
        for order in pos_order_ids:
            if len(order.x_allocation_ids) == 0 and order.x_total_order > 0 and order.x_user_id:
                raise except_orm('Cảnh báo!', (
                    'Đơn hàng "%s" chưa được phân bổ doanh thu. Vui lòng phân bổ trước khi đóng phiên' %order.name))
            allo = Allocation.search([('order_id', '=', order.id)])
            for a in allo:
                if a.state == 'draft':
                    raise except_orm('Cảnh báo!', (
                            'Đơn phân bổ "%s" chưa đóng. Vui lòng đóng phân bổ' % a.name))
        return super(PosSession,self).action_pos_session_close()

