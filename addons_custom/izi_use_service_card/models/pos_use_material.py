# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import except_orm
from datetime import datetime, date


class PosUserMaterial(models.Model):
    _name = 'pos.user.material'
    _order = 'date desc, id desc'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    # _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char("Name", default='/', track_visibility='onchange')
    date = fields.Date("Date", track_visibility='onchange')
    employee_ids = fields.Many2many('hr.employee', string="Employee", track_visibility='onchange')
    origin = fields.Char("Origin", track_visibility='onchange')
    using_service_id = fields.Many2one('izi.service.card.using', "Using service", track_visibility='onchange')
    state = fields.Selection([('draft', "Draft"), ('wait_material', "Wait Material"), ('wait_confirm', "Wait Confirm"),
                              ('exported', "Exported"), ('adjust', "Adjust"), ('done', "Done"), ('cancel', "Cancel")],
                             default='draft', track_visibility='onchange')
    use_move_line_ids = fields.One2many('izi.using.stock.move.line', 'use_material_id', "Use Move Line")
    adjust_active = fields.Boolean('Adjust Active', default=False, track_visibility='onchange')
    picking_id = fields.Many2one('stock.picking', "Picking", track_visibility='onchange')
    check_send = fields.Boolean("Check send", default=False)
    type = fields.Selection([('output', "OutPut"), ('input', "Input")], default='output', track_visibility='onchange')
    customer_id = fields.Many2one('res.partner', "Customer", track_visibility='onchange')
    service_ids = fields.Many2many('product.product', string="Service", track_visibility='onchange')
    quantity = fields.Float("Quantity")
    src_location = fields.Many2one('stock.location', "Location")
    picking_type_id = fields.Many2one('stock.picking.type', "Stock Picking Type")
    force_available_active = fields.Boolean('Force Available Active', default=False)
    type_service = fields.Selection([('spa', "Spa"), ('clinic', "Clinic"), ('guarantee_spa', "Guarantee Spa"), ('guarantee_clinic', "Guaranteee Clinic")], default='spa')


    @api.model
    def create(self, vals):
        if vals.get('name', _('New')) == _('New'):
            vals['name'] = self.env['ir.sequence'].next_by_code('pos.user.material') or _('New')
        return super(PosUserMaterial, self).create(vals)

    @api.multi
    def unlink(self):
        for line in self:
            if line.state != 'draft':
                raise except_orm('Cảnh báo!', ("Không thể xoa khi ở trang thái khác nháp"))
        super(PosUserMaterial, self).unlink()

    @api.multi
    def action_set_default_value(self):
        for line in self.use_move_line_ids:
            if line.replace_material_id:
                continue
            line.quantity_used = line.quantity

    @api.multi
    def action_create_picking(self):
        stock_move_obj = self.env['stock.move']
        stock_location = self.env['stock.location']
        customer_location = stock_location.sudo().search([('usage', '=', 'customer')])[0]
        if not self.using_service_id.pos_session_id.config_id.x_material_picking_type_id:
            raise except_orm("Cảnh báo!", ("Vui long kiểm tra lại lý do xuất kho làm dịch vụ"))
        if not self.using_service_id.pos_session_id.config_id.x_cosmetic_surgery_picking_type:
            raise except_orm("Cảnh báo!", ("Vui long kiểm tra lại lý do xuất kho phẫu thuật thẩm mỹ"))
        src_location = self.using_service_id.pos_session_id.config_id.x_material_picking_type_id.default_location_src_id
        src_location_pttm = self.using_service_id.pos_session_id.config_id.x_cosmetic_surgery_picking_type.default_location_src_id
        if not src_location:
            raise except_orm('Cảnh báo!', ("Có thể bạn chưa tạo kho hàng làm. Vui lòng kiểm tra lại"))
        if not src_location_pttm:
            raise except_orm('Cảnh báo!',
                             ("Có thể bạn chưa tạo kho hàng phẫu thuật thẩm mỹ. Vui lòng kiểm tra lại"))
        if not self.picking_id:
            picking_id = self._create_picking(self.picking_type_id.id,
                                              customer_location.id, self.picking_type_id.default_location_src_id.id)
            for tmp in self.use_move_line_ids:
                if tmp.use == False:
                    continue
                if tmp.replace_material_id:
                    if tmp.quantity_replace == 0:
                        continue
                    move_vals = {
                        'name': tmp.replace_material_id.name,
                        'product_id': tmp.replace_material_id.id,
                        'product_uom': tmp.uom_replace_id.id,
                        'product_uom_qty': tmp.quantity_replace,
                        'quantity_done': tmp.quantity_replace,
                        'location_id': self.picking_type_id.default_location_src_id.id,
                        'location_dest_id': customer_location.id,
                        'date': self.date,
                        'picking_type_id': self.picking_type_id.id,
                        'origin': self.name,
                        'picking_id': picking_id.id,

                    }
                    stock_move_id = stock_move_obj.create(move_vals)
                else:
                    if tmp.quantity_used == 0:
                        continue
                    move_vals = {
                        'name': tmp.material_id.name,
                        'product_id': tmp.material_id.id,
                        'product_uom': tmp.uom_id.id,
                        'product_uom_qty': tmp.quantity_used,
                        'quantity_done': tmp.quantity_used,
                        'location_id': self.picking_type_id.default_location_src_id.id,
                        'location_dest_id': customer_location.id,
                        'date': self.date,
                        'picking_type_id': self.picking_type_id.id,
                        'origin': self.name,
                        'picking_id': picking_id.id,

                    }
                    stock_move_id = stock_move_obj.create(move_vals)
            self.picking_id = picking_id.id
        else:
            self.picking_id.do_unreserve()
            list = []
            move_obj = self.env['stock.move'].search(
                [('picking_id', '=', self.picking_id.id)])
            for object in move_obj:
                list.append(object.product_id.id)
            for line2 in self.use_move_line_ids:
                if line2.material_id.id in list:
                    obj_move1 = self.env['stock.move'].search(
                        [('product_id', '=', line2.material_id.id), ('picking_id', '=', self.picking_id.id)])
                    if line2.quantity_used != obj_move1[0].product_uom_qty:
                        obj_move1[0].quantity_done += line2.quantity_used - obj_move1[0].quantity_done
                        obj_move1[0].product_uom_qty +=line2.quantity_used - obj_move1[0].product_uom_qty
                    else:
                        obj_move1[0].quantity_done = line2.quantity_used
                        obj_move1[0].product_uom_qty = line2.quantity_used
                if line2.replace_material_id.id in list:
                    obj_move2 = self.env['stock.move'].search(
                        [('product_id', '=', line2.replace_material_id.id), ('picking_id', '=', self.picking_id.id)])
                    if line2.quantity_replace != obj_move2[0].product_uom_qty:
                        obj_move2[0].quantity_done += line2.quantity_replace - obj_move2[0].quantity_done
                        obj_move2[0].product_uom_qty += line2.quantity_replace - obj_move2[0].product_uom_qty
                if line2.replace_material_id.id not in list and line2.quantity_replace > 0:
                    move_vals = {
                        'name': line2.replace_material_id.name,
                        'product_id': line2.replace_material_id.id,
                        'product_uom': line2.uom_replace_id.id,
                        'product_uom_qty': line2.quantity_replace,
                        'quantity_done': line2.quantity_replace,
                        'location_id': self.picking_type_id.default_location_src_id.id,
                        'location_dest_id': customer_location.id,
                        'date': self.date,
                        'picking_type_id': self.picking_type_id.id,
                        'origin': self.name,
                        'picking_id': self.picking_id.id,

                    }
                    stock_move_id = stock_move_obj.create(move_vals)
                if line2.material_id.id not in list and line2.quantity_used > 0 and line2.use == True:
                    move_vals = {
                        'name': line2.material_id.name,
                        'product_id': line2.material_id.id,
                        'product_uom': line2.uom_id.id,
                        'product_uom_qty': line2.quantity_used,
                        'quantity_done': line2.quantity_used,
                        'location_id': self.picking_type_id.default_location_src_id.id,
                        'location_dest_id': customer_location.id,
                        'date': self.date,
                        'picking_type_id': self.picking_type_id.id,
                        'origin': self.name,
                        'picking_id': self.picking_id.id,
                    }
                    stock_move_id = stock_move_obj.create(move_vals)
        if self.force_available_active == False:
            self.picking_id.action_confirm()
            self.picking_id.action_assign()
        else:
            # cưỡng bức đơn
            for move in self.picking_id.move_lines:
                move.quantity_done = move.product_uom_qty
            self.picking_id.action_assign()
    #
    @api.multi
    def action_confirm(self):
        if self.state not in ('draft', 'wait_material'):
            raise except_orm('Cảnh báo!', ("Trạng thái sử dụng dịch vụ đã thay đổi. Vui lòng F5 hoặc load lại trang"))
        self.state = 'wait_confirm'
        for line in self.use_move_line_ids:
            if line.use == True:
                if line.quantity_used == 0 and (line.quantity_replace == 0 or not line.replace_material_id):
                    raise except_orm('Cảnh báo!',
                                     ('Bạn phải nhập nguyên vật liệu thay thế cho những nguyên vật liệu không còn'))
                if line.quantity_replace == 0 and line.replace_material_id:
                    raise except_orm('Cảnh báo!',
                                     ('Bạn phải nhập số lượng cho nguyên vật liệu thay thế'))
                if line.quantity_replace != 0 and not line.replace_material_id:
                    raise except_orm('Cảnh báo!',
                                     ('Bạn không thể nhập số lượng khi không chọn sản phẩm thay thế'))
        count = 0
        for line in self.use_move_line_ids:
            if line.quantity_used > line.quantity:
                count += 1
            if line.replace_material_id:
                count += 1
        if count == 0:
            self.action_create_picking()
            self.state = 'exported'
            self.using_service_id.state = 'working'
            # self.using_service_id.with_context(izi=True).write({'state': 'working'})
            self.using_service_id.date_start = datetime.now()
            # SangsLA thêm ngày 3/10/2018 Thêm using_service vào form khi chung của khách hàng
            pos_sum_digital_obj = self.env['pos.sum.digital.sign'].search(
                [('partner_id', '=', self.customer_id.id), ('state', '=', 'draft'), ('session_id', '=',self.using_service_id.pos_session_id.id)])
            if pos_sum_digital_obj:
                self.using_service_id.update({'x_digital_sign_id': pos_sum_digital_obj.id})
            else:
                pos_sum_digital_obj = self.env['pos.sum.digital.sign'].create({
                    'partner_id': self.customer_id.id,
                    'state': 'draft',
                    'date': date.today(),
                    'session_id': self.using_service_id.pos_session_id.id,
                })
                self.using_service_id.update({'x_digital_sign_id': pos_sum_digital_obj.id})
            using_line = self.env['izi.service.card.using.line'].search([('using_id', '=', self.using_service_id.id)])

            for line in using_line:
                line.update({'x_digital_sign_id': pos_sum_digital_obj.id})
        else:
            self.state = 'wait_confirm'
            self.using_service_id.date_start = datetime.now()

    @api.multi
    def action_supervisor_confirm(self):
        if self.state != 'wait_confirm':
            raise except_orm('Cảnh báo!', ("Trạng thái sử dụng dịch vụ đã thay đổi. Vui lòng F5 hoặc load lại trang"))
        self.state = 'exported'
        self.action_create_picking()
        if self.adjust_active == False:
            self.state = 'exported'
            self.using_service_id.state = 'working'
            # SangsLA thêm ngày 3/10/2018 Thêm using_service vào form khi chung của khách hàng
            pos_sum_digital_obj = self.env['pos.sum.digital.sign'].search(
                [('partner_id', '=', self.customer_id.id), ('state', '=', 'draft'), ('session_id', '=', self.using_service_id.pos_session_id.id)])
            if pos_sum_digital_obj:
                self.using_service_id.update({'x_digital_sign_id': pos_sum_digital_obj.id})
            else:
                pos_sum_digital_obj = self.env['pos.sum.digital.sign'].create({
                    'partner_id': self.customer_id.id,
                    'state': 'draft',
                    'date': date.today(),
                    'session_id': self.using_service_id.pos_session_id.id,
                })
                self.using_service_id.update({'x_digital_sign_id': pos_sum_digital_obj.id})
            using_line = self.env['izi.service.card.using.line'].search([('using_id', '=', self.using_service_id.id)])

            for line in using_line:
                line.update({'x_digital_sign_id': pos_sum_digital_obj.id})
        #         hết
        else:
            # SangsLA thêm ngày 3/10/2018 Thêm using_service vào form khi chung của khách hàng
            pos_sum_digital_obj = self.env['pos.sum.digital.sign'].search(
                [('partner_id', '=', self.customer_id.id), ('state', '=', 'draft'),
                 ('session_id', '=', self.using_service_id.pos_session_id.id)])
            if pos_sum_digital_obj:
                self.using_service_id.update({'x_digital_sign_id': pos_sum_digital_obj.id})
            else:
                pos_sum_digital_obj = self.env['pos.sum.digital.sign'].create({
                    'partner_id': self.customer_id.id,
                    'state': 'draft',
                    'date': date.today(),
                    'session_id': self.using_service_id.pos_session_id.id,
                })
                self.using_service_id.update({'x_digital_sign_id': pos_sum_digital_obj.id})
            using_line = self.env['izi.service.card.using.line'].search([('using_id', '=', self.using_service_id.id)])

            for line in using_line:
                line.update({'x_digital_sign_id': pos_sum_digital_obj.id})
            #         hết
            self.action_done()

    @api.multi
    def action_adjust(self):
        if self.state != 'exported':
            raise except_orm('Cảnh báo!', ("Trạng thái sử dụng dịch vụ đã thay đổi. Vui lòng F5 hoặc load lại trang"))
        self.state = 'adjust'
        self.adjust_active = True

    @api.multi
    def action_confirm_adjust(self):
        if self.state != 'adjust':
            raise except_orm('Cảnh báo!', ("Trạng thái sử dụng dịch vụ đã thay đổi. Vui lòng F5 hoặc load lại trang"))
        self.state = 'wait_confirm'
        for line in self.use_move_line_ids:
            if line.use == True:
                if line.quantity_used == 0 and (line.quantity_replace == 0 or not line.replace_material_id):
                    raise except_orm('Cảnh báo!',
                                     ('Bạn phải nhập nguyên vật liệu thay thế cho những nguyên vật liệu không còn'))
                if line.quantity_replace == 0 and line.replace_material_id:
                    raise except_orm('Cảnh báo!',
                                     ('Bạn phải nhập số lượng cho nguyên vật liệu thay thế'))
                if line.quantity_replace != 0 and not line.replace_material_id:
                    raise except_orm('Cảnh báo!',
                                     ('Bạn không thể nhập số lượng khi không chọn sản phẩm thay thế'))
        self.state = 'wait_confirm'

    @api.multi
    def action_done(self):
        if self.state == 'done':
            raise except_orm("Cảnh báo",
                             ("Đơn yêu cầu nguyên vật liệu đã thay đổi trạng thái. Bạn cần F5 hoặc tải lại trạng thái"))
        else:
            pick = self.picking_id
            res_dict = pick.button_validate()
            #pick khác so với số lượng yêu cầu
            if pick.state != 'done':
                wizard = self.env[(res_dict.get('res_model'))].browse(res_dict.get('res_id'))
                wizard.process_cancel_backorder()
                self.state = 'done'
            else:
                self.state = 'done'

    @api.multi
    def action_back(self):
        if self.state != 'wait_confirm':
            raise except_orm("Cảnh báo",
                             ("Đơn yêu cầu nguyên vật liệu đã thay đổi trạng thái. Bạn cần F5 hoặc tải lại trạng thái"))
        self.state = 'draft'
        if self.adjust_active == False:
            self.state = 'draft'
        else:
            self.state = 'adjust'

    @api.multi
    def force_available(self):
        if self.adjust_active == False:
            for line in self.use_move_line_ids:
                if line.use == True:
                    if line.quantity_used == 0 and (line.quantity_replace == 0 or not line.replace_material_id):
                        raise except_orm('Cảnh báo!',
                                         ('Bạn phải nhập nguyên vật liệu thay thế cho những nguyên vật liệu không còn'))
                    if line.quantity_replace == 0 and line.replace_material_id:
                        raise except_orm('Cảnh báo!',
                                         ('Bạn phải nhập số lượng cho nguyên vật liệu thay thế'))
                    if line.quantity_replace != 0 and not line.replace_material_id:
                        raise except_orm('Cảnh báo!',
                                         ('Bạn không thể nhập số lượng khi không chọn sản phẩm thay thế'))
        count = 0
        for line in self.use_move_line_ids:
            if line.quantity_used > line.quantity:
                count += 1
            if line.replace_material_id:
                count += 1
        if count == 0:
            self.action_create_picking()
            self.state = 'exported'
            self.using_service_id.state = 'working'
            # self.using_service_id.with_context(izi=True).write({'state': 'working'})
            self.using_service_id.date_start = datetime.now()
            # SangsLA thêm ngày 3/10/2018 Thêm using_service vào form khi chung của khách hàng
            pos_sum_digital_obj = self.env['pos.sum.digital.sign'].search(
                [('partner_id', '=', self.customer_id.id), ('state', '=', 'draft'), ('session_id', '=', self.using_service_id.pos_session_id.id)])
            if pos_sum_digital_obj:
                self.using_service_id.update({'x_digital_sign_id': pos_sum_digital_obj.id})
            else:
                pos_sum_digital_obj = self.env['pos.sum.digital.sign'].create({
                    'partner_id': self.customer_id.id,
                    'state': 'draft',
                    'date': date.today(),
                    'session_id': self.using_service_id.pos_session_id.id,
                })
                self.using_service_id.update({'x_digital_sign_id': pos_sum_digital_obj.id})
            using_line = self.env['izi.service.card.using.line'].search([('using_id', '=', self.using_service_id.id)])

            for line in using_line:
                line.update({'x_digital_sign_id': pos_sum_digital_obj.id})
        #         hết
        else:
            self.state = 'wait_confirm'
            self.using_service_id.date_start = datetime.now()

    @api.multi
    def check_available(self):
        list = []
        src_location = self.picking_type_id.default_location_src_id
        amount = 0
        for line in self.use_move_line_ids:
            amount += line.quantity_used + line.quantity_replace
        if amount == 0:
            raise except_orm('Cảnh báo!', "Bạn phải nhập số lượng sử dụng sử dụng")
        if self.picking_id.id:
            obj_stock_move = self.env['stock.move'].search([('picking_id', '=', self.picking_id.id)])
            for line_move in obj_stock_move:
                list.append(line_move.product_id.id)
        for line in self.use_move_line_ids:
            if self.picking_id.id:
                if line.material_id.id in list and line.use == True and line.quantity_used > 0:
                    qty_avai = line._get_inventory(line.material_id, src_location)
                    line.quantity_remain_stock = qty_avai
                    move = self.env['stock.move'].search(
                        [('product_id', '=', line.material_id.id), ('picking_id', '=', self.picking_id.id)])
                    if line.quantity_used <= qty_avai or move.reserved_availability >= line.quantity_used or line.quantity_used <= move.reserved_availability + qty_avai:
                        line.state = 'ready'
                    else:
                        line.state = 'stock_out'
                elif line.material_id.id not in list and line.use == True and line.quantity_used > 0:
                    # if line.quantity_used == 0:
                    #     raise except_orm('Cảnh báo!', "Bạn phải nhập số lượng sử dụng sử dụng")
                    qty_avai = line._get_inventory(line.material_id, src_location)
                    line.quantity_remain_stock = qty_avai
                    if line.quantity_used > qty_avai:
                        line.state = 'stock_out'
                    else:
                        line.state = 'ready'
                elif line.replace_material_id.id in list and line.quantity_replace > 0 and line.use == True:
                    # if line.quantity_replace == 0:
                    #     raise except_orm('Cảnh báo!', "Bạn phải nhập số lượng sử dụng sử dụng")
                    qty_avai = line._get_inventory(line.replace_material_id, src_location)
                    line.quantity_remain_stock_replace = qty_avai
                    move = self.env['stock.move'].search(
                        [('product_id', '=', line.replace_material_id.id), ('picking_id', '=', self.picking_id.id)])
                    if line.quantity_replace <= qty_avai or move.reserved_availability >= line.quantity_replace or line.quantity_replace <= move.reserved_availability + qty_avai:
                        line.state = 'ready'
                    else:
                        line.state = 'stock_out'
                elif line.replace_material_id.id not in list and line.use == True and line.quantity_replace > 0:
                    # if line.quantity_replace == 0:
                    #     raise except_orm('Cảnh báo!', "Bạn phải nhập số lượng sử dụng sử dụng")
                    qty_avai = line._get_inventory(line.replace_material_id, src_location)
                    line.quantity_remain_stock_replace = qty_avai
                    if line.quantity_replace > qty_avai:
                        line.state = 'stock_out'
                    else:
                        line.state = 'ready'
            else:
                qty_avai = 0
                if line.replace_material_id.id == False:
                    # if line.quantity_used == 0:
                    #     raise except_orm('Cảnh báo!', "Bạn phải nhập số lượng sử dụng sử dụng")
                    qty_avai = line._get_inventory(line.material_id, src_location)
                    line.quantity_remain_stock = qty_avai
                    if line.quantity_used > qty_avai:
                        line.state = 'stock_out'
                    else:
                        line.state = 'ready'
                else:
                    # if line.quantity_replace == 0:
                    #     raise except_orm('Cảnh báo!', "Bạn phải nhập số lượng sử dụng sử dụng")
                    qty_avai = line._get_inventory(line.replace_material_id, src_location)
                    line.quantity_remain_stock_replace = qty_avai
                    if line.quantity_replace > qty_avai:
                        line.state = 'stock_out'
                    else:
                        line.state = 'ready'
        for line in self.use_move_line_ids:
            if line.state != 'ready':
                self.state = 'wait_material'
                self.check_send = False
                self.force_available_active = True
                break
            else:
                self.check_send = True

    @api.multi
    def action_confirm_cancel(self):
        if self.state != 'exported':
            raise except_orm('Cảnh báo!', ("Trạng thái sử dụng dịch vụ đã thay đổi. Vui lòng F5 hoặc load lại trang"))
        self.state = 'done'
        count_use = 0
        if len(self.use_move_line_ids) > 0:
            for line in self.use_move_line_ids:
                if line.use == True:
                    count_use +=1
        if count_use != 0:
            stock_move_obj = self.env['stock.move']
            # self.state = 'done'
            stock_location = self.env['stock.location']
            customer_location = stock_location.sudo().search([('usage', '=', 'customer')])[0]
            if not self.using_service_id.pos_session_id.config_id.x_material_picking_type_id.return_picking_type_id:
                raise except_orm("Cảnh báo!", ("Vui lòng kiểm tra lại lý do nhập kho"))
            src_location = self.picking_type_id.return_picking_type_id.default_location_dest_id
            if not src_location:
                raise except_orm('Cảnh báo!', ("Có thể bạn chưa tạo kho hàng làm. Vui lòng kiểm tra lại"))

            picking_id = self._create_picking(self.picking_type_id.return_picking_type_id.id, src_location.id,
                                              customer_location.id)
            for line in self.use_move_line_ids:
                if line.use == False:
                    continue
                if line.replace_material_id:
                    move_obj = self.env['stock.move'].search(
                        [('picking_id', '=', picking_id.id), ('product_id', '=', line.replace_material_id.id)])
                    if move_obj:
                        move_obj.product_uom_qty += line.quantity_replace
                        move_obj.quantity_done += line.quantity_replace
                    else:
                        if line.quantity_replace == 0:
                            continue
                        move_vals = {
                            'name': line.replace_material_id.name,
                            'product_id': line.replace_material_id.id,
                            'product_uom': line.uom_replace_id.id,
                            'product_uom_qty': line.quantity_replace,
                            'quantity_done': line.quantity_replace,
                            'location_id': customer_location.id,
                            'location_dest_id': src_location.id,
                            'date': self.date,
                            'picking_type_id': self.picking_type_id.return_picking_type_id.id,
                            'origin': self.using_service_id.name,
                            'picking_id': picking_id.id,

                        }
                        stock_move_id = stock_move_obj.create(move_vals)
                else:
                    move_obj = self.env['stock.move'].search(
                        [('picking_id', '=', picking_id.id), ('product_id', '=', line.material_id.id)])
                    if move_obj:
                        move_obj.product_uom_qty += line.quantity_used
                        move_obj.quantity_done += line.quantity_used
                    else:
                        if line.quantity_used == 0:
                            continue
                        move_vals = {
                            'name': line.material_id.name,
                            'product_id': line.material_id.id,
                            'product_uom': line.uom_id.id,
                            'product_uom_qty': line.quantity_used,
                            'quantity_done': line.quantity_used,
                            'location_id': customer_location.id,
                            'location_dest_id': src_location.id,
                            'date': self.date,
                            'picking_type_id': self.picking_type_id.return_picking_type_id.id,
                            'origin': self.using_service_id.name,
                            'picking_id': picking_id.id,

                        }
                        stock_move_id = stock_move_obj.create(move_vals)
            self.picking_id = picking_id.id
            picking_id.action_confirm()
            picking_id.action_assign()
            picking_id.button_validate()

        count = 0
        for line in self.using_service_id.use_material_ids:
            if line.state != 'done':
                count += 1
        if count == 0:
            self.using_service_id.state = 'cancel'

    @api.multi
    def _create_picking(self, picking_type_id, location_dest_id, location_id):
        StockPicking = self.env['stock.picking']
        res = self._prepare_picking(picking_type_id, location_dest_id, location_id)
        picking = StockPicking.create(res)
        return picking

    @api.model
    def _prepare_picking(self, picking_type_id, location_dest_id, location_id):
        user_id = self.env['res.users'].search([('id', '=', self.env.uid)])
        return {
            'picking_type_id': picking_type_id,
            'partner_id': self.using_service_id.customer_id.id,
            'date': self.date,
            'origin': self.name,
            'location_dest_id': location_dest_id,
            'location_id': location_id,
            'company_id': user_id.company_id.id
        }

    @api.multi
    def action_send_wait_material(self):
        self.state = 'wait_material'

    @api.multi
    def action_request_material(self):
        if self.env.context is None:
            context = {}
        ctx = self.env.context.copy()
        ctx.update({'default_using_service_id': self.using_service_id.id,
                    'default_customer_id': self.customer_id.id,
                    'default_date': datetime.now().date(),
                    'default_origin': self.name
                    })
        # view = self.env.ref('izi_use_service_card.pos_request_materia_action_form')
        return {
            'name': _('Request Material'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'pos.request.material',
            'views': [(False, 'form')],
            'target': 'new',
            'context': ctx,
        }

    @api.multi
    def action_done_not_product(self):
        if len(self.use_move_line_ids) > 0:
            for line in self.use_move_line_ids:
                if line.use == True:
                    raise except_orm("Thông báo!", ('Có NVL vui lòng xuất kho'))
        # SangsLA thêm ngày 3/10/2018 Thêm using_service vào form khi chung của khách hàng
        pos_sum_digital_obj = self.env['pos.sum.digital.sign'].search(
            [('partner_id', '=', self.customer_id.id), ('state', '=', 'draft'),
             ('session_id', '=', self.using_service_id.pos_session_id.id)])
        if pos_sum_digital_obj:
            self.using_service_id.update({'x_digital_sign_id': pos_sum_digital_obj.id})
        else:
            pos_sum_digital_obj = self.env['pos.sum.digital.sign'].create({
                'partner_id': self.customer_id.id,
                'state': 'draft',
                'date': date.today(),
                'session_id': self.using_service_id.pos_session_id.id,
            })
            self.using_service_id.update({'x_digital_sign_id': pos_sum_digital_obj.id})
        using_line = self.env['izi.service.card.using.line'].search(
            [('using_id', '=', self.using_service_id.id)])

        for line in using_line:
            line.update({'x_digital_sign_id': pos_sum_digital_obj.id})
        #         hết
        self.state = 'done'
        self.using_service_id.state = 'working'
        self.using_service_id.date_start = datetime.now()