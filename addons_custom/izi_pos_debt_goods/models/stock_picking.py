# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import except_orm
from datetime import date

class StockPicking(models.Model):
    _inherit = 'stock.picking'

    @api.multi
    def action_done(self):
        picking = super(StockPicking,self).action_done()
        Debit = self.env['pos.debit.good']
        debit_id = Debit.search([('name', '=', self.origin)], limit=1)
        if debit_id.id != False:
            for line in debit_id.line_ids:
                if line.qty_transfer != 0:
                    # tao lich su
                    debit_vals_history = {
                        'date': fields.Datetime.now(),
                        'debit_id': line.debit_id.id,
                        'picking_id': self.id,
                    }
                    self.env['pos.debit.good.history'].create(debit_vals_history)
                    #capnhat lai só lượng nợ
                    line.qty_depot = line.qty_depot + line.qty_transfer
                    line.qty_debit = line.qty_debit - line.qty_transfer
                    line.qty_transfer = 0
            debit_id.state = 'rate'
            # SangsLA thêm ngày 3/10/2018 Thêm using_service vào form khi chung của khách hàng
            # pos_sum_digital_obj = self.env['pos.sum.digital.sign'].search(
            #     [('partner_id', '=', debit_id.partner_id.id), ('state', '=', 'draft')])
            # if pos_sum_digital_obj:
            #     debit_id.update({'x_digital_sign_id': pos_sum_digital_obj.id})
            # else:
            #     pos_sum_digital_id = self.env['pos.sum.digital.sign'].create({
            #         'partner_id': debit_id.partner_id.id,
            #         'state': 'draft',
            #         'date': date.today()
            #     })
            #     debit_id.update({'x_digital_sign_id': pos_sum_digital_id.id})
            #         hết
        return picking

    @api.multi
    def action_cancel(self):
        picking = super(StockPicking,self).action_cancel()
        Debit = self.env['pos.debit.good']
        debit_id = Debit.search([('name', '=', self.origin)], limit=1)
        if debit_id.id != False:
            if debit_id.state != 'waiting':
                raise except_orm('Cảnh báo!', ('Đơn quản lý nợ hàng đang không ở trạng thái chờ kho! Vui lòng ấn "F5" để làm mới trình duyệt của bạn'))
            for line in debit_id.line_ids:
                line.qty_transfer = 0
            debit_id.state = 'debit'
        return picking

