# -*- coding: utf-8 -*-
from werkzeug._internal import _log
from odoo import models, fields, api
from odoo.exceptions import ValidationError
from odoo.tools.translate import _
from odoo.exceptions import except_orm, Warning as UserError



class DebitGoods(models.TransientModel):
    _name = "pos.debit.good.transient"

    line_ids = fields.One2many('pos.debit.good.transient.line', 'line_id',string="Line")
    debit_id = fields.Many2one('pos.debit.good')

    def action_check_picking(self, line_ids, debit_ids):
        # Ngoan thêm hạn mức ghi nợ để xuất hàng
        amount = 0
        to_debt = 0
        amount_payment = 0
        amount_service = 0
        # Ngoan sửa hạn mức xuất hàng cần xuất hàng
        for line_order in self.line_ids:
            pos_config_id = self.env['pos.config'].search([('id', '=', line_order.order_id.user_id.x_pos_config_id.id)])
            # tính toán công nợ đã thanh toán cho đơn hàng này
            obj_account_invoice = self.env['account.invoice'].search(
                [('partner_id', '=', self.debit_id.partner_id.id),
                 ('origin', '=', line_order.order_id.name)])
            if len(obj_account_invoice)>0:
                amount_payment = obj_account_invoice[0].amount_total - obj_account_invoice[0].residual
            for line in line_order.order_id.statement_ids:
                if len(pos_config_id) > 0:
                    for line3 in pos_config_id.journal_debt_id:
                        if line.journal_id.id == line3.id:
                            obj_order_line = self.env['pos.order.line'].search(
                                [('order_id', '=', line_order.order_id.id)])
                            amount = 0
                            for line2 in obj_order_line:
                                # tính số tiền đã xuất và yêu cầu xuất lúc này
                                obj_product = self.env['product.template'].search(
                                    [('id', '=', line2.product_id.product_tmpl_id.id), ('type', '=', 'product')])
                                if len(obj_product) > 0:
                                    debit_product_line = self.env['pos.debit.good.line'].search(
                                        [('order_id', '=', line_order.order_id.id),
                                         ('product_id', '=', line2.product_id.id)])
                                    if line_order.qty_transfer > 0 and line_order.product_id.id == line2.product_id.id:
                                        amount = amount + ((line2.price_unit * (1 - line2.discount / 100)) * (
                                                    debit_product_line.qty_depot + line_order.qty_transfer)) - line2.x_discount
                                # tính toán số tiền dịch vụ đã sử dụng cho đơn xuất hàng này
                                if line2.lot_name:
                                    obj_product_lot = self.env['stock.production.lot'].search([('name', '=', line2.lot_name)])
                                    obj_sevice_detail = self.env['izi.service.card.detail'].search(
                                        [('lot_id', '=', obj_product_lot[0].id)])
                                    for line_detail in obj_sevice_detail:
                                        amount_service += line_detail.qty_use * line_detail.price_unit
            if len(obj_account_invoice)>0 and obj_account_invoice[0].residual > 0:
                to_debt += amount_payment - amount - amount_service
            else:
                to_debt = 0
        return to_debt

    @api.multi
    def action_create_picking(self):
        debit = self.action_check_picking(self.line_ids, self.debit_id)
        if debit < 0:
            self.debit_id.state = 'approved'
        else:
            Picking = self.env['stock.picking']
            Move = self.env['stock.move']
            picking_type_id = self.env.user.x_pos_config_id.picking_type_id
            picking_vals = {
                'origin': self.debit_id.name,
                'partner_id': self.debit_id.partner_id.id,
                'scheduled_date': fields.Datetime.now(),
                'picking_type_id': picking_type_id.id,
                'move_type': 'direct',
                'note': 'Return goods',
                'location_id': picking_type_id.default_location_src_id.id,
                'location_dest_id': picking_type_id.default_location_dest_id.id,
            }
            picking_id = Picking.create(picking_vals)
            for line in self.line_ids:
                if line.qty_transfer == 0:
                    raise except_orm('Cảnh báo!', ('Tồn tại bản ghi chưa nhập số lượng trả'))
                if line.qty_transfer > line.qty_debit:
                    raise except_orm('Cảnh báo!', ('Tồn tại bản ghi có số lượng trả lớn hơn số lượng KH đã mua'))
                Move.create({
                    'name': line.order_id.name,
                    'product_uom': line.product_id.uom_id.id,
                    'picking_id': picking_id.id,
                    'picking_type_id': picking_type_id.id,
                    'product_id': line.product_id.id,
                    'product_uom_qty': line.qty_transfer,
                    'state': 'draft',
                    'location_id': picking_type_id.default_location_src_id.id,
                    'location_dest_id': picking_type_id.default_location_dest_id.id,
                })
                line.debit_line_id.qty_transfer = line.qty_transfer
            picking_id.action_confirm()
            self.debit_id.picking_id = picking_id.id
            self.debit_id.state = 'waiting'

class DebitGoodsLine(models.TransientModel):
    _name = "pos.debit.good.transient.line"

    line_id = fields.Many2one('pos.debit.good.transient')
    order_id = fields.Many2one('pos.order', string="Order")
    product_id = fields.Many2one('product.product', string="Product")
    qty_transfer = fields.Float(string='Quantity transfer')
    qty_debit = fields.Float(string='Quantity debit')
    debit_line_id = fields.Many2one('pos.debit.good.line')


