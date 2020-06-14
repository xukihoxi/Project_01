# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from datetime import datetime
from odoo.exceptions import MissingError, ValidationError, except_orm
from odoo.osv import osv


class SplitTotal(models.Model):
    _name = 'izi.product.split'
    _order = 'split_date desc'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char("Name", default="/", copy=False)
    state = fields.Selection(
        selection=(('draft', 'Draft'), ('to_confirm', 'To confirm'), ('confirm', 'Confirm'), ('done', 'Done'), ('cancel', 'Cancel')),
        default='draft',track_visibility='onchange')
    note = fields.Text("Note",track_visibility='onchange')
    split_date = fields.Date("Split date", required=True, default=datetime.now())
    warehouse_id = fields.Many2one('stock.warehouse', "Split at", required=True)
    splitting_lines = fields.One2many('izi.product.split.detail', 'split_total_id', "Splitting lines")
    picking_ids = fields.Many2many('stock.picking', string='Picking', readonly=True, copy=False)


    @api.model
    def create(self, vals):
        if vals.get('name', _('New')) == _('New'):
            vals['name'] = self.env['ir.sequence'].next_by_code('izi.product.split') or _('New')
        return super(SplitTotal, self).create(vals)

    @api.multi
    def unlink(self):
        for line in self:
            if line.state != 'draft':
                raise except_orm('Thông báo!', (
                    "Không thể xóa bản ghi ở trạng thái khác bản thảo"))
        return super(SplitTotal, self).unlink()

    @api.one
    def action_sent(self):
        detail = self.env['izi.product.split.detail'].search([('split_total_id','=',self.id)])
        for child_line in self.splitting_lines:
            i =0
            for detail_id in detail:
                if detail_id.product_id.id == child_line.product_id.id:
                    i = i+1
            if i > 1:
                raise except_orm('Cảnh báo!', ('Sản phẩm đem tách bị trùng lặp. Vui lòng kiểm tra lại!'))
            child_line.check_product()
            detail_line = self.env['izi.product.split.detail.line'].search([('splitting_id', '=', child_line.id)])
            for grand_son_line in child_line.out_put_product_lines:
                k = 0
                for detail_id in detail_line:
                    if detail_id.product_id.id == grand_son_line.product_id.id:
                        k = k + 1
                if k > 1:
                    raise except_orm('Cảnh báo!', ('Thành phẩm bạn chọn sau tách bị trùng lặp. Vui lòng kiểm tra lại!'))
                grand_son_line.check_product()
        self.validate_qty()
        self.state = 'to_confirm'

    @api.one
    def action_cancel(self):
        self.state = 'cancel'

    @api.one
    def action_confirm(self):
        self.state = 'confirm'

    @api.one
    def process_split_total(self):
        if self.state == 'done':
            return True
        self.validate_duplication()
        self.create_picking_out()
        self.create_picking_in()
        self.state = 'done'
        for child_line in self.splitting_lines:
            child_line.action_set_state()

    def validate_duplication(self):
        out_put_product_ids = []
        for child_line in self.splitting_lines:
            for grand_son_line in child_line.out_put_product_lines:
                if grand_son_line.product_id.id in out_put_product_ids:
                    raise except_orm("Hoạt động không được hỗ trợ",
                                     "Rất tiếc, hệ thống không hỗ trợ việc tách có trùng lặp sản phẩm thành phẩm "
                                     "trong các dòng. Xin hãy tách thành các phiếu tách riêng biệt.\n"
                                     "Sản phẩm trùng lặp: " + grand_son_line.product_id.name.encode('utf-8'))
                else:
                    out_put_product_ids.append(grand_son_line.product_id.id)

    # Không cho tách sản phẩm âm kho
    def _get_inventory(self, product_id, location_id):
        total_availability = self.env['stock.quant']._get_available_quantity(product_id, location_id)
        return total_availability
    def validate_qty(self):
        for child_line in self.splitting_lines:
            total_availability = self._get_inventory(child_line.product_id, self.warehouse_id.lot_stock_id)
            if total_availability < child_line.product_uom_qty:
                raise osv.except_osv("Không đủ hàng",
                                     _('Sản phẩm "%s" không đủ hàng \n'
                                       'SL trong kho "%s-%s": %s') % (
                                         child_line.product_id.name,  self.warehouse_id.lot_stock_id.x_code,  self.warehouse_id.lot_stock_id.name,
                                         total_availability))


    def _get_inventory_loss(self, product_id):
        if not product_id.property_stock_inventory:
            raise except_orm('Error!', 'Bạn phải cấu hình tài khoản kế toán cho sản phẩm')
        property_stock_inventory = product_id.property_stock_inventory.id
        cost_price = product_id.standard_price
        dict = {
            'property_stock_inventory': property_stock_inventory,
            'cost_price': cost_price
        }
        return dict

    def create_picking_out(self):
        stock_picking = self.env['stock.picking']
        picking_type_id = self.warehouse_id.x_outgoing_split_id
        if picking_type_id.id == False:
            raise except_orm('Cảnh báo!', (
                "Chưa cấu hình loại điều chuyển kho xuất tách. Vui lòng liên hệ quản trị viên !"))
        move_lines = []
        property_stock_inventory_list =[]
        for child_line in self.splitting_lines:
            product_vals = self._get_inventory_loss(child_line.product_id)
            property_stock_inventory = product_vals.get('property_stock_inventory')
            property_stock_inventory_list.append(property_stock_inventory)
            move_out_args = {
                'origin': self.name,
                'note': self.note,
                'product_id': child_line.product_id.id,
                'name': child_line.product_id.name,
                'product_uom': child_line.product_uom_id.id,
                'product_uom_qty': child_line.product_uom_qty,
                'quantity_done': child_line.product_uom_qty,
                'location_id': picking_type_id.default_location_src_id.id,
                'location_dest_id': property_stock_inventory,
                'price_unit': child_line.product_id.standard_price,
                'move_date': self.split_date
            }
            move_lines.append([0, False, move_out_args])
        picking_out_args = {
            'origin': self.name,
            'picking_type_id': picking_type_id.id,
            'move_lines': move_lines,
            'location_id': picking_type_id.default_location_src_id.id,
            'location_dest_id': property_stock_inventory_list[0],
            'date': self.split_date
        }
        new_picking = stock_picking.create(picking_out_args)
        new_picking.do_transfer()
        self.write({'picking_ids': [(4, new_picking.id)]})

    def create_picking_in(self):
        stock_picking = self.env['stock.picking']
        picking_type_id = self.warehouse_id.x_incoming_split_id
        if picking_type_id.id == False:
            raise except_orm('Cảnh báo!', (
                "Chưa cấu hình loại điều chuyển kho nhập tách. Vui lòng liên hệ quản trị viên !"))
        property_stock_inventory_list = []
        move_lines = []
        for child_line in self.splitting_lines:
            for grand_son_line in child_line.out_put_product_lines:
                product_vals = self._get_inventory_loss(grand_son_line.product_id)
                property_stock_inventory = product_vals.get('property_stock_inventory')
                property_stock_inventory_list.append(property_stock_inventory)
                move_in_args = {
                    'origin': self.name,
                    'note': self.note,
                    'product_id': grand_son_line.product_id.id,
                    'name': grand_son_line.product_id.name,
                    'product_uom': grand_son_line.product_uom_id.id,
                    'product_uom_qty': grand_son_line.product_uom_qty,
                    'quantity_done': grand_son_line.product_uom_qty,
                    'location_id': property_stock_inventory,
                    'location_dest_id': picking_type_id.default_location_dest_id.id,
                    'move_date': self.split_date
                }
                move_lines.append([0, False, move_in_args])
        picking_in_args = {
            'origin': self.name,
            'picking_type_id': picking_type_id.id,
            'move_lines': move_lines,
            'location_id': property_stock_inventory_list[0],
            'location_dest_id': picking_type_id.default_location_dest_id.id,
            'date': self.split_date
        }
        picking_in = stock_picking.create(picking_in_args)
        picking_in.do_transfer()
        self.write({'picking_ids': [(4, picking_in.id)]})





