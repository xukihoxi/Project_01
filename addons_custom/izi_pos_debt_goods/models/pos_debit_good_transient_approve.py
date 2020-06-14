# -*- coding: utf-8 -*-
from werkzeug._internal import _log
from odoo import models, fields, api
from odoo.exceptions import ValidationError
from odoo.tools.translate import _
from odoo.exceptions import except_orm, Warning as UserError
from odoo.exceptions import UserError


class DebitGoods(models.TransientModel):
    _name = "pos.debit.good.transient.approved"

    line_ids = fields.One2many('pos.debit.good.transient.approved.line', 'line_id',string="Line")
    debit_id = fields.Many2one('pos.debit.good')

    @api.multi
    def action_create_picking_approved(self):
        if len(self.line_ids) == 0:
            raise except_orm('Cảnh báo!', ('Không có thông tin trả hàng'))
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
    _name = "pos.debit.good.transient.approved.line"

    line_id = fields.Many2one('pos.debit.good.transient.approved')
    order_id = fields.Many2one('pos.order', string="Order")
    product_id = fields.Many2one('product.product', string="Product")
    qty_transfer = fields.Float(string='Quantity transfer')
    qty_debit = fields.Float(string='Quantity debit')
    debit_line_id = fields.Many2one('pos.debit.good.line')



