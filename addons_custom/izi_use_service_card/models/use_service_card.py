# -*- coding: utf-8 -*-
from reportlab.graphics.barcode.common import Barcode

from odoo import models, fields, api, _
from datetime import datetime, timedelta, date
from odoo.exceptions import except_orm, ValidationError, UserError
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT
import math
import copy


class ServiceCardUsing(models.Model):
    _name = "izi.service.card.using"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = "id desc"

    def _default_pos_session(self):
        pos_session = self.env['pos.session']
        pos_config_id = self.env.user.x_pos_config_id.id
        my_session = pos_session.search([('config_id', '=', pos_config_id), ('state', '=', 'opened')])
        if not my_session:
            return False
        else:
            return my_session.id

    name = fields.Char("Name", default='/', copy=False)
    serial_code = fields.Char("Serial Code", track_visibility='onchange', copy=False)
    redeem_date = fields.Datetime("Redeem Date", default=fields.Datetime.now, track_visibility='onchange', copy=False)
    customer_id = fields.Many2one('res.partner', "Customer", track_visibility='onchange')
    pricelist_id = fields.Many2one('product.pricelist', "Pricelist", track_visibility='onchange')
    state = fields.Selection([('draft', "Draft"),('wait_payment', "Wait Payment"),('wait_approve', "Wait Approve"), ('wait_material', "Wait Material"),
                              ('working', "Working"), ('rate', "Rate"), ('done', "Done"),
                              ('wait_confirm', "Wait Confirm"), ('wait_delivery', "Wait Delivery"),
                              ('cancel', "Cancel")], default='draft', track_visibility='onchange', copy=False)
    service_card_ids = fields.One2many('izi.service.card.using.line', 'using_id', "Service Card", copy=False)
    use_material_ids = fields.One2many('pos.user.material', 'using_service_id', "Use Material", copy=False)
    old_image_ids = fields.One2many('izi.images', 'old_service_card_id', string='Image', copy=False)
    old_image_note = fields.Text("Note", copy=False)
    new_image_ids = fields.One2many('izi.images', 'new_service_card_id', string='Image', copy=False)
    new_image_note = fields.Text("Note", copy=False)
    type = fields.Selection([('service', "Service"), ('card', "Card"), ('guarantee', "Guarantee")], default='card', required=1)
    pos_payment_service_ids = fields.One2many('pos.payment.service', 'using_service_id', "Pos Payment Service", copy=False)
    rank_id = fields.Many2one('crm.vip.rank', "Rank", track_visibility='onchange')
    service_card1_ids = fields.One2many('izi.service.card.using.line', 'using_id', "Service Card", copy=False)
    pos_order_id = fields.Many2one('pos.order', "Pos Order", track_visibility='onchange', copy=False)
    pos_order_refund_id = fields.Many2one('pos.order', "Pos Order Refund", track_visibility='onchange', copy=False)
    date_start = fields.Datetime("Date Start", track_visibility='onchange', copy=False)
    date_end = fields.Datetime("Date End", track_visibility='onchange', copy=False)
    signature_image = fields.Binary("Signature Image", default=False, attachment=True, track_visibility='onchange', copy=False)
    pending = fields.Boolean('Pending', default=False, track_visibility='onchange', copy=False)
    pending_note = fields.Text("Pending Text", track_visibility='onchange', copy=False)
    amount_total = fields.Float("Amount Total", compute='_compute_amount_total', copy=False)
    user_id = fields.Many2one('res.users', "User", default=lambda self: self.env.uid)
    pos_session_id = fields.Many2one('pos.session', "Pos Session", default=_default_pos_session)
    debt_amount = fields.Float('Debt Amount', compute='_compute_amount', copy=False)
    payment_amount = fields.Float("Payment Amount", compute='_compute_amount', copy=False)
    option_refund = fields.Selection([('cancel', "Cancel"), ('refund', "Refund")], copy=False)
    note = fields.Text("Note", copy=False)
    product_ids = fields.Many2many('product.product', 'use_service_product_rel', 'use_service_id', 'product_id',
                                   'Product', copy=False)
    merge = fields.Boolean("Merge", default=True, copy=False)
    rate_content = fields.Text(string="Rate content")
    # Sangla thêm ngày 23/10/2018 them chọn khách hàng ra số điện thoại để seach
    partner_search_id = fields.Many2one('res.partner', "Partner Search")

    def get_service_card_detail(self):
        list_service_card_details = []
        service_card_details = self.env['izi.service.card.detail'].search([('lot_id.x_customer_id', '=', self.customer_id.id)])
        if service_card_details:
            for service_card_detail in service_card_details:
                if service_card_detail.state == 'ready':
                    state = 'Sẵn sàng'
                elif service_card_detail.state == 'cancel':
                    state = 'Hủy'
                else:
                    state = service_card_detail.state
                date = datetime.strptime(service_card_detail.lot_id.life_date, '%Y-%m-%d %H:%M:%S') + timedelta(days=1)
                day_now = datetime.today().replace(minute=0, hour=0, second=0)
                if date < day_now:
                    state = 'Hết hạn'
                list_service_card_details.append({
                    'card_name': service_card_detail.lot_id.name,
                    'service_code': service_card_detail.product_id.default_code,
                    'service_name': service_card_detail.product_id.name,
                    'total_qty': service_card_detail.total_qty,
                    'qty_hand': service_card_detail.qty_hand,
                    'qty_use': service_card_detail.qty_use,
                    'state': state,
                })
        return list_service_card_details

    def get_use_service_history(self):
        use_service_histories = []
        services_card_using = self.env['izi.service.card.using'].search([('customer_id', '=', self.customer_id.id)])
        for service_card_using in services_card_using:
            services_card_using_lines = self.env['izi.service.card.using.line'].search([('using_id', '=', service_card_using.id)])
            for services_card_using_line in services_card_using_lines:
                employee = ''
                doctor = ''
                for x in services_card_using_line.employee_ids:
                    employee = employee + ', ' + str(x.name)
                for y in services_card_using_line.doctor_ids:
                    doctor = doctor + ', ' + str(y.name)
                use_service_history = {
                    'redeem_date': services_card_using_line.using_id.redeem_date,
                    'service_name': services_card_using_line.service_id.name,
                    'service_code': services_card_using_line.service_id.default_code,
                    'quantity': services_card_using_line.quantity,
                    'uom_id': services_card_using_line.uom_id.id,
                    'employee': employee[1:],
                    'doctor': doctor[1:],
                    'using_name': services_card_using_line.using_id.name,
                    'serial_id': services_card_using_line.serial_id.id,
                    'price_unit': services_card_using_line.price_unit,
                    'state': services_card_using_line.using_id.state,
                    'x_search_id': self.id,
                    'customer_sign': services_card_using_line.using_id.signature_image,
                    'note': services_card_using_line.note,
                    'type': 'card',
                }
                use_service_histories.append(use_service_history)
        return use_service_histories

    def _check_service_card_ids_service_card1_ids(self):
        for service_card in self.service_card_ids:
            if service_card.service_id.x_use_doctor and not service_card.doctor_ids and service_card.quantity != 0:
                raise ValidationError('Dịch vụ [%s]%s phải chọn bác sĩ!' % (str(service_card.service_id.default_code), str(service_card.service_id.name)))

        for service_card1 in self.service_card1_ids:
            if service_card1.service_id.x_use_doctor and not service_card1.doctor_ids and service_card1.quantity != 0:
                raise ValidationError('Dịch vụ [%s]%s phải chọn bác sĩ!' % (str(service_card1.service_id.default_code), str(service_card1.service_id.name)))

    @api.model
    def default_get(self, fields):
        res = super(ServiceCardUsing, self).default_get(fields)
        if not self._context.get('inventory_update', False):
            current_session = self.env['pos.session'].search(
                [('state', '!=', 'closed'), ('config_id', '=', self.env.user.x_pos_config_id.id)], limit=1)
            if not current_session:
                raise except_orm(("Cảnh báo!"), ('Bạn phải mở phiên trước khi tạo đơn hàng mới.'))
        return res

    @api.onchange('type')
    def onchange_type(self):
        if self.type == 'service':
            self.service_card1_ids = False
            self.service_card_ids = False
        elif self.type == 'guarantee':
            self.service_card1_ids = False
            self.service_card_ids = False
        else:
            #ngoannt them doan onchange dich vụ khách hàng đang có
            if self.customer_id is not None and self.customer_id:
                self.serial_code = self.customer_id.phone
                self.action_search_serial()
            else:
                self.service_card_ids = False

    @api.onchange('partner_search_id')
    def action_onchange_partner(self):
        if self.partner_search_id.phone:
            self.serial_code = self.partner_search_id.phone
        elif self.partner_search_id.mobile:
            self.serial_code = self.partner_search_id.mobile

    @api.depends('pos_payment_service_ids')
    def _compute_amount(self):
        money = 0
        journal_debt_id = self.pos_session_id.config_id.journal_debt_id.id if self.pos_session_id.config_id.journal_debt_id else False
        if journal_debt_id:
            for statement in self.pos_payment_service_ids:
                if statement.journal_id.id == journal_debt_id:
                    money += statement.amount
        self.debt_amount = money
        self.payment_amount = self.amount_total - money

    @api.depends('service_card1_ids.quantity', 'service_card1_ids.price_unit')
    def _compute_amount_total(self):
        for line in self:
            for tmp in line.service_card1_ids:
                line.amount_total += tmp.amount

    @api.onchange('customer_id')
    def onchange_partner(self):
        partner_id = self.env['res.partner'].search([('id', '=', self.customer_id.id)])
        self.rank_id = partner_id.x_rank.id

    @api.model
    def create(self, vals):
        if vals.get('name', _('New')) == _('New'):
            vals['name'] = self.env['ir.sequence'].next_by_code('izi.service.card.using') or _('New')
        return super(ServiceCardUsing, self).create(vals)

    @api.multi
    def unlink(self):
        for line in self:
            if line.state != 'draft':
                raise except_orm('Cảnh báo!', ('Bạn không thể xóa khi khác trạng thái nháp'))
        return super(ServiceCardUsing, self).unlink()

    @api.onchange('customer_id')
    def onchange_customer_id(self):
        if self.customer_id:
            self.pricelist_id = self.customer_id.property_product_pricelist.id

    @api.multi
    def action_search_serial(self):
        self.service_card_ids.unlink()
        serial = self.serial_code
        if serial and len(serial) > 0:
            serial = str(self.serial_code).upper().strip()
        else:
            raise except_orm(_('Thông báo'), _('Vui lòng nhập mã thẻ !'))

        service_card_using_line_obj = self.env['izi.service.card.using.line']
        lot_obj = self.env['stock.production.lot'].search([('name', '=', serial)], limit=1)
        if lot_obj:
            if lot_obj.x_status != 'using':
                raise except_orm('Cảnh báo!', "Thẻ không dùng được")
            customer_obj = lot_obj.x_customer_id
            date = datetime.strptime(lot_obj.life_date, '%Y-%m-%d %H:%M:%S') + timedelta(days=1)
            date_life = date.date()
            if date_life <= datetime.strptime(self.redeem_date, '%Y-%m-%d %H:%M:%S').replace(minute=0, hour=0,
                                                                                             second=0).date():
                raise except_orm('Cảnh báo!', ('Thẻ đã hết hạn'))
            if lot_obj.x_status != 'using' and lot_obj.x_status != 'used':
                raise except_orm('Cảnh báo!', ('Thẻ không hợp lệ'))
            lines = []
            for line in lot_obj.x_card_detail_ids:
                if line.total_qty == line.qty_use:
                    continue
                if line.state == 'ready':
                    argvs = {
                        'serial_id': lot_obj.id,
                        'detail_serial_id': line.id,
                        'service_id': line.product_id.id,
                        'paid_count': line.total_qty,
                        'used_count': line.qty_use,
                        'uom_id': line.product_id.uom_id.id,
                    }
                    lines.append(argvs)
            # self.service_card_ids = lines
        else:
            if not self.pos_session_id.branch_id.brand_id: raise except_orm('Thông báo', 'Chi nhánh %s của bạn chưa gắn thương hiệu không thể tìm KH' % (str(self.pos_session_id.branch_id.name)))
            customer_obj = self.env['res.partner'].search(
                ['|', '|', '|', ('x_code', '=', serial.upper().strip()), ('x_old_code', '=', serial.upper().strip()),
                 ('phone', '=', serial.upper().strip()), ('mobile', '=', serial.upper().strip()), ('x_brand_id', '=', self.pos_session_id.branch_id.brand_id.id)])
            if customer_obj:
                lot_ids = self.env['stock.production.lot'].search([('x_customer_id', '=', customer_obj.id)])
                if not lot_ids:
                    raise except_orm("Cảnh báo",
                                     ("Không tìm thấy dịch vụ của khách hàng. VUi lòng kiểm tra lại mã khách hàng"))
                lines = []
                for line in lot_ids:
                    date = datetime.strptime(line.life_date, '%Y-%m-%d %H:%M:%S') + timedelta(days=1)
                    date_life = date.date()
                    if date_life <= datetime.strptime(self.redeem_date, '%Y-%m-%d %H:%M:%S').replace(minute=0, hour=0,
                                                                                                     second=0).date():
                        continue
                    if line.x_release_id.use_type == '0' and line.x_customer_id.id != customer_obj.id:
                        continue
                    if line.x_status == 'destroy':
                        continue
                    for tmp in line.x_card_detail_ids:
                        if tmp.total_qty == tmp.qty_use:
                            continue
                        if tmp.state == 'ready':
                            argvs = {
                                'serial_id': line.id,
                                'detail_serial_id': tmp.id,
                                'service_id': tmp.product_id.id,
                                'paid_count': tmp.total_qty,
                                'used_count': tmp.qty_use,
                                'uom_id': tmp.product_id.product_tmpl_id.uom_id.id,
                            }
                            lines.append(argvs)
                if len(lines) == 0:
                    raise except_orm('Cảnh báo!', ("Thẻ dịch vụ của khách hàng đã hết!"))
                # self.service_card_ids = lines
                # self.customer_id = customer_obj.id
                # self.rank_id = customer_obj.x_rank.id
                # self.pricelist_id = customer_obj.property_product_pricelist.id
            else:
                raise except_orm('Cảnh báo!', ("Mã không được tìm thấy. Vui lòng kiểm tra lại"))

        self.service_card_ids = lines
        self.customer_id = customer_obj.id
        self.rank_id = customer_obj.x_rank.id
        self.pricelist_id = customer_obj.property_product_pricelist.id
        self.serial_code = ''
        self.partner_search_id = ''

    def _get_material_user(self,quantity,product_id, use_service_id, line_service):
        if product_id.bom_service_count <= 0 and product_id.product_tmpl_id.x_type_service  == 'spa' and self.type != 'guarantee':
            raise except_orm('Cảnh báo!', "Chưa cấu hình nguyên vật liệu sử dụng cho dịch vụ này")
        else:
            # action = self.env.ref('izi_use_service_card.tmp_pos_use_material_view')quantity
            line = []
            bom_id = False
            tmp_service = self.env['tmp.service.card.using']
            tmp_service_line = self.env['tmp.service.card.using.line']
            tmp_service_obj = self.env['tmp.service.card.using'].search([('user_service_card_id', '=', use_service_id)])
            if tmp_service_obj:
                for tmp in product_id.bom_service_ids:
                    if not tmp.product_id or tmp.product_id == product_id:
                        bom_id = tmp.id
                        break
                i = quantity
                while (i > 0):
                    i -= 1
                    if product_id.bom_service_count >1:
                        vals = {
                            'product_id': product_id.id,
                            'bom_id': bom_id if bom_id else False,
                            'qty_using': 1,
                            'tmp_service_card_using': tmp_service_obj.id,
                            'user_service_card_line_id': line_service.id,
                        }
                        tmp_service_line.create(vals)
                    else:
                        vals = {
                            'product_id': product_id.id,
                            'bom_id': bom_id if bom_id else False,
                            'qty_using': quantity,
                            'tmp_service_card_using': tmp_service_obj.id,
                            'user_service_card_line_id': line_service.id,
                        }
                        tmp_service_line.create(vals)
                        break
            else:
                tmp_service_id = self.env['tmp.service.card.using'].create({'user_service_card_id': use_service_id})
                for tmp in product_id.bom_service_ids:
                    if not tmp.product_id or tmp.product_id == product_id:
                        bom_id = tmp.id
                        break
                i = quantity
                while (i > 0):
                    i -= 1
                    if product_id.bom_service_count >1:
                        vals = {
                            'product_id': product_id.id,
                            'bom_id': bom_id if bom_id else False,
                            'qty_using': 1,
                            'tmp_service_card_using': tmp_service_id.id,
                            'user_service_card_line_id': line_service.id,
                        }
                        tmp_service_line.create(vals)
                    else:
                        vals = {
                            'product_id': product_id.id,
                            'bom_id': bom_id if bom_id else False,
                            'qty_using': quantity,
                            'tmp_service_card_using': tmp_service_id.id,
                            'user_service_card_line_id': line_service.id,
                        }
                        tmp_service_line.create(vals)
                        break


    # Không  dùng hàm action_validate_service nữa
    # @api.multi
    # def action_validate_service(self):
    #     if self.state not in ('wait_approve', 'draft'):
    #         raise except_orm('Cảnh báo!', ("Trạng thái sử dụng dịch vụ đã thay đổi. Vui lòng F5 hoặc load lại trang"))
    #     using_stock_move = self.env['izi.using.stock.move.line']
    #     # Thẻ dịch vụ
    #     if self.type == 'card':
    #         count = 0
    #         use_material_obj = self.env['pos.user.material']
    #         # Không gộp đơn xuất nguyên vật liệu
    #         if self.merge == False:
    #             for line in self.service_card_ids:
    #                 use_material_id = self._create_use_material(line)
    #                 # if line.service_id.bom_service_count > 1:
    #                 return self._get_material_user(line.quantity,line.service_id,use_material_id,using_stock_move)
    #                 # else:
    #                 #     res = self._get_material_user(line.quantity,line.service_id,use_material_id,using_stock_move)
    #         else:
    #             employess_ids = []
    #             service_ids = []
    #             count_quantity = 0
    #             # Kiểm tra xem dịch vụ được xuất từ kho nào
    #             picking_type_id = self.pos_session_id.config_id.x_cosmetic_surgery_picking_type.id
    #             argvss = {
    #                 'using_service_id': self.id,
    #                 'date': self.redeem_date,
    #                 'origin': self.name,
    #                 'customer_id': self.customer_id.id,
    #                 'picking_type_id': picking_type_id,
    #             }
    #             use_material_id = use_material_obj.create(argvss)
    #             for line in self.service_card_ids:
    #                 count_quantity += line.quantity
    #                 for x in line.employee_ids:
    #                     employess_ids.append(x.id)
    #                 for y in line.doctor_ids:
    #                     employess_ids.append(y.id)
    #                 if line.service_id.bom_service_count > 1:
    #                     return self._get_material_user(line.quantity, line.service_id, use_material_id,
    #                                                    using_stock_move)
    #                 else:
    #                     res = self._get_material_user(line.quantity, line.service_id, use_material_id, using_stock_move)
    #                     service_ids.append(line.service_id.id)
    #                     use_material_id.update({'employee_ids': [(4, x) for x in employess_ids],
    #                                             'service_ids': [(4, x) for x in service_ids],
    #                                             'quantity': count_quantity})
    #         service_card_detail_obj = self.env['izi.service.card.detail'].search(
    #             [('lot_id', '=', line.serial_id.id), ('product_id', '=', line.service_id.id)])
    #         service_card_detail_obj.qty_use += line.quantity
    #         if service_card_detail_obj.remain_amount >= (service_card_detail_obj.price_unit * line.quantity):
    #             service_card_detail_obj.remain_amount -= service_card_detail_obj.price_unit * line.quantity
    #             # giảm x_balancce trong res_partner
    #             self.customer_id.x_balance = self.customer_id.x_balance - service_card_detail_obj.price_unit * line.quantity
    #         else:
    #             service_card_detail_obj.remain_amount = 0
    #             # giảm x_balancce trong res_partner
    #             self.customer_id.x_balance = self.customer_id.x_balance - (
    #                     service_card_detail_obj.price_unit * line.quantity - service_card_detail_obj.remain_amount)
    #         self.state = 'wait_material'
    #     else:
    #         using_stock_move = self.env['izi.using.stock.move.line']
    #         use_material_obj = self.env['pos.user.material']
    #         if self.merge == False:
    #             for line in self.service_card1_ids:
    #                 use_material_id = self._create_use_material(line)
    #                 if line.service_id.bom_service_count > 1:
    #                     return self._get_material_user(line.quantity,line.service_id,use_material_id,using_stock_move)
    #                 else:
    #                     res = self._get_material_user(line.quantity,line.service_id,use_material_id,using_stock_move)
    #         else:
    #             employess_ids = []
    #             service_ids = []
    #             count_quantity = 0
    #             # Kiểm tra xem dịch vụ được xuất từ kho nào
    #             picking_type_id = self.pos_session_id.config_id.x_cosmetic_surgery_picking_type.id
    #             argvss = {
    #                 'using_service_id': self.id,
    #                 'date': self.redeem_date,
    #                 'origin': self.name,
    #                 'customer_id': self.customer_id.id,
    #                 'picking_type_id': picking_type_id,
    #             }
    #             use_material_id = use_material_obj.create(argvss)
    #             for line in self.service_card1_ids:
    #                 count_quantity += line.quantity
    #                 for x in line.employee_ids:
    #                     employess_ids.append(x.id)
    #                 for y in line.doctor_ids:
    #                     employess_ids.append(y.id)
    #                 if line.service_id.bom_service_count > 1:
    #                     return self._get_material_user(line.quantity, line.service_id, use_material_id,
    #                                                    using_stock_move)
    #                 else:
    #                     res = self._get_material_user(line.quantity, line.service_id, use_material_id, using_stock_move)
    #                     service_ids.append(line.service_id.id)
    #                     use_material_id.update({'employee_ids': [(4, x) for x in employess_ids],
    #                                             'service_ids': [(4, x) for x in service_ids],
    #                                             'quantity': count_quantity})
    #         if not self.pos_order_id:
    #             pos_order_obj = self.env['pos.order']
    #             argvs = {
    #                 'session_id': self.pos_session_id.id,
    #                 'partner_id': self.customer_id.id,
    #                 'x_rank_id': self.rank_id.id,
    #                 'user_id': self.user_id.id,
    #                 'pricelist_id': self.pricelist_id.id,
    #                 'date_order': self.redeem_date,
    #                 'x_type': '3'
    #             }
    #             pos_order_id = pos_order_obj.create(argvs)
    #             self.pos_order_id = pos_order_id.id
    #             pos_order_line_obj = self.env['pos.order.line']
    #             for line in self.service_card1_ids:
    #                 argvs = {
    #                     'product_id': line.service_id.id,
    #                     'qty': line.quantity,
    #                     'price_unit': line.price_unit,
    #                     'discount': line.discount,
    #                     'price_subtotal': line.amount,
    #                     'price_subtotal_incl': line.amount,
    #                     'order_id': pos_order_id.id,
    #                     'x_is_gift': False,
    #                 }
    #                 pos_order_line_obj.create(argvs)
    #
    #         count = 0
    #         count1 = 0
    #         for line in self.service_card1_ids:
    #             count += line.amount
    #         for line in self.pos_payment_service_ids:
    #             count1 += line.amount
    #         if count != count1:
    #             raise except_orm('Cảnh báo!',
    #                              ('Bạn không thể hoàn thành khi số tiền thanh toán không bằng số tiền làm dịch vụ'))
    #         for line in self.pos_payment_service_ids:
    #             x_lot_id = None
    #             if line.x_vc_code:
    #                 x_lot_id = self.env['stock.production.lot'].search(
    #                     [('name', '=', line.x_vc_code.upper().strip())], limit=1).id
    #             statement_id = False
    #             for statement in self.pos_session_id.statement_ids:
    #                 if statement.id == statement_id:
    #                     journal_id = statement.journal_id.id
    #                     break
    #                 elif statement.journal_id.id == line.journal_id.id:
    #                     statement_id = statement.id
    #                     break
    #             if not statement_id:
    #                 raise UserError(_('You have to open at least one cashbox.'))
    #             company_cxt = dict(self.env.context, force_company=line.journal_id.company_id.id)
    #             account_def = self.env['ir.property'].with_context(company_cxt).get('property_account_receivable_id',
    #                                                                                 'res.partner')
    #             account_id = (self.customer_id.property_account_receivable_id.id) or (
    #                     account_def and account_def.id) or False
    #             argvs = {
    #                 'ref': self.pos_session_id.name,
    #                 'name': self.pos_order_id.name,
    #                 'partner_id': self.customer_id.id,
    #                 'amount': line.amount,
    #                 'account_id': account_id,
    #                 'statement_id': statement_id,
    #                 'pos_statement_id': self.pos_order_id.id,
    #                 'journal_id': line.journal_id.id,
    #                 'date': self.redeem_date,
    #                 'x_vc_id': x_lot_id
    #             }
    #             self.env['account.bank.statement.line'].create(argvs)
    #         self.pos_order_id.action_order_complete()
    #         pos_order_id.process_customer_signature()
    #         if self.pos_order_id.x_debt != 0:
    #             self.pos_order_id.statement_ids.write({'x_ignore_reconcile': True})
    #     self.state = 'wait_material'

    @api.multi
    def action_confirm_card(self):
        param_obj = self.env['ir.config_parameter']
        code = param_obj.get_param('default_code_product_category_material')

        #kiểm tra dịch vụ có sử dụng bác sĩ?
        self._check_service_card_ids_service_card1_ids()

        if not code:
            raise ValidationError(
                _(u"Bạn chưa cấu hình thông số hệ thống cho mã nhóm xuất NVL là default_code_product_category_material. Xin hãy liên hệ với người quản trị."))
        list = code.split(',')
        if self.state != 'draft':
            raise except_orm('Cảnh báo!', ("Trạng thái sử dụng dịch vụ đã thay đổi. Vui lòng F5 hoặc load lại trang"))
        else:
            if self.state != 'draft':
                raise except_orm('Cảnh báo!', ("Trạng thái sử dụng dịch vụ đã thay đổi. Vui lòng F5 hoặc load lại trang"))
            # self.state = 'wait_material'
        for line in self.service_card_ids:
            if line.quantity == 0:
                line.unlink()
            else:
                if (len(line.employee_ids) + len(line.doctor_ids)) == 0:
                    raise except_orm('Cảnh báo!', ('Bạn cần chọn kỹ thuật viên trước khi xác nhận'))
        if self.env.context.get('default_type', False):
            context = dict(self.env.context or {})
            del context['default_type']
            self = self.with_context(context)
        if not self.customer_id:
            raise except_orm('Cảnh báo!', ("Bạn phải chọn khách hàng trước khi xác nhận!"))
        pos_session = self.env['pos.session']
        pos_config_id = self.env.user.x_pos_config_id.id
        my_session = pos_session.search([('config_id', '=', pos_config_id), ('state', '=', 'opened')])
        if not my_session:
            raise except_orm("LỖI", "Không có phiên POS nào đang mở. Xin hãy mở phiên trước khi thao tác !!")
        else:
            self.pos_session_id = my_session.id

        if self.type == 'card':
            count = 0
            for line in self.service_card_ids:
                if line.serial_id.x_release_id.use_type == '0':
                    if line.serial_id.x_customer_id.id != self.customer_id.id:
                        raise except_orm('Cảnh báo!', ("Thẻ này là đích danh không thể sử dụng cho khách hàng khác!"))
                if line.quantity != 0:
                    count += 1
            if count == 0:
                raise except_orm('Cảnh báo!',
                                 ("Số lượng dịch vụ không thể bằng không.Vui lòng xóa hoặc thay đổi số lượng!"))
            tmp_service_obj = self.env['tmp.service.card.using'].search([('user_service_card_id', '=', self.id)])
            for line in tmp_service_obj:
                for tmp in line.lines:
                    tmp.unlink()
                line.unlink()
            count_service_bom = 0
            count_service_viet = 0
            for line in self.service_card_ids:
                if line.service_id.product_tmpl_id.categ_id.x_category_code in list:
                    count_service_viet += 1
                if line.service_id.bom_service_count > 1:
                    count_service_bom += 1
                    self._get_material_user(line.quantity, line.service_id, self.id, line)
            if count_service_viet == 0:
                self.state = 'working'
                self.date_start = datetime.now()
                for z in self.service_card_ids:
                    service_card_detail_obj = self.env['izi.service.card.detail'].search(
                        [('lot_id', '=', z.serial_id.id), ('product_id', '=', z.service_id.id)])
                    service_card_detail_obj.qty_use += z.quantity
                    if service_card_detail_obj.remain_amount >= (
                            service_card_detail_obj.price_unit * z.quantity):
                        service_card_detail_obj.remain_amount -= service_card_detail_obj.price_unit * z.quantity
                    else:
                        service_card_detail_obj.remain_amount = 0
            else:
                if count_service_bom > 0:
                    tmp_service_obj = self.env['tmp.service.card.using'].search(
                        [('user_service_card_id', '=', self.id)])
                    view = self.env.ref('izi_use_service_card.tmp_pos_use_material_view')
                    return {
                        'name': _('Chosse?'),
                        'type': 'ir.actions.act_window',
                        'view_type': 'form',
                        'view_mode': 'form',
                        'res_model': 'tmp.service.card.using',
                        'views': [(view.id, 'form')],
                        'view_id': view.id,
                        'target': 'new',
                        'res_id': tmp_service_obj.id,
                        'context': self.env.context,
                    }
                else:
                    self.state = 'wait_material'
                    using_stock_move = self.env['izi.using.stock.move.line']
                    use_material_obj = self.env['pos.user.material']
                    employess_ids = []
                    service_ids = []
                    # Kiểm tra xem dịch vụ được xuất từ kho nào
                    count_service_pttm = 0
                    count_service = 0
                    for line in self.service_card_ids:
                        if line.service_id.product_tmpl_id.x_type_service == 'clinic' and line.service_id.product_tmpl_id.categ_id.x_category_code in list and line.service_id.bom_service_count > 0:
                            count_service_pttm += 1
                            if not self.pos_session_id.config_id.x_cosmetic_surgery_picking_type:
                                raise except_orm("Thông báo!", ('Vui lòng cấu hình lý do xuất kho PTTM'))
                            picking_type_pttm_id = self.pos_session_id.config_id.x_cosmetic_surgery_picking_type.id
                        elif line.service_id.product_tmpl_id.x_type_service == 'spa' and line.service_id.product_tmpl_id.categ_id.x_category_code in list and line.service_id.bom_service_count > 0:
                            count_service += 1
                            if not self.pos_session_id.config_id.x_material_picking_type_id:
                                raise except_orm("Thông báo!", ('Vui lòng cấu hình lý do xuất kho hàng làm'))
                            picking_type_id = self.pos_session_id.config_id.x_material_picking_type_id.id
                        elif line.service_id.product_tmpl_id.x_type_service == 'none':
                            raise except_orm("Thông báo!", ('Kiểm tra lại cấu hình loại dịch vụ "%s"'% line.service_id.name))
                        # Trừ dịch vụ trong thẻ
                        service_card_detail_obj = self.env['izi.service.card.detail'].search(
                            [('lot_id', '=', line.serial_id.id), ('product_id', '=', line.service_id.id)])
                        service_card_detail_obj.qty_use += line.quantity
                        if service_card_detail_obj.remain_amount >= (
                                service_card_detail_obj.price_unit * line.quantity):
                            service_card_detail_obj.remain_amount -= service_card_detail_obj.price_unit * line.quantity
                        else:
                            service_card_detail_obj.remain_amount = 0
                    if count_service_pttm > 0:
                        count_quantity = 0
                        argvss = {
                            'using_service_id': self.id,
                            'date': self.redeem_date,
                            'origin': self.name,
                            'customer_id': self.customer_id.id,
                            'picking_type_id': picking_type_pttm_id,
                            'type_service': 'clinic',
                        }
                        use_material_surgery_id = use_material_obj.create(argvss)
                        for line in self.service_card_ids:
                            if line.service_id.product_tmpl_id.x_type_service == 'clinic' and line.service_id.product_tmpl_id.categ_id.x_category_code in list and line.service_id.bom_service_count > 0:
                                count_quantity += line.quantity
                                for x in line.employee_ids:
                                    employess_ids.append(x.id)
                                for y in line.doctor_ids:
                                    employess_ids.append(y.id)
                                service_ids.append(line.service_id.id)
                                service_bom_obj = self.env['service.bom'].search(
                                    [('product_tmpl_id', '=', line.service_id.product_tmpl_id.id),
                                     ('product_id', '=', line.service_id.id)])
                                if len(service_bom_obj) > 1:
                                    raise except_orm("Thông báo", (
                                        "Đang có nhiều định mức cho dịch vụ này. Vui lòng liên hệ Admintrantor để kiểm tra"))
                                for tmp in service_bom_obj.bom_line_ids:
                                    using_stock_move_obj = self.env['izi.using.stock.move.line'].search(
                                        [('use_material_id', '=', use_material_surgery_id.id),
                                         ('material_id', '=', tmp.product_id.id)])
                                    if using_stock_move_obj:
                                        using_stock_move_obj.quantity += tmp.product_qty * line.quantity
                                    else:
                                        if tmp.product_id.product_tmpl_id.uom_id.id != tmp.product_uom_id.id:
                                            raise except_orm("Cảnh báo!", (
                                                "Cấu hình đơn vị của nguyên vật liệu xuất khác với đơn vị tồn kho. Vui lòng kiểm tra lại"))
                                        argvs = {
                                            'material_id': tmp.product_id.id,
                                            'quantity': tmp.product_qty * line.quantity,
                                            'uom_id': tmp.product_uom_id.id,
                                            'use_material_id': use_material_surgery_id.id,
                                            'use': True
                                        }
                                        using_stock_move.create(argvs)
                        use_material_surgery_id.update({'employee_ids': [(4, x) for x in employess_ids],
                                                        'service_ids': [(4, x) for x in service_ids],
                                                        'quantity': count_quantity})

                        if my_session.config_id.x_auto_export_import_materials:
                            use_material_surgery_id.action_set_default_value()
                            use_material_surgery_id.force_available()
                            use_material_surgery_id.action_done()
                    if count_service > 0:
                        count_quantity = 0
                        argvss = {
                            'using_service_id': self.id,
                            'date': self.redeem_date,
                            'origin': self.name,
                            'customer_id': self.customer_id.id,
                            'picking_type_id': picking_type_id,
                            'type_service': 'spa',
                        }
                        use_material_surgery_id = use_material_obj.create(argvss)
                        for line in self.service_card_ids:
                            if line.service_id.product_tmpl_id.x_type_service == 'spa' and line.service_id.product_tmpl_id.categ_id.x_category_code in list and line.service_id.bom_service_count > 0:
                                count_quantity += line.quantity
                                for x in line.employee_ids:
                                    employess_ids.append(x.id)
                                for y in line.doctor_ids:
                                    employess_ids.append(y.id)
                                service_ids.append(line.service_id.id)
                                service_bom_obj = self.env['service.bom'].search(
                                    [('product_tmpl_id', '=', line.service_id.product_tmpl_id.id),
                                     ('product_id', '=', line.service_id.id)])
                                if len(service_bom_obj) > 1:
                                    raise except_orm("Thông báo", (
                                        "Đang có nhiều định mức cho dịch vụ này. Vui lòng liên hệ Admintrantor để kiểm tra"))
                                # if len(service_bom_obj) == 0:
                                #     raise except_orm("Thông báo", (
                                #         "Dịch vụ không có định lượng . Vui lòng liên hệ Admintrantor để kiểm tra"))
                                for tmp in service_bom_obj.bom_line_ids:
                                    using_stock_move_obj = self.env['izi.using.stock.move.line'].search(
                                        [('use_material_id', '=', use_material_surgery_id.id),
                                         ('material_id', '=', tmp.product_id.id)])
                                    if using_stock_move_obj:
                                        using_stock_move_obj.quantity += tmp.product_qty * line.quantity
                                    else:
                                        if tmp.product_id.product_tmpl_id.uom_id.id != tmp.product_uom_id.id:
                                            raise except_orm("Cảnh báo!", (
                                                "Cấu hình đơn vị của nguyên vật liệu xuất khác với đơn vị tồn kho. Vui lòng kiểm tra lại"))
                                        argvs = {
                                            'material_id': tmp.product_id.id,
                                            'quantity': tmp.product_qty * line.quantity,
                                            'uom_id': tmp.product_uom_id.id,
                                            'use_material_id': use_material_surgery_id.id,
                                            'use': True
                                        }
                                        using_stock_move.create(argvs)
                        use_material_surgery_id.update({'employee_ids': [(4, x) for x in employess_ids],
                                                        'service_ids': [(4, x) for x in service_ids],
                                                        'quantity': count_quantity})

                        if my_session.config_id.x_auto_export_import_materials:
                            use_material_surgery_id.action_set_default_value()
                            use_material_surgery_id.force_available()
                            use_material_surgery_id.action_done()
                    if count_service_pttm == 0 and count_service == 0:
                        self.state = 'working'
                        self.date_start = datetime.now()
        #Làm trò mèo! Do chưa tìm ra nguyên nhân state của line bị null nên code này sẽ cưỡng bức state = 'new'
        for line in self.service_card_ids:
            line.state = 'new'
        pos_sum_digital_obj = self.env['pos.sum.digital.sign'].search(
            [('partner_id', '=', self.customer_id.id), ('state', '=', 'draft'), ('session_id', '=',self.pos_session_id.id)])
        if pos_sum_digital_obj:
            self.x_digital_sign_id = pos_sum_digital_obj.id
        else:
            pos_sum_digital_obj = self.env['pos.sum.digital.sign'].create({
                'partner_id': self.customer_id.id,
                'state': 'draft',
                'date': date.today(),
                'session_id': self.pos_session_id.id,
            })
            self.x_digital_sign_id = pos_sum_digital_obj.id

        for line in self.service_card_ids:
            line.update({'x_digital_sign_id': pos_sum_digital_obj.id})
            # return {
            #         'name': _('Chose '),
            #         'type': 'ir.actions.act_window',
            #         'res_model': 'tmp.service.card.using',
            #         'view_type': 'form',
            #         'view_mode': 'form',
            #         'view_id': self.env.ref('izi_use_service_card.tmp_pos_use_material_view').id,
            #         'target': 'new',
            #         'context': {
            #             'default_user_service_card': self.id,
            #             'default_lines':line
            #         }
            #     }

            # Kiểm tra xem thẻ sử dụng là thẻ gì
            # tbh = 0
            # for line in self.service_card_ids:
            #     if line.serial_id.product_id.x_type_card == 'tbh':
            #         tbh += 1
            # list = []
            # list_service = []
            # trường hợp check thẻ dịch vụ
            # for line in self.service_card_ids:
            #     if line.quantity > 0 and line.serial_id.id not in list:
            #         list.append(line.serial_id.id)
            # list1 = copy.deepcopy(list)
            # for line in self.service_card_ids:
            #     # if line.serial_id.product_id.x_type_card == 'tbh':
            #     #     self.state = 'wait_approve'
            #     # else:
            #     to_debt = amount = amount_service = amount_payment = 0
            #     if line.serial_id.id in list1:
            #         obj_pos_order_line = self.env['pos.order.line'].sudo().search([('lot_name', '=', line.serial_id.name)], limit=1)
            #         # tính toán công nợ đã thanh toán cho đơn hàng này chỉ lấy origin ko lấy khách hàng vì có trừng hợp thẻ linh hoạt
            #         obj_account_invoice = self.env['account.invoice'].search(
            #             [('origin', '=', obj_pos_order_line.order_id.name)])
            #         if len(obj_account_invoice)>0:
            #             if obj_account_invoice[0].residual != 0:
            #                amount_payment += obj_account_invoice[0].amount_total - obj_account_invoice[0].residual
            #             else:
            #                 to_debt = 1
            #         obj_order_line = self.env['pos.order.line'].search(
            #             [('order_id', '=', obj_pos_order_line.order_id.id)])
            #         for line3 in obj_order_line:
            #             # tính số tiền đã xuất và yêu cầu xuất lúc này
            #             obj_product = self.env['product.template'].search(
            #                 [('id', '=', line3.product_id.product_tmpl_id.id), ('type', '=', 'product')])
            #             if len(obj_product) > 0:
            #                 if line3.qty == line3.x_qty:
            #                     amount += (line3.price_unit * (
            #                                 1 - line3.discount / 100)) * line3.x_qty - line3.x_discount
            #                 else:
            #                     debit_product_line = self.env['pos.debit.good.line'].search(
            #                         [('order_id', '=', obj_pos_order_line.order_id.id),
            #                          ('product_id', '=', line3.product_id.id)], limit=1)
            #                     amount += ((line3.price_unit * (1 - line3.discount / 100)) * (
            #                                 debit_product_line.qty_depot + debit_product_line.qty_transfer))- line3.x_discount
            #         for line_service in self.service_card_ids:
            #             if line_service.serial_id.id == line.serial_id.id:
            #                 obj_sevice_detail = self.env['izi.service.card.detail'].search(
            #                     [('lot_id', '=', line.serial_id.id),('product_id','=',line_service.service_id.id),('price_unit', '>', 0)])
            #                 for line_service_detail in obj_sevice_detail:
            #                     amount_service += (line_service.quantity + line_service_detail.qty_use) * line_service_detail.price_unit
            #         if to_debt ==0:
            #            to_debt += amount_payment - amount - amount_service
            #         if to_debt < 0 and (amount_payment > 0 or (obj_account_invoice and amount_payment == 0)):
            #             self.state = 'wait_approve'
            #         list1.remove(line.serial_id.id)
            #
            # if self.state != 'wait_approve':
            #     amount = 0
            #     for line in self.service_card_ids:
            #         amount += line.amount
            #     using_stock_move = self.env['izi.using.stock.move.line']
            #     use_material_obj = self.env['pos.user.material']
            #     # Không gộp đơn xuất nguyên vật liệu
            #     if self.merge == False:
            #         for line in self.service_card_ids:
            #             use_material_id = self._create_use_material(line)
            #             if line.service_id.bom_service_count > 1:
            #                 return self._get_material_user(line.quantity, line.service_id, use_material_id,
            #                                                using_stock_move)
            #             else:
            #                 res = self._get_material_user(line.quantity, line.service_id, use_material_id,
            #                                               using_stock_move)
            #     else:
            #         employess_ids = []
            #         service_ids = []
            #         count_quantity = 0
            #         # Kiểm tra xem dịch vụ được xuất từ kho nào
            #         picking_type_id = self.pos_session_id.config_id.x_cosmetic_surgery_picking_type.id
            #         argvss = {
            #             'using_service_id': self.id,
            #             'date': self.redeem_date,
            #             'origin': self.name,
            #             'customer_id': self.customer_id.id,
            #             'picking_type_id': picking_type_id,
            #         }
            #         use_material_id = use_material_obj.create(argvss)
            #         for line in self.service_card_ids:
            #             count_quantity += line.quantity
            #             for x in line.employee_ids:
            #                 employess_ids.append(x.id)
            #             for y in line.doctor_ids:
            #                 employess_ids.append(y.id)
            #             if line.service_id.bom_service_count > 1:
            #                 return self._get_material_user(line.quantity, line.service_id, use_material_id,
            #                                                using_stock_move)
            #             else:
            #                 res = self._get_material_user(line.quantity, line.service_id, use_material_id,
            #                                               using_stock_move)
            #                 service_ids.append(line.service_id.id)
            #                 use_material_id.update({'employee_ids': [(4, x) for x in employess_ids],
            #                                         'service_ids': [(4, x) for x in service_ids],
            #                                         'quantity': count_quantity})
            #     service_card_detail_obj = self.env['izi.service.card.detail'].search(
            #         [('lot_id', '=', line.serial_id.id), ('product_id', '=', line.service_id.id)])
            #     service_card_detail_obj.qty_use += line.quantity
            #     if service_card_detail_obj.remain_amount >= (service_card_detail_obj.price_unit * line.quantity):
            #         service_card_detail_obj.remain_amount -= service_card_detail_obj.price_unit * line.quantity
            #         # giảm x_balancce trong res_partner
            #         self.customer_id.x_balance = self.customer_id.x_balance - service_card_detail_obj.price_unit * line.quantity
            #     else:
            #         service_card_detail_obj.remain_amount = 0
            #         # giảm x_balancce trong res_partner
            #         self.customer_id.x_balance = self.customer_id.x_balance - (
            #                 service_card_detail_obj.price_unit * line.quantity - service_card_detail_obj.remain_amount)
            #     self.state = 'wait_material'

    @api.multi
    def convert_numbers_to_text_sangla(self, numbers):
        result = ""
        numbers = int(abs(numbers))
        numbers_str = str(int(numbers))
        max_len = len(numbers_str)
        tien = ''
        res = []
        surplus = max_len % 3
        if surplus != 0:
            sub_str = numbers_str[0:surplus]
            res.append(sub_str)
            tien += str(sub_str + '.')
        decimal_number = max_len / 3
        for i in range(0, int(decimal_number)):
            num = surplus
            index = num + 3
            sub_str = numbers_str[num:index]
            res.append(sub_str)
            tien += str(sub_str + '.')
            surplus = index
        return tien

    @api.multi
    def action_confirm_service(self):
        param_obj = self.env['ir.config_parameter']
        code = param_obj.get_param('default_code_product_category_material')
        if not code:
            raise ValidationError(
                _(
                    u"Bạn chưa cấu hình thông số hệ thống cho mã nhóm xuất NVL là default_code_product_category_material. Xin hãy liên hệ với người quản trị."))
        list = code.split(',')
        if self.state != 'wait_payment':
            raise except_orm('Cảnh báo!', ("Trạng thái sử dụng dịch vụ đã thay đổi. Vui lòng F5 hoặc load lại trang"))
        # self.state = 'wait_material'
        picking_type_id = self.env['stock.picking.type']
        if self.env.context.get('default_type', False):
            context = dict(self.env.context or {})
            del context['default_type']
            self = self.with_context(context)
        if not self.customer_id:
            raise except_orm('Cảnh báo!', ("Bạn phải chọn khách hàng trước khi xác nhận!"))
        pos_session = self.env['pos.session']
        pos_config_id = self.env.user.x_pos_config_id.id
        my_session = pos_session.search([('config_id', '=', pos_config_id), ('state', '=', 'opened')])
        if not my_session:
            raise except_orm("LỖI", "Không có phiên POS nào đang mở. Xin hãy mở phiên trước khi thao tác !!")
        else:
            self.pos_session_id = my_session.id
        if self.type == 'service':
            if self.debt_amount + self.payment_amount < self.amount_total:
                raise except_orm('Cảnh báo!', ("Bạn phải thanh toán trước khi xác nhận đơn sử dụng dịch vụ"))
            money = 0
            for line in self.pos_payment_service_ids:
                if line.journal_id.code.upper() == 'VM':
                    money += line.amount
            vm_amount = self.env['pos.virtual.money'].get_available_amount_by_partner(self.customer_id.id)
            if money > 0:
                if money > vm_amount:
                    raise except_orm("Cảnh báo!", ('Số tiền trong thẻ tiền không đủ để thanh toán'))
            count = 0
            for line in self.service_card1_ids:
                if line.quantity != 0:
                    count += 1
                    if (len(line.employee_ids) + len(line.doctor_ids)) == 0:
                        raise except_orm('Cảnh báo!', ('Bạn cần chọn kỹ thuật viên trước khi xác nhận'))
            if count == 0:
                raise except_orm('Cảnh báo!',
                                 ("Số lượng dịch vụ không thể bằng không.Vui lòng xóa hoặc thay đổi số lượng!"))
            counta = 0
            count1a = 0
            for line in self.service_card1_ids:
                counta += line.amount
            for line in self.pos_payment_service_ids:
                count1a += line.amount
            if counta != count1a:
                raise except_orm('Cảnh báo!',
                                 ('Bạn không thể hoàn thành khi số tiền thanh toán không bằng số tiền làm dịch vụ'))
            for line in self.service_card1_ids:
                if line.quantity == 0:
                    line.unlink()
            # using_stock_move = self.env['izi.using.stock.move.line']
            # use_material_obj = self.env['pos.user.material']
            tmp_service_obj = self.env['tmp.service.card.using'].search([('user_service_card_id', '=', self.id)])
            for line in tmp_service_obj:
                for tmp in line.lines:
                    tmp.unlink()
                line.unlink()
            count_service_bom = 0
            count_service_viet = 0
            for line in self.service_card1_ids:
                if line.service_id.product_tmpl_id.categ_id.x_category_code in list:
                    count_service_viet += 1
                if line.service_id.bom_service_count > 1:
                    count_service_bom +=1
                    self._get_material_user(line.quantity, line.service_id, self.id, line)
            if count_service_viet == 0:
                self.state = 'working'
                self.date_start = datetime.now()
            else:
                if count_service_bom > 0:
                    tmp_service_obj = self.env['tmp.service.card.using'].search(
                        [('user_service_card_id', '=', self.id)])
                    view = self.env.ref('izi_use_service_card.tmp_pos_use_material_view')
                    return {
                        'name': _('Choose?'),
                        'type': 'ir.actions.act_window',
                        'view_type': 'form',
                        'view_mode': 'form',
                        'res_model': 'tmp.service.card.using',
                        'views': [(view.id, 'form')],
                        'view_id': view.id,
                        'target': 'new',
                        'res_id': tmp_service_obj.id,
                        'context': self.env.context,
                    }
                else:
                    self.state = 'wait_material'
                    using_stock_move = self.env['izi.using.stock.move.line']
                    use_material_obj = self.env['pos.user.material']
                    employess_ids = []
                    service_ids = []
                    # Kiểm tra xem dịch vụ được xuất từ kho nào
                    count_service_pttm = 0
                    count_service = 0
                    for line in self.service_card1_ids:
                        if line.service_id.product_tmpl_id.x_type_service == 'clinic' and line.service_id.product_tmpl_id.categ_id.x_category_code in list and line.service_id.bom_service_count > 0:
                            count_service_pttm += 1
                            if not self.pos_session_id.config_id.x_cosmetic_surgery_picking_type:
                                raise except_orm("Thông báo!", ('Vui lòng cấu hình lý do xuất kho PTTM'))
                            picking_type_pttm_id = self.pos_session_id.config_id.x_cosmetic_surgery_picking_type.id
                        elif line.service_id.product_tmpl_id.x_type_service == 'spa' and line.service_id.product_tmpl_id.categ_id.x_category_code in list and line.service_id.bom_service_count > 0:
                            count_service += 1
                            if not self.pos_session_id.config_id.x_material_picking_type_id:
                                raise except_orm("Thông báo!", ('Vui lòng cấu hình lý do xuất kho hàng làm'))
                            picking_type_id = self.pos_session_id.config_id.x_material_picking_type_id.id
                        elif line.service_id.product_tmpl_id.x_type_service == 'none':
                            raise except_orm("Thông báo!", ('Kiểm tra lại cấu hình loại dịch vụ "%s"'% line.service_id.name))
                    if count_service_pttm >0:
                        count_quantity = 0
                        argvss = {
                            'using_service_id': self.id,
                            'date': self.redeem_date,
                            'origin': self.name,
                            'customer_id': self.customer_id.id,
                            'picking_type_id': picking_type_pttm_id,
                            'type_service': 'clinic',
                        }
                        use_material_surgery_id = use_material_obj.create(argvss)
                        for line in self.service_card1_ids:
                            if line.service_id.product_tmpl_id.x_type_service == 'clinic' and line.service_id.product_tmpl_id.categ_id.x_category_code in list and line.service_id.bom_service_count > 0:
                                count_quantity += line.quantity
                                for x in line.employee_ids:
                                    employess_ids.append(x.id)
                                for y in line.doctor_ids:
                                    employess_ids.append(y.id)
                                service_ids.append(line.service_id.id)
                                service_bom_obj = self.env['service.bom'].search(
                                    [('product_tmpl_id', '=', line.service_id.product_tmpl_id.id),
                                     ('product_id', '=', line.service_id.id)])
                                if len(service_bom_obj) > 1:
                                    raise except_orm("Thông báo", (
                                        "Đang có nhiều định mức cho dịch vụ này. Vui lòng liên hệ Admintrantor để kiểm tra"))
                                for tmp in service_bom_obj.bom_line_ids:
                                    using_stock_move_obj = self.env['izi.using.stock.move.line'].search(
                                        [('use_material_id', '=', use_material_surgery_id.id),
                                         ('material_id', '=', tmp.product_id.id)])
                                    if using_stock_move_obj:
                                        using_stock_move_obj.quantity += tmp.product_qty * line.quantity
                                    else:
                                        if tmp.product_id.product_tmpl_id.uom_id.id != tmp.product_uom_id.id:
                                            raise except_orm("Cảnh báo!", (
                                                "Cấu hình đơn vị của nguyên vật liệu xuất khác với đơn vị tồn kho. Vui lòng kiểm tra lại"))
                                        argvs = {
                                            'material_id': tmp.product_id.id,
                                            'quantity': tmp.product_qty * line.quantity,
                                            'uom_id': tmp.product_uom_id.id,
                                            'use_material_id': use_material_surgery_id.id,
                                            'use': True
                                        }
                                        using_stock_move.create(argvs)
                        use_material_surgery_id.update({'employee_ids': [(4, x) for x in employess_ids],
                                    'service_ids': [(4, x) for x in service_ids],
                                    'quantity': count_quantity})

                        if my_session.config_id.x_auto_export_import_materials:
                            use_material_surgery_id.action_set_default_value()
                            use_material_surgery_id.force_available()
                            use_material_surgery_id.action_done()
                    if count_service > 0:
                        count_quantity = 0
                        argvss = {
                            'using_service_id': self.id,
                            'date': self.redeem_date,
                            'origin': self.name,
                            'customer_id': self.customer_id.id,
                            'picking_type_id': picking_type_id,
                            'type_service': 'spa',
                        }
                        use_material_surgery_id = use_material_obj.create(argvss)
                        for line in self.service_card1_ids:
                            if line.service_id.product_tmpl_id.x_type_service == 'spa' and line.service_id.product_tmpl_id.categ_id.x_category_code in list and line.service_id.bom_service_count > 0:
                                count_quantity += line.quantity
                                for x in line.employee_ids:
                                    employess_ids.append(x.id)
                                for y in line.doctor_ids:
                                    employess_ids.append(y.id)
                                service_ids.append(line.service_id.id)
                                service_bom_obj = self.env['service.bom'].search(
                                    [('product_tmpl_id', '=', line.service_id.product_tmpl_id.id),
                                     ('product_id', '=', line.service_id.id)])
                                if len(service_bom_obj) > 1:
                                    raise except_orm("Thông báo", (
                                        "Đang có nhiều định mức cho dịch vụ này. Vui lòng liên hệ Admintrantor để kiểm tra"))
                                # if len(service_bom_obj) == 0:
                                #     raise except_orm("Thông báo", (
                                #         "Không có định mức cho dịch vụ này. Vui lòng liên hệ Admintrantor để kiểm tra"))
                                for tmp in service_bom_obj.bom_line_ids:
                                    using_stock_move_obj = self.env['izi.using.stock.move.line'].search(
                                        [('use_material_id', '=', use_material_surgery_id.id),
                                         ('material_id', '=', tmp.product_id.id)])
                                    if using_stock_move_obj:
                                        using_stock_move_obj.quantity += tmp.product_qty * line.quantity
                                    else:
                                        if tmp.product_id.product_tmpl_id.uom_id.id != tmp.product_uom_id.id:
                                            raise except_orm("Cảnh báo!", (
                                                "Cấu hình đơn vị của nguyên vật liệu xuất khác với đơn vị tồn kho. Vui lòng kiểm tra lại"))
                                        argvs = {
                                            'material_id': tmp.product_id.id,
                                            'quantity': tmp.product_qty * line.quantity,
                                            'uom_id': tmp.product_uom_id.id,
                                            'use_material_id': use_material_surgery_id.id,
                                            'use': True
                                        }
                                        using_stock_move.create(argvs)
                        use_material_surgery_id.update({'employee_ids': [(4, x) for x in employess_ids],
                                                        'service_ids': [(4, x) for x in service_ids],
                                                        'quantity': count_quantity})
                        if my_session.config_id.x_auto_export_import_materials:
                            use_material_surgery_id.action_set_default_value()
                            use_material_surgery_id.force_available()
                            use_material_surgery_id.action_done()
                    if count_service_pttm == 0 and count_service == 0:
                        self.state = 'working'
                        self.date_start = datetime.now()
            # Tạo pos_order cho đơn hangf
            if not self.pos_order_id:
                pos_order_obj = self.env['pos.order']
                argvs = {
                    'session_id': self.pos_session_id.id,
                    'partner_id': self.customer_id.id,
                    'x_rank_id': self.rank_id.id,
                    'user_id': self.user_id.id,
                    'pricelist_id': self.pricelist_id.id,
                    'date_order': self.redeem_date,
                    'x_type': '3'
                }
                pos_order_id = pos_order_obj.create(argvs)
                self.pos_order_id = pos_order_id.id
                pos_order_line_obj = self.env['pos.order.line']
                for line in self.service_card1_ids:
                    argvs = {
                        'product_id': line.service_id.id,
                        'qty': line.quantity,
                        'price_unit': line.price_unit,
                        'discount': line.discount,
                        'price_subtotal': line.amount,
                        'price_subtotal_incl': line.amount,
                        'order_id': pos_order_id.id,
                        'x_is_gift': False,
                    }
                    pos_order_line_obj.create(argvs)
                # if self.pos_order_id.x_debt != 0:
                #     self.pos_order_id.create_invoice()
            count = 0
            count1 = 0
            for line in self.service_card1_ids:
                count += line.amount
            for line in self.pos_payment_service_ids:
                count1 += line.amount
            if count != count1:
                raise except_orm('Cảnh báo!',
                                 ('Bạn không thể hoàn thành khi số tiền thanh toán không bằng số tiền làm dịch vụ'))
            for line in self.pos_payment_service_ids:
                x_lot_id = None
                if line.x_vc_code:
                    x_lot_id = self.env['stock.production.lot'].search(
                        [('name', '=', line.x_vc_code.upper().strip())], limit=1).id
                statement_id = False
                for statement in self.pos_session_id.statement_ids:
                    if statement.id == statement_id:
                        journal_id = statement.journal_id.id
                        break
                    elif statement.journal_id.id == line.journal_id.id:
                        statement_id = statement.id
                        break
                if not statement_id:
                    raise UserError(_('You have to open at least one cashbox.'))
                company_cxt = dict(self.env.context, force_company=line.journal_id.company_id.id)
                account_def = self.env['ir.property'].with_context(company_cxt).get('property_account_receivable_id',
                                                                                    'res.partner')
                account_id = (self.customer_id.property_account_receivable_id.id) or (
                        account_def and account_def.id) or False
                argvs = {
                    'ref': self.pos_session_id.name,
                    'name': pos_order_id.name,
                    'partner_id': self.customer_id.id,
                    'amount': line.amount,
                    'account_id': account_id,
                    'statement_id': statement_id,
                    'pos_statement_id': pos_order_id.id,
                    'journal_id': line.journal_id.id,
                    'date': self.redeem_date,
                    'x_vc_id': x_lot_id
                }
                pos_make_payment_id = self.env['account.bank.statement.line'].create(argvs)
            # pos_order_id.action_order_complete()
            if self.x_user_id:
                self.pos_order_id.x_user_id = self.x_user_id
            pos_order_id.process_customer_signature()
            pos_order_id.action_order_confirm()
            if self.pos_order_id.x_debt != 0:
                self.pos_order_id.statement_ids.write({'x_ignore_reconcile': True})

        #Làm trò mèo! Do chưa tìm ra nguyên nhân state của line bị null nên code này sẽ cưỡng bức state = 'new'
        for line in self.service_card1_ids:
            line.state = 'new'
        pos_sum_digital_obj = self.env['pos.sum.digital.sign'].search(
            [('partner_id', '=', self.customer_id.id), ('state', '=', 'draft'), ('session_id', '=',self.pos_session_id.id)])
        if pos_sum_digital_obj:
            self.x_digital_sign_id = pos_sum_digital_obj.id
        else:
            pos_sum_digital_obj = self.env['pos.sum.digital.sign'].create({
                'partner_id': self.customer_id.id,
                'state': 'draft',
                'date': date.today(),
                'session_id': self.pos_session_id.id,
            })
            self.x_digital_sign_id = pos_sum_digital_obj.id

        for line in self.service_card1_ids:
            line.update({'x_digital_sign_id': pos_sum_digital_obj.id})
            # k = []
            # for line in self.service_card1_ids:
            #     parent_id = self.env['product.product'].search([('parent_id', '=', line.service_id.id)])
            #     if parent_id:
            #         raise  except_orm('Cảnh báo!', ("Bạn cần chọn chính xác dịch vụ khách hàng làm"))
            #         for t in parent_id:
            #             k.append(t)
            # self.product_ids = [(4, x.id) for x in k]
            #     Ngày 31/5/ sangla comment lại phê duyệt khi băn nợ
            # amount_debt = 0
            # amount_exception = 0
            # for x in self.pos_payment_service_ids:
            #     if x.journal_id in self.pos_session_id.config_id.journal_debt_id:
            #         amount_debt += x.amount
            #     if x.journal_id in self.pos_session_id.config_id.journal_exception_ids:
            #         amount_exception += x.amount
            # if amount_debt + amount_exception > 0:
            #     self.state = 'wait_approve'
            #     return
            # if self.product_ids:
            #     view = self.env.ref('izi_use_service_card.view_pop_up_choose_service')
            #     return {
            #         'name': _('Choose Service?'),
            #         'type': 'ir.actions.act_window',
            #         'view_type': 'form',
            #         'view_mode': 'form',
            #         'res_model': 'izi.service.card.using',
            #         'views': [(view.id, 'form')],
            #         'view_id': view.id,
            #         'target': 'new',
            #         'res_id': self.id,
            #         'context': self.env.context,
            #     }
        #     use_material_obj = self.env['pos.user.material']
        #     # Không gộp đơn xuất nguyên vật liệu
        #     if self.merge == False:
        #         for line in self.service_card1_ids:
        #             use_material_id = self._create_use_material(line)
        #             if line.service_id.bom_service_count > 1:
        #                 return self._get_material_user(line.quantity, line.service_id, use_material_id,
        #                                                using_stock_move)
        #             else:
        #                 res = self._get_material_user(line.quantity, line.service_id, use_material_id, using_stock_move)
        #     else:
        #         employess_ids = []
        #         service_ids = []
        #         count_quantity = 0
        #         # Kiểm tra xem dịch vụ được xuất từ kho nào
        #         picking_type_id = self.pos_session_id.config_id.x_cosmetic_surgery_picking_type.id
        #         argvss = {
        #             'using_service_id': self.id,
        #             'date': self.redeem_date,
        #             'origin': self.name,
        #             'customer_id': self.customer_id.id,
        #             'picking_type_id': picking_type_id,
        #         }
        #         use_material_id = use_material_obj.create(argvss)
        #         for line in self.service_card1_ids:
        #             count_quantity += line.quantity
        #             for x in line.employee_ids:
        #                 employess_ids.append(x.id)
        #             for y in line.doctor_ids:
        #                 employess_ids.append(y.id)
        #             if line.service_id.bom_service_count > 1:
        #                 return self._get_material_user(line.quantity, line.service_id, use_material_id,
        #                                                using_stock_move)
        #             else:
        #                 res = self._get_material_user(line.quantity, line.service_id, use_material_id, using_stock_move)
        #                 service_ids.append(line.service_id.id)
        #                 use_material_id.update({'employee_ids': [(4, x) for x in employess_ids],
        #                                         'service_ids': [(4, x) for x in service_ids],
        #                                         'quantity': count_quantity})
        #     self.state = 'wait_material'
        #     if not self.pos_order_id:
        #         pos_order_obj = self.env['pos.order']
        #         argvs = {
        #             'session_id': self.pos_session_id.id,
        #             'partner_id': self.customer_id.id,
        #             'x_rank_id': self.rank_id.id,
        #             'user_id': self.user_id.id,
        #             'pricelist_id': self.pricelist_id.id,
        #             'date_order': self.redeem_date,
        #             'x_type': '3'
        #         }
        #         pos_order_id = pos_order_obj.create(argvs)
        #         self.pos_order_id = pos_order_id.id
        #         pos_order_line_obj = self.env['pos.order.line']
        #         for line in self.service_card1_ids:
        #             argvs = {
        #                 'product_id': line.service_id.id,
        #                 'qty': line.quantity,
        #                 'price_unit': line.price_unit,
        #                 'discount': line.discount,
        #                 'price_subtotal': line.amount,
        #                 'price_subtotal_incl': line.amount,
        #                 'order_id': pos_order_id.id,
        #                 'x_is_gift': False,
        #             }
        #             pos_order_line_obj.create(argvs)
        #     count = 0
        #     count1 = 0
        #     for line in self.service_card1_ids:
        #         count += line.amount
        #     for line in self.pos_payment_service_ids:
        #         count1 += line.amount
        #     if count != count1:
        #         raise except_orm('Cảnh báo!',
        #                          ('Bạn không thể hoàn thành khi số tiền thanh toán không bằng số tiền làm dịch vụ'))
        #     for line in self.pos_payment_service_ids:
        #         x_lot_id = None
        #         if line.x_vc_code:
        #             x_lot_id = self.env['stock.production.lot'].search(
        #                 [('name', '=', line.x_vc_code.upper().strip())], limit=1).id
        #         statement_id = False
        #         for statement in self.pos_session_id.statement_ids:
        #             if statement.id == statement_id:
        #                 journal_id = statement.journal_id.id
        #                 break
        #             elif statement.journal_id.id == line.journal_id.id:
        #                 statement_id = statement.id
        #                 break
        #         if not statement_id:
        #             raise UserError(_('You have to open at least one cashbox.'))
        #         company_cxt = dict(self.env.context, force_company=line.journal_id.company_id.id)
        #         account_def = self.env['ir.property'].with_context(company_cxt).get('property_account_receivable_id',
        #                                                                             'res.partner')
        #         account_id = (self.customer_id.property_account_receivable_id.id) or (
        #                 account_def and account_def.id) or False
        #         argvs = {
        #             'ref': self.pos_session_id.name,
        #             'name': pos_order_id.name,
        #             'partner_id': self.customer_id.id,
        #             'amount': line.amount,
        #             'account_id': account_id,
        #             'statement_id': statement_id,
        #             'pos_statement_id': pos_order_id.id,
        #             'journal_id': line.journal_id.id,
        #             'date': self.redeem_date,
        #             'x_vc_id': x_lot_id
        #         }
        #         self.env['account.bank.statement.line'].create(argvs)
        #     pos_order_id.action_order_complete()
        #     pos_order_id.process_customer_signature()
        #     if self.pos_order_id.x_debt != 0:
        #         self.pos_order_id.statement_ids.write({'x_ignore_reconcile': True})
        # self.state = 'wait_material'

    # Không dùng co chấp thuận từ lúc phát hành thẻ bảo hành cho khách hàng rồi lên lúc sử dụng không cần phê duyệt nữa
    # @api.multi
    # def action_approve_tbh(self):
    #     if self.state != 'wait_approve':
    #         raise except_orm('Cảnh báo!', ("Trạng thái sử dụng dịch vụ đã thay đổi. Vui lòng F5 hoặc load lại trang"))
    #     picking_type_id = self.env['stock.picking.type']
    #     amount = 0
    #     for line in self.service_card_ids:
    #         if line.quantity == 0:
    #             line.unlink()
    #         else:
    #             amount += line.amount
    #     using_stock_move = self.env['izi.using.stock.move.line']
    #     use_material_obj = self.env['pos.user.material']
    #     if self.product_ids:
    #         view = self.env.ref('izi_use_service_card.view_pop_up_choose_service')
    #         return {
    #             'name': _('Choose Service?'),
    #             'type': 'ir.actions.act_window',
    #             'view_type': 'form',
    #             'view_mode': 'form',
    #             'res_model': 'izi.service.card.using',
    #             'views': [(view.id, 'form')],
    #             'view_id': view.id,
    #             'target': 'new',
    #             'res_id': self.id,
    #             'context': self.env.context,
    #         }
    #     use_material_obj = self.env['pos.user.material']
    #     # Không gộp đơn xuất nguyên vật liệu
    #     if self.merge == False:
    #         for line in self.service_card_ids:
    #             use_material_id = self._create_use_material(line)
    #             if line.service_id.bom_service_count > 1:
    #                 return self._get_material_user(line.quantity, line.service_id, use_material_id, using_stock_move)
    #             else:
    #                 res = self._get_material_user(line.quantity, line.service_id, use_material_id, using_stock_move)
    #     else:
    #         employess_ids = []
    #         service_ids = []
    #         count_quantity = 0
    #         # Kiểm tra xem dịch vụ được xuất từ kho nào
    #         picking_type_id = self.pos_session_id.config_id.x_cosmetic_surgery_picking_type.id
    #         argvss = {
    #             'using_service_id': self.id,
    #             'date': self.redeem_date,
    #             'origin': self.name,
    #             'customer_id': self.customer_id.id,
    #             'picking_type_id': picking_type_id,
    #         }
    #         use_material_id = use_material_obj.create(argvss)
    #         for line in self.service_card_ids:
    #             count_quantity += line.quantity
    #             for x in line.employee_ids:
    #                 employess_ids.append(x.id)
    #             for y in line.doctor_ids:
    #                 employess_ids.append(y.id)
    #             if line.service_id.bom_service_count > 1:
    #                 return self._get_material_user(line.quantity, line.service_id, use_material_id,
    #                                                using_stock_move)
    #             else:
    #                 res = self._get_material_user(line.quantity, line.service_id, use_material_id, using_stock_move)
    #                 service_ids.append(line.service_id.id)
    #                 use_material_id.update({'employee_ids': [(4, x) for x in employess_ids],
    #                                         'service_ids': [(4, x) for x in service_ids],
    #                                         'quantity': count_quantity})
    #     service_card_detail_obj = self.env['izi.service.card.detail'].search(
    #         [('lot_id', '=', line.serial_id.id), ('product_id', '=', line.service_id.id)])
    #     service_card_detail_obj.qty_use += line.quantity
    #     if service_card_detail_obj.remain_amount >= (service_card_detail_obj.price_unit * line.quantity):
    #         service_card_detail_obj.remain_amount -= service_card_detail_obj.price_unit * line.quantity
    #         # giảm x_balancce trong res_partner
    #         self.customer_id.x_balance = self.customer_id.x_balance - service_card_detail_obj.price_unit * line.quantity
    #     else:
    #         service_card_detail_obj.remain_amount = 0
    #         # giảm x_balancce trong res_partner
    #         self.customer_id.x_balance = self.customer_id.x_balance - (
    #                 service_card_detail_obj.price_unit * line.quantity - service_card_detail_obj.remain_amount)
    #     self.state = 'wait_material'

    @api.multi
    def action_confirm_guarantee(self):
        param_obj = self.env['ir.config_parameter']
        code = param_obj.get_param('default_code_product_category_material')
        if not code:
            raise ValidationError(
                _(
                    u"Bạn chưa cấu hình thông số hệ thống cho mã nhóm xuất NVL là default_code_product_category_material. Xin hãy liên hệ với người quản trị."))
        list = code.split(',')
        if self.state != 'wait_payment':
            raise except_orm('Cảnh báo!', ("Trạng thái sử dụng dịch vụ đã thay đổi. Vui lòng F5 hoặc load lại trang"))
        # self.state = 'wait_material'
        picking_type_id = self.env['stock.picking.type']
        if self.env.context.get('default_type', False):
            context = dict(self.env.context or {})
            del context['default_type']
            self = self.with_context(context)
        if not self.customer_id:
            raise except_orm('Cảnh báo!', ("Bạn phải chọn khách hàng trước khi xác nhận!"))
        pos_session = self.env['pos.session']
        pos_config_id = self.env.user.x_pos_config_id.id
        my_session = pos_session.search([('config_id', '=', pos_config_id), ('state', '=', 'opened')])
        if not my_session:
            raise except_orm("LỖI", "Không có phiên POS nào đang mở. Xin hãy mở phiên trước khi thao tác !!")
        else:
            self.pos_session_id = my_session.id
        if self.type == 'guarantee':
            count = 0
            for line in self.service_card1_ids:
                if line.quantity != 0:
                    count += 1
                    if (len(line.employee_ids) + len(line.doctor_ids)) == 0:
                        raise except_orm('Cảnh báo!', ('Bạn cần chọn kỹ thuật viên trước khi xác nhận'))
            if count == 0:
                raise except_orm('Cảnh báo!',
                                 ("Số lượng dịch vụ không thể bằng không.Vui lòng xóa hoặc thay đổi số lượng!"))
            for line in self.service_card1_ids:
                if line.quantity == 0:
                    line.unlink()
            # using_stock_move = self.env['izi.using.stock.move.line']
            # use_material_obj = self.env['pos.user.material']
            tmp_service_obj = self.env['tmp.service.card.using'].search([('user_service_card_id', '=', self.id)])
            for line in tmp_service_obj:
                for tmp in line.lines:
                    tmp.unlink()
                line.unlink()
            count_service_bom = 0
            count_service_viet = 0
            for line in self.service_card1_ids:
                if line.service_id.product_tmpl_id.categ_id.x_category_code in list:
                    count_service_viet += 1
                if line.service_id.bom_service_count > 1:
                    count_service_bom += 1
                    self._get_material_user(line.quantity, line.service_id, self.id, line)
            if count_service_viet == 0:
                self.state = 'working'
                self.date_start = datetime.now()
            else:
                if count_service_bom > 0:
                    tmp_service_obj = self.env['tmp.service.card.using'].search(
                        [('user_service_card_id', '=', self.id)])
                    view = self.env.ref('izi_use_service_card.tmp_pos_use_material_view')
                    return {
                        'name': _('Choose?'),
                        'type': 'ir.actions.act_window',
                        'view_type': 'form',
                        'view_mode': 'form',
                        'res_model': 'tmp.service.card.using',
                        'views': [(view.id, 'form')],
                        'view_id': view.id,
                        'target': 'new',
                        'res_id': tmp_service_obj.id,
                        'context': self.env.context,
                    }
                else:
                    self.state = 'wait_material'
                    using_stock_move = self.env['izi.using.stock.move.line']
                    use_material_obj = self.env['pos.user.material']
                    employess_ids = []
                    service_ids = []
                    # Kiểm tra xem dịch vụ được xuất từ kho nào
                    count_service_pttm = 0
                    count_service = 0
                    for line in self.service_card1_ids:
                        if line.service_id.product_tmpl_id.x_type_service == 'clinic' and line.service_id.product_tmpl_id.categ_id.x_category_code in list and line.service_id.bom_service_count > 0:
                            count_service_pttm += 1
                            if not self.pos_session_id.config_id.x_cosmetic_surgery_picking_type:
                                raise except_orm("Thông báo!", ('Vui lòng cấu hình lý do xuất kho PTTM'))
                            picking_type_pttm_id = self.pos_session_id.config_id.x_cosmetic_surgery_picking_type.id
                        elif line.service_id.product_tmpl_id.x_type_service == 'spa' and line.service_id.product_tmpl_id.categ_id.x_category_code in list and line.service_id.bom_service_count > 0:
                            count_service += 1
                            if not self.pos_session_id.config_id.x_material_picking_type_id:
                                raise except_orm("Thông báo!", ('Vui lòng cấu hình lý do xuất kho hàng làm'))
                            picking_type_id = self.pos_session_id.config_id.x_material_picking_type_id.id
                        elif line.service_id.product_tmpl_id.x_type_service == 'none':
                            raise except_orm("Thông báo!",
                                             ('Kiểm tra lại cấu hình loại dịch vụ "%s"' % line.service_id.name))
                    if count_service_pttm > 0:
                        count_quantity = 0
                        argvss = {
                            'using_service_id': self.id,
                            'date': self.redeem_date,
                            'origin': self.name,
                            'customer_id': self.customer_id.id,
                            'picking_type_id': picking_type_pttm_id,
                            'type_service': 'clinic',
                        }
                        use_material_surgery_id = use_material_obj.create(argvss)
                        for line in self.service_card1_ids:
                            if line.service_id.product_tmpl_id.x_type_service == 'clinic' and line.service_id.product_tmpl_id.categ_id.x_category_code in list and line.service_id.bom_service_count > 0:
                                count_quantity += line.quantity
                                for x in line.employee_ids:
                                    employess_ids.append(x.id)
                                for y in line.doctor_ids:
                                    employess_ids.append(y.id)
                                service_ids.append(line.service_id.id)
                                service_bom_obj = self.env['service.bom'].search(
                                    [('product_tmpl_id', '=', line.service_id.product_tmpl_id.id),
                                     ('product_id', '=', line.service_id.id)])
                                if len(service_bom_obj) > 1:
                                    raise except_orm("Thông báo", (
                                        "Đang có nhiều định mức cho dịch vụ này. Vui lòng liên hệ Admintrantor để kiểm tra"))
                                for tmp in service_bom_obj.bom_line_ids:
                                    using_stock_move_obj = self.env['izi.using.stock.move.line'].search(
                                        [('use_material_id', '=', use_material_surgery_id.id),
                                         ('material_id', '=', tmp.product_id.id)])
                                    if using_stock_move_obj:
                                        using_stock_move_obj.quantity += tmp.product_qty * line.quantity
                                    else:
                                        if tmp.product_id.product_tmpl_id.uom_id.id != tmp.product_uom_id.id:
                                            raise except_orm("Cảnh báo!", (
                                                "Cấu hình đơn vị của nguyên vật liệu xuất khác với đơn vị tồn kho. Vui lòng kiểm tra lại"))
                                        argvs = {
                                            'material_id': tmp.product_id.id,
                                            'quantity': tmp.product_qty * line.quantity,
                                            'uom_id': tmp.product_uom_id.id,
                                            'use_material_id': use_material_surgery_id.id,
                                            'use': True
                                        }
                                        using_stock_move.create(argvs)
                        use_material_surgery_id.update({'employee_ids': [(4, x) for x in employess_ids],
                                                        'service_ids': [(4, x) for x in service_ids],
                                                        'quantity': count_quantity})

                        if my_session.config_id.x_auto_export_import_materials:
                            use_material_surgery_id.action_set_default_value()
                            use_material_surgery_id.force_available()
                            use_material_surgery_id.action_done()
                    if count_service > 0:
                        count_quantity = 0
                        argvss = {
                            'using_service_id': self.id,
                            'date': self.redeem_date,
                            'origin': self.name,
                            'customer_id': self.customer_id.id,
                            'picking_type_id': picking_type_id,
                            'type_service': 'spa',
                        }
                        use_material_surgery_id = use_material_obj.create(argvss)
                        for line in self.service_card1_ids:
                            if line.service_id.product_tmpl_id.x_type_service == 'spa' and line.service_id.product_tmpl_id.categ_id.x_category_code in list and line.service_id.bom_service_count > 0:
                                count_quantity += line.quantity
                                for x in line.employee_ids:
                                    employess_ids.append(x.id)
                                for y in line.doctor_ids:
                                    employess_ids.append(y.id)
                                service_ids.append(line.service_id.id)
                                service_bom_obj = self.env['service.bom'].search(
                                    [('product_tmpl_id', '=', line.service_id.product_tmpl_id.id),
                                     ('product_id', '=', line.service_id.id)])
                                if len(service_bom_obj) > 1:
                                    raise except_orm("Thông báo", (
                                        "Đang có nhiều định mức cho dịch vụ này. Vui lòng liên hệ Admintrantor để kiểm tra"))
                                    # if len(service_bom_obj) == 0:
                                    #     raise except_orm("Thông báo", (
                                    #         "Không có định mức cho dịch vụ này. Vui lòng liên hệ Admintrantor để kiểm tra"))
                                for tmp in service_bom_obj.bom_line_ids:
                                    using_stock_move_obj = self.env['izi.using.stock.move.line'].search(
                                        [('use_material_id', '=', use_material_surgery_id.id),
                                         ('material_id', '=', tmp.product_id.id)])
                                    if using_stock_move_obj:
                                        using_stock_move_obj.quantity += tmp.product_qty * line.quantity
                                    else:
                                        if tmp.product_id.product_tmpl_id.uom_id.id != tmp.product_uom_id.id:
                                            raise except_orm("Cảnh báo!", (
                                                "Cấu hình đơn vị của nguyên vật liệu xuất khác với đơn vị tồn kho. Vui lòng kiểm tra lại"))
                                        argvs = {
                                            'material_id': tmp.product_id.id,
                                            'quantity': tmp.product_qty * line.quantity,
                                            'uom_id': tmp.product_uom_id.id,
                                            'use_material_id': use_material_surgery_id.id,
                                            'use': True
                                        }
                                        using_stock_move.create(argvs)
                        use_material_surgery_id.update({'employee_ids': [(4, x) for x in employess_ids],
                                                        'service_ids': [(4, x) for x in service_ids],
                                                        'quantity': count_quantity})

                        if my_session.config_id.x_auto_export_import_materials:
                            use_material_surgery_id.action_set_default_value()
                            use_material_surgery_id.force_available()
                            use_material_surgery_id.action_done()
                    if count_service_pttm == 0 and count_service == 0:
                        self.state = 'working'
                        self.date_start = datetime.now()
        #Làm trò mèo! Do chưa tìm ra nguyên nhân state của line bị null nên code này sẽ cưỡng bức state = 'new'
        for line in self.service_card1_ids:
            line.state = 'new'
        pos_sum_digital_obj = self.env['pos.sum.digital.sign'].search(
            [('partner_id', '=', self.customer_id.id), ('state', '=', 'draft'), ('session_id', '=',self.pos_session_id.id)])
        if pos_sum_digital_obj:
            self.x_digital_sign_id = pos_sum_digital_obj.id
        else:
            pos_sum_digital_obj = self.env['pos.sum.digital.sign'].create({
                'partner_id': self.customer_id.id,
                'state': 'draft',
                'date': date.today(),
                'session_id': self.pos_session_id.id,
            })
            self.x_digital_sign_id = pos_sum_digital_obj.id

        for line in self.service_card1_ids:
            line.update({'x_digital_sign_id': pos_sum_digital_obj.id})
        # Sang la comment do bảo hành cũng dùng định mức như bình thường
        # param_obj = self.env['ir.config_parameter']
        # code = param_obj.get_param('default_code_product_category_material')
        # if not code:
        #     raise ValidationError(
        #         _(
        #             u"Bạn chưa cấu hình thông số hệ thống cho mã nhóm  xuất NVL là default_code_product_category_material. Xin hãy liên hệ với người quản trị."))
        # list = code.split(',')
        # if self.state != 'wait_payment':
        #     raise except_orm('Cảnh báo!', ("Trạng thái sử dụng dịch vụ đã thay đổi. Vui lòng F5 hoặc load lại trang"))
        # # self.state = 'wait_material'
        # picking_type_id = self.env['stock.picking.type']
        # if self.env.context.get('default_type', False):
        #     context = dict(self.env.context or {})
        #     del context['default_type']
        #     self = self.with_context(context)
        # if not self.customer_id:
        #     raise except_orm('Cảnh báo!', ("Bạn phải chọn khách hàng trước khi xác nhận!"))
        # pos_session = self.env['pos.session']
        # pos_config_id = self.env.user.x_pos_config_id.id
        # my_session = pos_session.search([('config_id', '=', pos_config_id), ('state', '=', 'opened')])
        # if not my_session:
        #     raise except_orm("LỖI", "Không có phiên POS nào đang mở. Xin hãy mở phiên trước khi thao tác !!")
        # else:
        #     self.pos_session_id = my_session.id
        # if self.type == 'guarantee':
        #     if self.debt_amount + self.payment_amount < self.amount_total:
        #         raise except_orm('Cảnh báo!', ("Bạn phải thanh toán trước khi xác nhận đơn sử dụng dịch vụ"))
        #     money = 0
        #     for line in self.pos_payment_service_ids:
        #         if line.journal_id.code.upper() == 'VM':
        #             money += line.amount
        #     vm_amount = self.env['pos.virtual.money'].get_available_amount_by_partner(self.customer_id.id)
        #     if money > 0:
        #         if money > vm_amount:
        #             raise except_orm("Cảnh báo!", ('Số tiền trong thẻ tiền không đủ để thanh toán'))
        #     count = 0
        #     for line in self.service_card1_ids:
        #         if line.quantity != 0:
        #             count += 1
        #             if (len(line.employee_ids) + len(line.doctor_ids)) == 0:
        #                 raise except_orm('Cảnh báo!', ('Bạn cần chọn kỹ thuật viên trước khi xác nhận'))
        #     if count == 0:
        #         raise except_orm('Cảnh báo!',
        #                          ("Số lượng dịch vụ không thể bằng không.Vui lòng xóa hoặc thay đổi số lượng!"))
        #     for line in self.service_card1_ids:
        #         if line.quantity == 0:
        #             line.unlink()
        #     # using_stock_move = self.env['izi.using.stock.move.line']
        #     # use_material_obj = self.env['pos.user.material']
        #     tmp_service_obj = self.env['tmp.service.card.using'].search([('user_service_card_id', '=', self.id)])
        #     for line in tmp_service_obj:
        #         for tmp in line.lines:
        #             tmp.unlink()
        #         line.unlink()
        #     # count_service_bom = 0
        #     # for line in self.service_card1_ids:
        #     #     if line.service_id.bom_service_count > 1:
        #     #         count_service_bom +=1
        #     #         self._get_material_user(line.quantity, line.service_id, self.id, line)
        #     # if count_service_bom > 0:
        #     #     tmp_service_obj = self.env['tmp.service.card.using'].search(
        #     #         [('user_service_card_id', '=', self.id)])
        #     #     view = self.env.ref('izi_use_service_card.tmp_pos_use_material_view')
        #     #     return {
        #     #         'name': _('Chose?'),
        #     #         'type': 'ir.actions.act_window',
        #     #         'view_type': 'form',
        #     #         'view_mode': 'form',
        #     #         'res_model': 'tmp.service.card.using',
        #     #         'views': [(view.id, 'form')],
        #     #         'view_id': view.id,
        #     #         'target': 'new',
        #     #         'res_id': tmp_service_obj.id,
        #     #         'context': self.env.context,
        #     #     }
        #     # else:
        #     self.state = 'wait_material'
        #     using_stock_move = self.env['izi.using.stock.move.line']
        #     use_material_obj = self.env['pos.user.material']
        #     employess_ids = []
        #     service_ids = []
        #     # Kiểm tra xem dịch vụ được xuất từ kho nào
        #     count_service_pttm = 0
        #     count_service = 0
        #     for line in self.service_card1_ids:
        #         if line.service_id.product_tmpl_id.x_type_service == 'clinic':
        #             count_service_pttm += 1
        #             if not self.pos_session_id.config_id.x_cosmetic_surgery_picking_type:
        #                 raise except_orm("Thông báo!", ('Vui lòng cấu hình lý do xuất kho PTTM'))
        #             picking_type_pttm_id = self.pos_session_id.config_id.x_cosmetic_surgery_picking_type.id
        #         elif line.service_id.product_tmpl_id.x_type_service == 'spa':
        #             count_service += 1
        #             if not self.pos_session_id.config_id.x_material_picking_type_id:
        #                 raise except_orm("Thông báo!", ('Vui lòng cấu hình lý do xuất kho hàng làm'))
        #             picking_type_id = self.pos_session_id.config_id.x_material_picking_type_id.id
        #         else:
        #             raise except_orm("Thông báo!", ('Kiểm tra lại cấu hình loại dịch vụ "%s"'% line.service_id.name))
        #     if count_service_pttm >0:
        #         count_quantity = 0
        #         argvss = {
        #             'using_service_id': self.id,
        #             'date': self.redeem_date,
        #             'origin': self.name,
        #             'customer_id': self.customer_id.id,
        #             'picking_type_id': picking_type_pttm_id,
        #             'type_service': 'guarantee_clinic',
        #         }
        #         use_material_surgery_id = use_material_obj.create(argvss)
        #         for line in self.service_card1_ids:
        #             if line.service_id.product_tmpl_id.x_type_service == 'clinic':
        #                 count_quantity += line.quantity
        #                 for x in line.employee_ids:
        #                     employess_ids.append(x.id)
        #                 for y in line.doctor_ids:
        #                     employess_ids.append(y.id)
        #                 service_ids.append(line.service_id.id)
        #                 # Sangsla comment lại. DỊch vụ bảo hành không cần chọn commponet không thêm đinh mức vào
        #                 # service_bom_obj = self.env['service.bom'].search(
        #                 #     [('product_tmpl_id', '=', line.service_id.product_tmpl_id.id),
        #                 #      ('product_id', '=', line.service_id.id)])
        #                 # if len(service_bom_obj) > 1:
        #                 #     raise except_orm("Thông báo", (
        #                 #         "Đang có nhiều định mức cho dịch vụ này. Vui lòng liên hệ Admintrantor để kiểm tra"))
        #                 # for tmp in service_bom_obj.bom_line_ids:
        #                 #     using_stock_move_obj = self.env['izi.using.stock.move.line'].search(
        #                 #         [('use_material_id', '=', use_material_surgery_id.id),
        #                 #          ('material_id', '=', tmp.product_id.id)])
        #                 #     if using_stock_move_obj:
        #                 #         using_stock_move_obj.quantity += tmp.product_qty * line.quantity
        #                 #     else:
        #                 #         if tmp.product_id.product_tmpl_id.uom_id.id != tmp.product_uom_id.id:
        #                 #             raise except_orm("Cảnh báo!", (
        #                 #                 "Cấu hình đơn vị của nguyên vật liệu xuất khác với đơn vị tồn kho. Vui lòng kiểm tra lại"))
        #                 #         argvs = {
        #                 #             'material_id': tmp.product_id.id,
        #                 #             'quantity': tmp.product_qty * line.quantity,
        #                 #             'uom_id': tmp.product_uom_id.id,
        #                 #             'use_material_id': use_material_surgery_id.id,
        #                 #             'use': True
        #                 #         }
        #                 #         using_stock_move.create(argvs)
        #         use_material_surgery_id.update({'employee_ids': [(4, x) for x in employess_ids],
        #                     'service_ids': [(4, x) for x in service_ids],
        #                     'quantity': count_quantity})
        #     if count_service > 0:
        #         count_quantity = 0
        #         argvss = {
        #             'using_service_id': self.id,
        #             'date': self.redeem_date,
        #             'origin': self.name,
        #             'customer_id': self.customer_id.id,
        #             'picking_type_id': picking_type_id,
        #             'type_service': 'guarantee_spa',
        #         }
        #         use_material_surgery_id = use_material_obj.create(argvss)
        #         for line in self.service_card1_ids:
        #             if line.service_id.product_tmpl_id.x_type_service == 'spa':
        #                 count_quantity += line.quantity
        #                 for x in line.employee_ids:
        #                     employess_ids.append(x.id)
        #                 for y in line.doctor_ids:
        #                     employess_ids.append(y.id)
        #                 service_ids.append(line.service_id.id)
        #                 # Sangsla comment lại. DỊch vụ bảo hành không cần chọn commponet không thêm đinh mức vào
        #                 # service_bom_obj = self.env['service.bom'].search(
        #                 #     [('product_tmpl_id', '=', line.service_id.product_tmpl_id.id),
        #                 #      ('product_id', '=', line.service_id.id)])
        #                 # if len(service_bom_obj) > 1:
        #                 #     raise except_orm("Thông báo", (
        #                 #         "Đang có nhiều định mức cho dịch vụ này. Vui lòng liên hệ Admintrantor để kiểm tra"))
        #                 # for tmp in service_bom_obj.bom_line_ids:
        #                 #     using_stock_move_obj = self.env['izi.using.stock.move.line'].search(
        #                 #         [('use_material_id', '=', use_material_surgery_id.id),
        #                 #          ('material_id', '=', tmp.product_id.id)])
        #                 #     if using_stock_move_obj:
        #                 #         using_stock_move_obj.quantity += tmp.product_qty * line.quantity
        #                 #     else:
        #                 #         if tmp.product_id.product_tmpl_id.uom_id.id != tmp.product_uom_id.id:
        #                 #             raise except_orm("Cảnh báo!", (
        #                 #                 "Cấu hình đơn vị của nguyên vật liệu xuất khác với đơn vị tồn kho. Vui lòng kiểm tra lại"))
        #                 #         argvs = {
        #                 #             'material_id': tmp.product_id.id,
        #                 #             'quantity': tmp.product_qty * line.quantity,
        #                 #             'uom_id': tmp.product_uom_id.id,
        #                 #             'use_material_id': use_material_surgery_id.id,
        #                 #             'use': True
        #                 #         }
        #                 #         using_stock_move.create(argvs)
        #         use_material_surgery_id.update({'employee_ids': [(4, x) for x in employess_ids],
        #                                         'service_ids': [(4, x) for x in service_ids],
        #                                         'quantity': count_quantity})

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
            'partner_id': self.customer_id.id,
            'date': self.redeem_date,
            'origin': self.name,
            'location_dest_id': location_dest_id,
            'location_id': location_id,
            'company_id': user_id.company_id.id
        }

    @api.multi
    def action_done(self):
        if self.state != 'rate':
            raise except_orm('Cảnh báo!', ("Trạng thái sử dụng dịch vụ đã thay đổi. Vui lòng F5 hoặc load lại trang"))
        self.state = 'done'
        for line in self.use_material_ids:
            if line.state != 'done':
                raise except_orm('Cảnh báo!',
                                 ("Bạn cần hoàn thành yêu cầu nguyên vật liệu trước khi hoàn thành dịch vụ"))
        # tạo pos_order khi phát sinh chi phí
        if self.type == 'card':
            for line in self.service_card_ids:
                count = 0
                for tmp in line.serial_id.x_card_detail_ids:
                    if tmp.total_qty != tmp.qty_use:
                        count += 1
                if count == 0:
                    line.serial_id.x_status = 'used'
        self.date_end = datetime.now()
        self.state = 'done'

    @api.multi
    def action_pending(self):
        self.pending = False

    @api.multi
    def payment_service(self):
        # self.action_compute_order_discount()
        if self.env.context is None:
            context = {}
        ctx = self.env.context.copy()
        ctx.update({'default_using_service_id': self.id})
        view = self.env.ref('izi_use_service_card.view_pop_up_pos_payment_service')
        return {
            'name': _('Payment Service'),
            'type': 'ir.actions.act_window',
            'res_model': 'pos.payment.service',
            'view_mode': 'form',
            'view_type': 'form',
            'views': [(view.id, 'form')],
            'view_id': view.id,
            'target': 'new',
            'context': {'default_using_service_id': self.id
                        },
        }

    @api.multi
    def action_refund(self):
        for line in self:
            if line.type == 'card':
                for tmp in self.service_card_ids:
                    date = datetime.strptime(tmp.serial_id.life_date, '%Y-%m-%d %H:%M:%S') + timedelta(days=1)
                    day_now = datetime.today().replace(minute=0, hour=0, second=0)
                    if day_now >= date:
                        raise except_orm("Cảnh báo!", 'Thẻ dịch vụ đã hết hạn bạn không thể Refund')
        view = self.env.ref('izi_use_service_card.view_pop_up_refund_service')
        return {
            'name': _('Method Refund?'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'izi.service.card.using',
            'views': [(view.id, 'form')],
            'view_id': view.id,
            'target': 'new',
            'res_id': self.id,
            'context': self.env.context,
        }

    @api.multi
    def action_confirm_refund(self):
        if self.state != 'wait_confirm':
            raise except_orm('Cảnh báo!', ("Trạng thái sử dụng dịch vụ đã thay đổi. Vui lòng F5 hoặc load lại trang"))
        self.state = 'cancel'
        pos_session = self.env['pos.session']
        pos_config_id = self.env.user.x_pos_config_id.id
        # my_session = pos_session.search([('config_id', '=', pos_config_id), ('state', '=', 'opened')])
        # if not my_session:
        #     raise except_orm("LỖI", "Không có phiên POS nào đang mở. Xin hãy mở phiên trước khi thao tác !!")
        if self.option_refund == 'cancel':
            for line in self.use_material_ids:
                if line.state == 'draft':
                    break
                using_stock_move = self.env['izi.using.stock.move.line']
                use_material_obj = self.env['pos.user.material']
                argvss = {
                    'customer_id': line.customer_id.id,
                    'service_ids': [(4, x.id) for x in line.service_ids],
                    'employee_ids': [(4, x.id) for x in line.employee_ids],
                    'using_service_id': line.using_service_id.id,
                    'date': line.date,
                    'origin': line.origin,
                    'type': 'input',
                    'state': 'exported',
                    'quantity': line.quantity,
                    'picking_type_id': line.picking_type_id.id,
                    'type_service': line.type_service,
                }
                use_material_id = use_material_obj.create(argvss)
                for tmp in line.use_move_line_ids:
                    argvs = {
                        'material_id': tmp.material_id.id,
                        'quantity': tmp.quantity,
                        'quantity_used': tmp.quantity_used,
                        'uom_id': tmp.uom_id.id,
                        'replace_material_id': tmp.replace_material_id.id,
                        'quantity_replace': tmp.quantity_replace,
                        'uom_replace_id': tmp.uom_replace_id.id,
                        'use_material_id': use_material_id.id,
                        'use': tmp.use
                    }
                    using_stock_move.create(argvs)
                if self.pos_session_id.config_id.x_auto_export_import_materials:
                    use_material_id.action_confirm_cancel()
        if self.type == 'service':
            if not self.pos_order_id.invoice_id:
                if self.pos_order_id.x_debt != 0:
                    self.pos_order_id.create_invoice()
            self.pos_order_id.refund()
            pos_order_refund = self.env['pos.order'].search([('x_pos_partner_refund_id', '=', self.pos_order_id.id)])
            self.update({'pos_order_refund_id': pos_order_refund.id})
        elif self.type == 'card':
            for line in self.service_card_ids:
                if line.serial_id.x_status == 'used':
                    line.serial_id.x_status = 'using'
                service_card_detail_obj = self.env['izi.service.card.detail'].search(
                    [('lot_id', '=', line.serial_id.id), ('product_id', '=', line.service_id.id)], limit=1)
                if service_card_detail_obj.amount_total - service_card_detail_obj.price_unit * service_card_detail_obj.qty_use > 0:
                    service_card_detail_obj.remain_amount += service_card_detail_obj.price_unit * line.quantity
                else:
                    service_card_detail_obj.remain_amount -= (
                                service_card_detail_obj.amount_total - service_card_detail_obj.price_unit * service_card_detail_obj.qty_use)
                service_card_detail_obj.qty_use -= line.quantity
            self.state = 'cancel'
        else:
            self.state = 'cancel'
        if self.option_refund == 'cancel':
            if self.use_material_ids:
                for line in self.use_material_ids:
                    if line.state not in ('done', 'cancel'):
                        self.state = 'wait_delivery'
                        break

    @api.multi
    def action_rate(self):
        view = self.env.ref('pos_digital_sign_sum.pos_digital_sign_sum_pop_up_form')
        return {
            'name': _('Sign Customer?'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'pos.sum.digital.sign',
            'views': [(view.id, 'form')],
            'view_id': view.id,
            'target': 'new',
            'res_id': self.x_digital_sign_id.id,
            'context': self.env.context,
        }

    @api.multi
    def process_rate_service(self):
        if not self.signature_image:
            raise except_orm('Cảnh báo!', 'Bạn cần phải ký để xác nhận!')
        self.state = 'rate'
        return {'type': 'ir.actions.act_window_close'}

    @api.multi
    def action_cancel(self):
        if self.state != 'wait_material':
            raise except_orm('Cảnh báo!', ("Trạng thái sử dụng dịch vụ đã thay đổi. Vui lòng F5 hoặc load lại trang"))
        self.state = 'cancel'
        for line in self.use_material_ids:
            if line.state != 'draft':
                raise except_orm('Cảnh báo!',
                                 "Phiếu xuất kho đã được xác nhận. Bạn cần hoàn thành lần sử dụng dịch vụ này sau đó refund. Cần xác nhận của supervisor thay cho khách hang")
            line.state = 'cancel'
        self.state = 'cancel'
        if self.type == 'card':
            for line in self.service_card_ids:
                service_card_detail_obj = self.env['izi.service.card.detail'].search(
                    [('lot_id', '=', line.serial_id.id), ('product_id', '=', line.service_id.id)])
                if service_card_detail_obj.amount_total - service_card_detail_obj.price_unit * service_card_detail_obj.qty_use > 0:
                    service_card_detail_obj.remain_amount += service_card_detail_obj.price_unit * line.quantity
                else:
                    service_card_detail_obj.remain_amount -= (
                            service_card_detail_obj.amount_total - service_card_detail_obj.price_unit * service_card_detail_obj.qty_use)
                service_card_detail_obj.qty_use -= line.quantity
        elif self.type == 'service':
            self.pos_order_id.refund()
            pos_order_refund = self.env['pos.order'].search([('x_pos_partner_refund_id', '=', self.pos_order_id.id)])
            view = self.env.ref('point_of_sale.view_pos_pos_form')
            return {
                'name': _('Customer Signature?'),
                'type': 'ir.actions.act_window',
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'pos.order',
                'views': [(view.id, 'form')],
                'view_id': view.id,
                'target': '',
                'res_id': pos_order_refund.id,
                'context': self.env.context,
            }

    @api.multi
    def action_back(self):
        self.state = 'draft'
        for line in self.pos_payment_service_ids:
            line.unlink()

    @api.multi
    def process_refund(self):
        if self.type == 'card':
            self.update({'state': 'wait_confirm'})
            return {'type': 'ir.actions.act_window_close'}
        elif self.type == 'service':
            self.update({'state': 'wait_confirm'})
            self.action_confirm_refund()
            pos_order_refund = self.env['pos.order'].search([('x_pos_partner_refund_id', '=', self.pos_order_id.id)])
            # pos_order_refund.send_refund()
            # pos_order_refund.confirm_refund()
            view = self.env.ref('point_of_sale.view_pos_pos_form')
            return {
                'name': _('Customer Signature?'),
                'type': 'ir.actions.act_window',
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'pos.order',
                'views': [(view.id, 'form')],
                'view_id': view.id,
                'target': '',
                'res_id': pos_order_refund.id,
                'context': self.env.context,
            }
        else:
            self.update({'state': 'wait_confirm'})
            return {'type': 'ir.actions.act_window_close'}

    # Chiết khấu Vip trong sử dụng dịch vụ lẻ
    def action_compute_order_discount(self):
        self.ensure_one()
        if self.service_card1_ids:
            for line in self.service_card1_ids:
                if line.discount != 0:
                    line.update({'discount': 0})
            # Lấy thông tin các sản phẩm được giảm giá ngoại lệ theo hạng VIP của KH
            except_dict = {}
            for product in self.customer_id.x_rank.except_product_ids:
                except_dict[product.product_id.id] = product.discount
                except_dict['%s_amount' % product.product_id.id] = product.max_amount
            discount_service = self.customer_id.x_rank.discount_service
            discount_product = self.customer_id.x_rank.discount_product
            discount_except = len(self.customer_id.x_rank.except_product_ids)

            for line in self.service_card1_ids:
                if line.service_id.x_type_card != 'none':
                    continue
                if line.service_id.default_code:
                    if line.service_id.default_code.upper() == 'PDDV':
                        break
                    # elif line.service_id.default_code.upper() == 'COIN':
                    #     continue
                # Sản phẩm thuộc ngoại lệ
                if discount_except and line.service_id.id in except_dict:
                    key = '%s_amount' % line.service_id.id
                    x_discount = except_dict[line.service_id.id] * (line.amount) / 100.0
                    if key in except_dict:
                        # Kiểm tra giới hạn số tiền tối đa
                        max_amount = except_dict[key]
                        if max_amount and max_amount < x_discount:
                            x_discount = max_amount
                    # Qui đổi số tiền ra phần trăm
                    line.discount = round(x_discount * 100.0 / (line.price_unit * line.quantity), 4)
                # Dịch vụ
                elif discount_service > 0 and line.service_id.type == 'service':
                    line.discount += discount_service
                # Sản phẩm
                elif discount_product > 0 and line.service_id.type == 'product':
                    line.discount += discount_product

    @api.multi
    def action_request_material(self):
        if self.env.context is None:
            context = {}
        ctx = self.env.context.copy()
        ctx.update({'default_using_service_id': self.id,
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
    def action_change_employeee(self):
        view = self.env.ref('izi_use_service_card.pop_up_change_employee_service')
        return {
            'name': _('Change_Service?'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'izi.service.card.using',
            'views': [(view.id, 'form')],
            'view_id': view.id,
            'target': 'new',
            'res_id': self.id,
            'context': self.env.context,
    }

    @api.multi
    def action_apply_change_employee(self):
        return {'type': 'ir.actions.act_window_close'}

    @api.multi
    def action_cancel_choose_service(self):
        if self.type == 'card':
            self.state = 'draft'
        if self.type == 'service':
            self.state = 'wait_approve'
        return {'type': 'ir.actions.act_window_close'}

    @api.multi
    def action_send_price(self):
        #kiểm tra dịch vụ có sử dụng bác sĩ?
        self._check_service_card_ids_service_card1_ids()
        if self.state != 'draft':
            raise except_orm("Cảnh báo!", ("Trạng thái đơn sử dụng đã thay đổi. Vui lòng F5 hoặc tải lại trang"))
        if self.type == 'card':
            for line in self.service_card_ids:
                if line.quantity == 0:
                    line.unlink()
                else:
                    if (len(line.employee_ids) + len(line.doctor_ids)) == 0:
                        raise except_orm('Cảnh báo!', ('Bạn cần chọn kỹ thuật viên trước khi xác nhận'))
        else:
            for line in self.service_card1_ids:
                if (len(line.employee_ids) + len(line.doctor_ids)) == 0:
                    raise except_orm('Cảnh báo!', ('Bạn cần chọn kỹ thuật viên trước khi xác nhận'))
        if self.env.context.get('default_type', False):
            context = dict(self.env.context or {})
            del context['default_type']
            self = self.with_context(context)
        if not self.customer_id:
            raise except_orm('Cảnh báo!', ("Bạn phải chọn khách hàng trước khi xác nhận!"))
        pos_session = self.env['pos.session']
        pos_config_id = self.env.user.x_pos_config_id.id
        my_session = pos_session.search([('config_id', '=', pos_config_id), ('state', '=', 'opened')])
        if not my_session:
            raise except_orm("LỖI", "Không có phiên POS nào đang mở. Xin hãy mở phiên trước khi thao tác !!")
        if self.type == 'card':
            count = 0
            for line in self.service_card_ids:
                if line.serial_id.x_release_id.use_type == '0':
                    if line.serial_id.x_customer_id.id != self.customer_id.id:
                        raise except_orm('Cảnh báo!', ("Thẻ này là đích danh không thể sử dụng cho khách hàng khác!"))
                if line.quantity != 0:
                    count += 1
            if count == 0:
                raise except_orm('Cảnh báo!',
                                 ("Số lượng dịch vụ không thể bằng không.Vui lòng xóa hoặc thay đổi số lượng!"))

        msg = []
        approve_price = False
        '''
        Dự án Amia không sử dụng chức năng bán dưới giá 29/11/2019
        if self.type == 'service':
            for line in self.service_card1_ids:
                price = self.pricelist_id.get_product_price(line.service_id, line.quantity or 1.0, self.customer_id)
                if line.price_unit < price:
                    approve_price = True
                    msg.append('Dịch vụ %s ' % (line.service_id.name))
                    msg.append('Giá niêm yết %r ' % self.convert_numbers_to_text_sangla(price))
                    msg.append('Giá bán %r ' % self.convert_numbers_to_text_sangla(line.price_unit))
                    msg.append('Dưới mức giá bán tối thiểu cần phê duyêt. ')
                if line.discount > 0 and line.price_unit * (100 - line.discount) / 100 < price:
                    approve_price = True
                    msg.append('Dịch vụ %s ' % (line.service_id.name))
                    msg.append('Giá niêm yết %r ' % self.convert_numbers_to_text_sangla(price))
                    msg.append('Nhập chiết khấu %r phần trăm ' % self.convert_numbers_to_text_sangla(line.discount))
                    msg.append('Giá bán %r ' % self.convert_numbers_to_text_sangla(line.price_unit * (100 - line.discount)/100))
                    msg.append('Dưới mức giá bán tối thiểu cần phê duyêt.')
        if self.type == 'guarantee':
            for line in self.service_card1_ids:
                if line.service_id.x_guarantee != True:
                    approve_price = True
                    msg.append('Dịch vụ %s ' % (line.service_id.name))
                    msg.append('bảo hành cần phê duyệt')
        '''
        if approve_price == True:
            '''
            Dự án Amia không sử dụng chức năng bán dưới giá 29/11/2019
            self.state = 'wait_approve'
            values = {'state': 'wait_approve'}
            # Thông báo quản lý phê duyệt
            values['message_follower_ids'] = []
            users = self.env['res.users'].search([
                ('groups_id', 'in', self.env.ref('point_of_sale.group_pos_manager').id),
                ('id', '!=', self._uid)])
            MailFollowers = self.env['mail.followers']
            follower_partner_ids = []
            for m in self.message_follower_ids:
                follower_partner_ids.append(m.partner_id.id)
            for user in self.user_id:
                if user.x_pos_config_id.id == self.pos_session_id.config_id.id and \
                        user.partner_id.id and user.partner_id.id not in follower_partner_ids:
                    values['message_follower_ids'] += \
                        MailFollowers._add_follower_command(self._name, [], {user.partner_id.id: None}, {})[0]
            self.write(values)
            self.message_post(subtype='mt_activities',
                              body=" %s !" % (' ' + ', '.join(msg) if len(msg) else ''))
            return {'type': 'ir.actions.act_window_close'}
            '''
        else:
            self.state = 'wait_payment'

    @api.multi
    def action_manager_confirm(self):
        if self.state != 'wait_approve':
            raise except_orm("Cảnh báo!", ("Trạng thái đơn sử dụng đã thay đổi. Vui lòng F5 hoặc tải lại trang"))
        self.state = 'wait_payment'

    @api.multi
    def action_back_working(self):
        if len(self.use_material_ids) > 0:
            raise except_orm("Thông báo!", ("Có yêu cầu NVL không thể quay lại"))

    @api.multi
    def action_print_work(self):
        if self.service_card_ids or self.service_card1_ids:
            return {
                'type': 'ir.actions.act_url',
                'url': 'report/pdf/izi_use_service_card.report_template_work_service_view/%s' % (str(self.id)),
                'target': 'new',
                'res_id': self.id,
            }