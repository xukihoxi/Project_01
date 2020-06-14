# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import except_orm
from datetime import datetime
from dateutil.relativedelta import relativedelta

import logging

_logger = logging.getLogger(__name__)

STATE_SELECTOR = [('new', 'New'), ('confirmed', 'Confirmed'), ('order', 'Order'), ('working', 'Working'),
                  ('done', 'Done'), ('cancel', 'Canceled'), ('no_sale', 'NoSale')]
DTF = '%Y-%m-%d %H:%M:%S'
DF = '%Y-%m-%d'
DTFR = '%d-%m-%Y %H:%M'


class ServiceBooking(models.Model):
    _name = 'service.booking'
    _description = 'Service booking'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'create_date DESC'

    def _default_company_id(self):
        if self._uid:
            user = self.env['res.users'].search([('id', '=', self._uid)])
            return user.company_id.id

    def _get_employees_domain(self):
        employee_ids = self.get_employee_by_team_id(self.env.user.sale_team_id.id)
        return [('id', 'in', employee_ids)]

    # def _get_customer_domain(self):
    #     domain = [('customer', '=', True)]
    #     if self.type == 'service':
    #         return domain
    #     is_manager = self.env.user.has_group('sales_team.group_sale_manager')
    #     is_lead = self.env.user.has_group('sales_team.group_sale_salesman_all_leads')
    #     if not is_manager:
    #         if not is_lead:
    #             return domain + [('user_id', 'in', self.env.user.sale_team_id.member_ids.ids)]
    #         return domain + [('user_id', '=', self.env.user.id)]
    #     return domain
    def _domain_team_id(self):
        UserObj = self.env['res.users']
        BrandObj = self.env['res.brand']

        user = UserObj.search([('id', '=', self.env.uid)])
        brand_ids = BrandObj.get_brand_ids_by_branches(user.branch_ids.ids)
        return [('x_branch_id.brand_id', 'in', brand_ids)]

    name = fields.Char(string='Name', track_visibility='onchange')
    type = fields.Selection([('service', 'Service Booking'), ('meeting', 'Customer meeting')], required=True,
                            default='service', track_visibility='onchange')
    customer_id = fields.Many2one('res.partner', string="Customer", track_visibility='onchange')
    date = fields.Date(string="Date", track_visibility='onchange', copy=False)
    time_from = fields.Datetime(string="Time From", track_visibility='onchange', copy=False)
    time_to = fields.Datetime(string="Time To", track_visibility='onchange', copy=False)
    date = fields.Date(string="Date", track_visibility='onchange', copy=False)
    company_id = fields.Many2one('res.company', string="Company", default=_default_company_id)
    branch_id = fields.Many2one('res.branch', string="Branch")
    team_id = fields.Many2one('crm.team', string="Team", domain=_domain_team_id)
    user_id = fields.Many2one('res.users', string="User Responsible", default=lambda self: self._uid,
                              track_visibility='onchange')
    customer_qty = fields.Integer(string="Customer quantity", default=1)
    services = fields.Many2many('product.product', string="Services", domain=[('product_tmpl_id.type', '=', 'service')])
    employees = fields.Many2many('hr.employee', string="Employees")
    beds = fields.Many2many('pos.service.bed', string='Beds')
    contact_number = fields.Char(string="Contact Number", size=64, track_visibility='onchange')
    note = fields.Text(string="Note")
    is_create_event = fields.Boolean(string='Create calendar event', default=False)
    ref_order_id = fields.Many2one('pos.order', string='Order', track_visibility='onchange')
    # ref_sale_order_id = fields.Many2one('sale.order', string='Sale Order', track_visibility='onchange')
    # source_type = fields.Selection([('employee', 'Employee created'), ('customer', 'Customer created')])
    reason_no_sale = fields.Text(string="Reason no sale")
    state = fields.Selection(STATE_SELECTOR, default='new', track_visibility='onchange')
    product_ids = fields.One2many('service.booking.product', 'service_booking_id', string='Products')
    # tham chiếu đơn sử dụng dịch vụ
    use_service_id = fields.Many2one('izi.service.card.using', string='Use service', track_visibility='onchange')
    time = fields.Float(string='Time', compute='_compute_time', store=True, digits=(16, 2))
    config_id = fields.Many2one('pos.config', string='Pos Config')
    crm_lead_id = fields.Many2one('crm.lead', 'Lead')
    selection = fields.Selection(selection=(('order', 'Order'),
                                            ('using', 'Use Service'),
                                            ('coin', "Coin"), ('deposit', "Deposit")), default='order',
                                 string='Order form')
    parent_id = fields.Many2one('service.booking', "Parent")
    expected_revenue = fields.Float(default=0, string="Expected revenue")
    real_revenue = fields.Float(string="Real revenue", compute='_compute_real_revenue')
    have_deals = fields.Boolean(string="Have deals", default=False, compute="_compute_have_deals")

    @api.onchange('team_id')
    def _onchange_team_id(self):
        if self.team_id:
            config_id = self.env['pos.config'].search([('crm_team_id', '=', self.team_id.id)], limit=1)
            self.config_id = config_id.id
            self.branch_id = self.team_id.x_branch_id.id
            return {'domain': {'user_id': [('id', 'in', self.team_id.x_member_ids.ids)], }}

    @api.multi
    def unlink(self):
        for line in self:
            if line.state != 'new':
                raise except_orm('Cảnh báo!', ('Không thể xóa bản ghi ở trạng thái khác mới'))
        super(ServiceBooking, self).unlink()

    @api.one
    @api.depends('customer_id')
    def _compute_have_deals(self):
        if self.customer_id:
            orders = self.env['pos.order'].search([('partner_id', '=', self.customer_id.id)])
            if orders:
                self.have_deals = True
            else:
                self.have_deals= False

    @api.one
    def _compute_real_revenue(self):
        if self.customer_id:
            from_time = '%s 00:00:00' % (str(self.date))
            to_time = '%s 23:59:59' % (str(self.date))
            real_revenue = 0
            orders = self.env['pos.order'].search([('partner_id', '=', self.customer_id.id), ('date_order', '>=', from_time), ('date_order', '<=', to_time)])
            if orders:
                for order in orders:
                    real_revenue += order.amount_total
            self.real_revenue = real_revenue

    @api.one
    @api.depends('time_from', 'time_to')
    def _compute_time(self):
        if self.time_from and self.time_to:
            if int(str(self.time_from)[14:16]) < int(str(self.time_to)[14:16]):
                self.time = int(str(self.time_to)[11:13]) - int(str(self.time_from)[11:13]) - 1 + (60 + int(
                    str(self.time_to)[14:16]) - int(str(self.time_from)[14:16])) / 60
            if int(str(self.time_to)[14:16]) >= int(str(self.time_from)[14:16]):
                self.time = int(str(self.time_to)[11:13]) - int(str(self.time_from)[11:13]) + (int(
                    str(self.time_to)[14:16]) - int(str(self.time_from)[14:16])) / 60

    @api.onchange('customer_id')
    def _onchange_customer_id(self):
        if self.customer_id:
            self.contact_number = self.customer_id.phone

    @api.onchange('time_from', 'time_to')
    def _onchange_time_from_time_to(self):
        if self.time_from:
            self.time_from = datetime.strptime(self.time_from, "%Y-%m-%d %H:%M:%S").strftime('%Y-%m-%d %H:%M:00')
            self.date = (datetime.strptime(self.time_from, "%Y-%m-%d %H:%M:%S") + relativedelta(hours=7)).strftime('%Y-%m-%d')
        if self.time_to:
            self.time_to = datetime.strptime(self.time_to, "%Y-%m-%d %H:%M:%S").strftime('%Y-%m-%d %H:%M:00')
        if self.time_from and self.time_to:
            if datetime.strptime(self.time_from, "%Y-%m-%d %H:%M:%S") > datetime.strptime(self.time_to,
                                                                                          "%Y-%m-%d %H:%M:%S"):
                self.time_to = False
                return {'warning': {'title': _('Thông báo'),
                                    'message': _('"Từ giờ" phải trước "Đến giờ". Vui lòng chọn lại!')}
                        }

    @api.model
    def create(self, vals):
        self.validate_time_booking_meeting(vals)
        self.validate_exist_customer_booking_meeting(vals)
        # Comment do không phải người phụ trách vẫn đặt lịch được
        # self.validate_product_ids_permission(vals)

        if not vals.get('name', False):
            vals['name'] = self.get_service_booking_name(vals.get('type', 'service'))

        booking = super(ServiceBooking, self).create(vals)
        # Comment do không cần chọn giuwongf, nhân viên. Nếu cần thì bật lên
        # booking.validate_bed_state()
        # booking.validate_employee_state()
        booking.validate_time_with_service_time()
        #
        ### self.change_lead_state(self._context.get('lead_id', None), vals.get('type', 'meeting'))
        booking.create_event(vals.get('is_create_event', False))
        return booking

    @api.multi
    def write(self, vals):
        self.validate_time_booking_meeting(vals)
        # self.validate_product_ids_permission(vals)
        res = super(ServiceBooking, self).write(vals)
        # self.validate_bed_state()
        # self.validate_employee_state()
        self.validate_time_with_service_time()
        self.create_event(vals.get('is_create_event', False))
        return res

    @api.multi
    def action_confirm(self):
        # if self.type == 'service':
        #     if len(self.employees) < 1:
        #         raise except_orm('Thông báo', 'Bạn chưa chọn nhân viên. Vui lòng kiểm tra lại trước khi xác nhận!!!')
        #     if not self.branch_id:
        #         raise except_orm('Thông báo', 'Xin mời bạn nhập branch khi xác nhận lịch đặt hẹn!!!')
        #     if len(self.employees) != self.customer_qty:
        #         raise except_orm('Thông báo', 'Số lượng nhân viên phải bằng số lượng khách hàng!!!')
        #     if len(self.services) < 1:
        #         raise except_orm('Thông báo', 'Bạn chưa chọn dịch vụ. Vui lòng kiểm tra lại trước khi xác nhận!!!')
        self.write({'state': 'confirmed'})

    @api.multi
    def action_working(self):
        self.state = 'working'

    @api.multi
    def action_redeem(self):
        if self.use_service_id and self.use_service_id.state != 'cancel':
            raise except_orm("Thông báo", "Đơn sử dụng dịch vụ %s đang ở trạng thái %s vui lòng hủy!" %
                             (self.use_service_id.name, self.use_service_id.state))
        view = self.env.ref('izi_use_service_card.use_service_card_form')
        return {
            'name': _('Booking to service using'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'izi.service.card.using',
            'views': [(view.id, 'form')],
            'view_id': view.id,
            'target': 'current',
            'context': {'readonly_by_pass': True,
                        'default_origin': self.name,
                        'default_customer_id': self.customer_id.id,
                        'default_pricelist_id': self.customer_id.property_product_pricelist.id,
                        'default_type': 'service',
                        'default_partner_search_id': self.customer_id.id,
                        'default_serial_code': self.customer_id.phone,
                        },
        }

    def __get_service_booking_products(self):
        products = []
        if not self.services:
            return products
        for line in self.services:
            service = self.env['product.template'].search([('default_code', '=', line.code)])
            if service:
                price_unit = service.list_price
            product = (0, 0, {'service_id': line.id,
                            'quantity': 1,
                            'price_unit': price_unit,
                            'discount': 0,
                            'amount': price_unit,})
            products.append(product)
        return products

    @api.multi
    def action_done(self):
        if self.state == 'done':
            raise except_orm("Thông báo", "Lịch hẹn này đã hoàn thành, vui lòng làm mới lại trình duyệt.")
        if self.type == 'service':
            if not self.use_service_id:
                raise except_orm("Thông báo", "Booking này chưa thu hồi dịch vụ.")

            if self.use_service_id.state != 'done':
                raise except_orm("Thông báo",
                                 "Đơn sử dụng dịch vụ %s đang ở trạng thái %s vui lòng hoàn thành!" %
                                 (self.use_service_id.name, self.use_service_id.state))
            if self.use_service_id.pos_order_id:
                self.ref_order_id = self.use_service_id.pos_order_id.id
        self.state = 'done'

    @api.multi
    def action_cancel(self):
        self.write({'state': 'cancel'})
        if not self.use_service_id:
            ctx = {'meeting_id': self.id,
                   'action_state': 'cancel',
                   'customer_id': self.customer_id.id}
            return self.env['confirm.dialog'].with_context(**ctx).get_no_sale_confirm_dialog()
        if self.use_service_id.state not in ('done', 'cancel'):
            raise except_orm("Thông báo", "Đơn sử dụng dịch vụ %s đang ở trạng thái %s vui lòng hủy!" %
                             (self.use_service_id.name, self.use_service_id.state))
            # elif self.use_service_id.state == 'done':
            #     self.use_service_id.refund()
            #     self.use_service_id.action_confirm_refund()
            #     self.use_service_id.action_done_refund()

    @api.multi
    def action_back_to_new(self):
        if self.use_service_id:
            raise except_orm("Thông báo", "Đã có đơn sử dụng dịch vụ %s!. Không thể quay lại trạng thái mới" %
                             (self.use_service_id.name))
        self.state = 'new'

    # @api.multi
    # def action_sale_order(self):
    #     view_id = self.env.ref('sale.view_order_form').id
    #     sale_order = self.create_sale_order()
    #     self.write({'state': 'order',
    #                 'ref_sale_order_id': sale_order.id})
    #     return {
    #         'type': 'ir.actions.act_window',
    #         'res_model': 'sale.order',
    #         'view_type': 'form',
    #         'view_mode': 'form',
    #         'views': [(view_id, 'form')],
    #         'target': 'current',
    #         'res_id': sale_order.id
    #     }

    # def validate_permission(self):
    #     user = self.env.user
    #     is_sale_man = user.has_group('sales_team.group_sale_salesman')
    #     is_lead = user.has_group('sales_team.group_sale_salesman_all_leads')
    #     is_manager = user.has_group('sales_team.group_sale_manager')
    #     if (is_manager or is_sale_man) and not is_lead:
    #         raise except_orm('Cảnh báo', 'Bạn không có quyền xác nhận Booking/Meeting này.')
    #     if is_lead and self.team_id != user.sale_team_id:
    #         raise except_orm('Cảnh báo', 'Bạn không có quyền xác nhận Booking/Meeting của shop khác')

    def get_employee_by_team_id(self, team_id):
        query = '''SELECT he.id 
                    FROM hr_employee he 
                    INNER JOIN res_users ru ON ru.id = he.user_id
                    WHERE ru.sale_team_id = %s'''
        self._cr.execute(query, (team_id,))
        rows = self._cr.dictfetchall()
        return [r['id'] for r in rows]

    def validate_time_with_service_time(self):
        if self.type == 'meeting':
            return
        service_time = 0
        time_booking = (datetime.strptime(self.time_to, "%Y-%m-%d %H:%M:%S") - datetime.strptime(self.time_from,
                                                                                                 "%Y-%m-%d %H:%M:%S")).seconds / 60
        for service in self.services:
            service_time += service.x_duration
        if service_time > time_booking:
            raise except_orm('Cảnh báo', 'Tổng thời gian làm các dịch vụ phải nhỏ hơn thời gian của booking')

    def get_service_booking_name(self, type):
        seq = 'ev_service_meeting_name_seq'
        if type == 'service':
            seq = 'ev_service_booking_name_seq'
        return self.env['ir.sequence'].with_context(**self._context).next_by_code(seq)

    def change_lead_state(self, lead_id, type='meeting'):
        if not lead_id:
            return
        lead = self.env['crm.lead'].browse(lead_id)
        lead_state = 'booking' if type == 'service' else 'meeting'
        lead.state = lead_state

    def validate_bed_state(self):
        if self.type == 'meeting':
            return
        # if self.customer_qty != len(self.beds):
        #     raise except_orm('Cảnh báo', 'Số lượng giường phải bằng số lượng người làm booking.')
        for bed in self.beds:
            if self.env['pos.service.bed'].get_bed_state(bed.id, datetime.strptime(self.time_from,
                                                                                   "%Y-%m-%d %H:%M:%S").strftime(
                    '%Y-%m-%d %H:%M:00'),
                                                         datetime.strptime(self.time_to, "%Y-%m-%d %H:%M:%S").strftime(
                                                             '%Y-%m-%d %H:%M:00'), self.id) == 'busy':
                raise except_orm('Cảnh báo', 'Bạn không thể tạo booking khi giường đang bận')

    def validate_employee_state(self):
        if self.type == 'meeting':
            return
        if self.customer_qty > len(self.employees):
            raise except_orm('Cảnh báo', 'Số lượng nhân viên phải bằng số lượng người làm booking.')
            # for employee in self.employees:
            #     if self.env['hr.employee'].get_employee_state(employee.id, datetime.strptime(self.time_from, "%Y-%m-%d %H:%M:%S").strftime('%Y-%m-%d %H:%M:%S'),
            #                                                   datetime.strptime(self.time_to, "%Y-%m-%d %H:%M:%S").strftime('%Y-%m-%d %H:%M:%S'), self.id) == 'busy':
            #         raise except_orm('Cảnh báo', 'Bạn không thể tạo booking khi nhân viên đang bận')

    def validate_product_ids_permission(self, vals):
        partner_id = vals.get('customer_id', None) or self.customer_id.id
        partner = self.env['res.partner'].search([('id', '=', partner_id)])
        if 'product_ids' in vals and partner.user_id.id != self.env.user.id:
            raise except_orm('Cảnh báo', 'Bạn không thẻ thêm sản phẩm dự kiến cho khách hàng bạn không chăm sóc!')

    # def create_sale_order(self):
    #     order_line = []
    #     for line in self.product_ids:
    #         price_unit = self.__get_product_price_unit(self.customer_id, line.product_id)
    #         order_line.append((0, 0, {'product_id': line.product_id.id,
    #                                   'name': line.product_id.name,
    #                                   'price_unit': price_unit,
    #                                   'product_uom': line.product_id.uom_id.id,
    #                                   'product_uom_qty': line.qty}))
    #
    #     vals = {'type': 'retail',
    #             'user_id': self.user_id.id,
    #             'team_id': self.team_id.id,
    #             'branch_id': self.branch_id.id,
    #             'date_order': self.time_from,
    #             'partner_id': self.customer_id.id,
    #             'order_line': order_line}
    #
    #     return self.env['sale.order'].create(vals)

    @staticmethod
    def __get_product_price_unit(customer, product):
        discount = customer.x_rank_id.discount_service if product.type == 'service' \
            else customer.x_rank_id.discount_product
        price = customer.property_product_pricelist.get_product_price(product, 1, customer)
        return price - ((price * discount) / 100)

    @api.multi
    def action_no_sale(self):
        ctx = {'meeting_id': self.id,
               'action_state': 'no_sale',
               'customer_id': self.customer_id.id}
        return self.env['confirm.dialog'].with_context(**ctx).get_no_sale_confirm_dialog()

    def validate_time_booking_meeting(self, vals):
        time_from = vals.get('time_from', None) or datetime.strptime(
            self.time_from, "%Y-%m-%d %H:%M:%S").strftime(DTF)
        time_to = vals.get('time_to', None) or datetime.strptime(
            self.time_to, "%Y-%m-%d %H:%M:%S").strftime(DTF)
        time_from = (datetime.strptime(time_from, DTF) + relativedelta(hours=7)).strftime(DTFR)
        time_to = (datetime.strptime(time_to, DTF) + relativedelta(hours=7)).strftime(DTFR)
        if time_from[0:4] != time_to[0:4] \
                or time_from[5:7] != time_to[5:7] \
                or time_from[8:10] != time_to[8:10]:
            raise except_orm('Thông báo', 'Thời gian đặt lịch phải trong một ngày!!!')

    def validate_exist_customer_booking_meeting(self, vals):
        """
            Trong 1 ngày 1 khách hàng:
            + Chỉ tồn tại Booking || Meeting
            + Booking/Meeting có thể có nhiều nhưng không được cùng thời điểm
        """
        customer_id = vals.get('customer_id', None) or self.customer_id.id
        time_from = vals.get('time_from', None) or datetime.strptime(
            self.time_from, "%Y-%m-%d %H:%M:%S").strftime(DTF)
        time_to = vals.get('time_from', None) or datetime.strptime(
            self.time_to, "%Y-%m-%d %H:%M:%S").strftime(DTF)
        date = datetime.strptime(time_from, DTF).strftime(DF)
        # Chỉ tồn tại Booking || Meeting
        self.validate_exists_one_of_booking_meeting_on_day(vals['type'], customer_id, date)
        # Booking/Meeting có thể có nhiều nhưng không được cùng thời điểm
        self.validate_exists_one_of_booking_meeting_on_time(vals['type'], customer_id, time_from, time_to)

    def validate_exists_one_of_booking_meeting_on_day(self, type, customer_id, date):
        query = '''SELECT name, type FROM service_booking 
                                WHERE customer_id = %s 
                                    AND state != 'cancel'
                                    AND time_from::date = %s'''
        self._cr.execute(query, (customer_id, date))
        res = self._cr.dictfetchone()
        if not res:
            return
        if res['type'] == 'service' and type == 'meeting':
            raise except_orm('Cảnh báo',
                             'Khách hàng đã tồn tại booking, vui lòng kiểm tra lại %s' % res['name'])
        if res['type'] == 'meeting' and type == 'service':
            raise except_orm('Cảnh báo',
                             'Khách hàng đã tồn tại meeting, vui lòng kiểm tra lại %s' % res['name'])

    def validate_exists_one_of_booking_meeting_on_time(self, type, customer_id, time_from, time_to):
        query = '''SELECT name FROM service_booking 
                        WHERE customer_id = %s 
                            AND type = %s 
                            AND state != 'cancel' 
                            AND ((time_from >= %s AND time_from <= %s) 
                                OR (time_to >= %s AND time_to <= %s) 
                                OR (time_from >= %s AND time_to <= %s))'''
        self._cr.execute(query, (customer_id, type, time_from, time_from, time_to, time_to, time_from, time_to))
        res = self._cr.dictfetchone()
        bm = 'Booking' if type == 'service' else 'Meeting'
        if res:
            raise except_orm('Cảnh báo',
                             'Đã tồn tại %s cho khách hàng trong khoảng thời gian này: %s' % (bm, res['name']))

    def create_event(self, is_create_event):
        if not is_create_event:
            return
        partner_ids = [self.customer_id.id]
        partner_id = self.env['res.users'].search([('id', '=', self._uid)]).partner_id.id
        partner_ids.append(partner_id)
        name_event = 'Customer meeting'
        if self.type == 'service':
            name_event = 'Service booking'
        arg = {
            'name': name_event,
            'start': datetime.strptime(
                self.time_from, "%Y-%m-%d %H:%M:%S").strftime(DTF),
            'stop': datetime.strptime(
                self.time_to, "%Y-%m-%d %H:%M:%S").strftime(DTF),
            'allday': False,
            'description': self.note,
            'partner_ids': [(6, 0, partner_ids)],
            'alarm_ids': [(4, 3)],
            'booking_id': self.id,
        }
        self.env['calendar.event'].create(arg)

    # Chuyển lịch sang lịch khách hàng


    # Tạo đơn hàng từ meeting
    @api.multi
    def action_order(self):
        view = self.env.ref('izi_crm_booking.izi_service_booking_form_pos')
        return {
            'name': _('Choice create form'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'service.booking',
            'views': [(view.id, 'form')],
            'view_id': view.id,
            'target': 'new',
            'res_id': self.id,
            'context': self.env.context,
        }

    @api.multi
    def action_pos(self):
        self.state = 'done'
        current_session = self.env['pos.session'].search(
            [('state', '=', 'opened'), ('config_id', '=', self.config_id.id)], limit=1)
        if not current_session:
            raise except_orm(("Cảnh báo!"), _('Bạn phải mở phiên trước khi tạo đơn hàng mới.'))
        if self.crm_lead_id:
            self.crm_lead_id.x_stage = 4
            stage_id = self.env['crm.stage'].search([('name', '=', 'Thắng')], limit=1)
            self.crm_lead_id.stage_id = stage_id.id
        if len(self.product_ids) != 0:
            if self.selection == 'order':
                employees = []
                employees_ids = self.env['hr.employee'].search(
                    [('user_id', 'in', [self.user_id.id, self.create_uid.id])])
                for x in employees_ids:
                    employees.append(x.id)
                PosOrder = self.env['pos.order']
                argv = {
                    'session_id': current_session.id,
                    'partner_id': self.customer_id.id,
                    'state': 'draft',
                    'x_opportunity_id': self.crm_lead_id.id,
                    'user_id': self.user_id.id,
                    'x_user_id': [(4, x) for x in employees],
                    'origin_service_booking': self.name
                }
                order_id = PosOrder.create(argv)
                self.ref_order_id = order_id.id
                for line in self.product_ids:
                    line = {
                        'product_id': line.product_id.id,
                        'qty': line.qty,
                        'price_unit': line.amount_total / line.qty if line.qty != 0 else 0,
                        'order_id': order_id.id,
                    }
                    PosOrder = self.env['pos.order.line'].create(line)
                view = self.env.ref('point_of_sale.view_pos_pos_form')
                context = self.env.context.copy()
                # context.update({'lead_employee_ids': self.create_uid.id})
                return {
                    'name': _('Choice create form'),
                    'type': 'ir.actions.act_window',
                    'view_type': 'form',
                    'view_mode': 'form',
                    'res_model': 'pos.order',
                    'views': [(view.id, 'form')],
                    'view_id': view.id,
                    'res_id': order_id.id,
                    'target': '',
                    'context': context,
                }
            elif self.selection == 'using':
                employees = []
                employees_ids = self.env['hr.employee'].search(
                    [('user_id', 'in', [self.user_id.id, self.create_uid.id])])
                for x in employees_ids:
                    employees.append(x.id)
                Using = self.env['izi.service.card.using']
                context = self.env.context.copy()
                argv = {
                    'session_id': current_session.id,
                    'customer_id': self.customer_id.id,
                    'pricelist_id': self.customer_id.property_product_pricelist.id,
                    'state': 'draft',
                    'x_opportunity_id': self.crm_lead_id.id,
                    'user_id': self.user_id.id,
                    'type': 'service',
                    'x_user_id': [(4, x) for x in employees],
                    'default_origin': self.name,
                }
                using_id = Using.create(argv)
                self.use_service_id = using_id.id
                for line in self.product_ids:
                    if line.product_id.product_tmpl_id.type == 'service' and line.product_id.default_code != 'COIN':
                        line = {
                            'service_id': line.product_id.id,
                            'quantity': line.qty,
                            'price_unit': line.amount_total / line.qty if line.qty != 0 else 0,
                            'using_id': using_id.id,
                        }
                        Detail = self.env['izi.service.card.using.line'].create(line)
                view = self.env.ref('izi_use_service_card.use_service_card_form')
                # context.update({'lead_employee_ids': self.create_uid.id})
                return {
                    'name': _('Choice create form'),
                    'type': 'ir.actions.act_window',
                    'view_type': 'form',
                    'view_mode': 'form',
                    'res_model': 'izi.service.card.using',
                    'views': [(view.id, 'form')],
                    'view_id': view.id,
                    'res_id': using_id.id,
                    'target': '',
                    'context': context,
                }
            elif self.selection == 'deposit':
                ctx = self.env.context.copy()
                ctx.update(
                    {'default_partner_id': self.customer_id.id, 'default_x_type': 'deposit', 'default_type': 'deposit',
                     'default_x_opportunity_id': self.crm_lead_id.id, 'default_session_id': current_session.id,
                     'default_user_id': self.user_id.id})
                # 'lead_employee_ids': self.create_uid.id})
                # deposit = self.env['pos.customer.deposit.line']
                # argv = {
                #     'session_id': current_session.id,
                #     'partner_id': self.partner_id.id,
                #     'state': 'draft',
                #     'x_opportunity_id': self.id,
                #     'user_id': self.user_id.id
                # }
                # deposit_id = deposit.create(argv)
                view = self.env.ref('pos_customer_deposit.pos_customer_deposit_line_form_view')
                return {
                    'name': _('Choice create form'),
                    'type': 'ir.actions.act_window',
                    'view_type': 'form',
                    'view_mode': 'form',
                    'res_model': 'pos.customer.deposit.line',
                    'views': [(view.id, 'form')],
                    'view_id': view.id,
                    'target': '',
                    'context': ctx,
                }
            else:
                PosOrder = self.env['pos.order']
                employees = []
                employees_ids = self.env['hr.employee'].search(
                    [('user_id', 'in', [self.user_id.id, self.create_uid.id])])
                for x in employees_ids:
                    employees.append(x.id)
                context = self.env.context.copy()
                argv = {
                    'session_id': current_session.id,
                    'partner_id': self.customer_id.id,
                    'state': 'draft',
                    'x_opportunity_id': self.crm_lead_id.id,
                    'user_id': self.user_id.id,
                    'x_user_id': [(4, x) for x in employees],
                    'x_type': '2',
                    'origin_service_booking': self.name,
                }
                order_id = PosOrder.create(argv)
                self.ref_order_id = order_id.id
                product_id = self.env['product.product'].search([('default_code', '=', 'COIN')], limit=1)
                line = {
                    'product_id': product_id.id,
                    'qty': 1,
                    'price_unit': 1,
                    'order_id': order_id.id,
                }
                PosOrder = self.env['pos.order.line'].create(line)
                view = self.env.ref('izi_virtual_money.view_pos_pos_form_izi_vm_sell')
                # context.update({'lead_employee_ids': self.create_uid.id})
                return {
                    'name': _('Choice create form'),
                    'type': 'ir.actions.act_window',
                    'view_type': 'form',
                    'view_mode': 'form',
                    'res_model': 'pos.order',
                    'views': [(view.id, 'form')],
                    'view_id': view.id,
                    'res_id': order_id.id,
                    'target': '',
                    'context': self.env.context,
                }

        else:
            if self.selection == 'order':
                ctx = self.env.context.copy()
                ctx.update(
                    {'default_partner_id': self.customer_id.id, 'default_x_opportunity_id': self.crm_lead_id.id,
                     'default_user_id': self.user_id.id, 'default_session_id': current_session.id,
                     'default_x_type': '1', 'default_origin_service_booking': self.name})
                # 'lead_employee_ids': self.create_uid.id,
                view = self.env.ref('point_of_sale.view_pos_pos_form')
                return {
                    'name': _('Choice create form'),
                    'type': 'ir.actions.act_window',
                    'view_type': 'form',
                    'view_mode': 'form',
                    'res_model': 'pos.order',
                    'views': [(view.id, 'form')],
                    'view_id': view.id,
                    'target': '',
                    'context': ctx,
                }

            elif self.selection == 'using':
                ctx = self.env.context.copy()
                ctx.update({'default_customer_id': self.customer_id.id, 'default_type': 'service',
                            'default_x_opportunity_id': self.crm_lead_id.id, 'default_session_id': current_session.id,
                            'default_user_id': self.user_id.id, 'default_origin': self.name})
                # 'lead_employee_ids': self.create_uid.id})
                view = self.env.ref('izi_use_service_card.use_service_card_form')
                return {
                    'name': _('Choice create form'),
                    'type': 'ir.actions.act_window',
                    'view_type': 'form',
                    'view_mode': 'form',
                    'res_model': 'izi.service.card.using',
                    'views': [(view.id, 'form')],
                    'view_id': view.id,
                    'target': '',
                    'context': ctx,
                }
            elif self.selection == 'deposit':
                ctx = self.env.context.copy()
                ctx.update(
                    {'default_partner_id': self.customer_id.id, 'default_x_type': 'deposit', 'default_type': 'deposit',
                     'default_x_opportunity_id': self.crm_lead_id.id, 'default_session_id': current_session.id,
                     'default_user_id': self.user_id.id})
                # 'lead_employee_ids': self.create_uid.id})
                # deposit = self.env['pos.customer.deposit.line']
                # argv = {
                #     'session_id': current_session.id,
                #     'partner_id': self.partner_id.id,
                #     'state': 'draft',
                #     'x_opportunity_id': self.id,
                #     'user_id': self.user_id.id
                # }
                # deposit_id = deposit.create(argv)
                view = self.env.ref('pos_customer_deposit.pos_customer_deposit_line_form_view')
                return {
                    'name': _('Choice create form'),
                    'type': 'ir.actions.act_window',
                    'view_type': 'form',
                    'view_mode': 'form',
                    'res_model': 'pos.customer.deposit.line',
                    'views': [(view.id, 'form')],
                    'view_id': view.id,
                    'target': '',
                    'context': ctx,
                }
            else:
                ctx = self.env.context.copy()
                ctx.update(
                    {'default_partner_id': self.customer_id.id, 'izi_sell_vm': True,
                     'default_x_opportunity_id': self.crm_lead_id.id,
                     'default_user_id': self.user_id.id, 'default_session_id': current_session.id,
                     'default_x_type': '2', 'default_origin_service_booking': self.name})
                # 'lead_employee_ids': self.create_uid.id,
                view = self.env.ref('izi_virtual_money.view_pos_pos_form_izi_vm_sell')
                return {
                    'name': _('Choice create form'),
                    'type': 'ir.actions.act_window',
                    'view_type': 'form',
                    'view_mode': 'form',
                    'res_model': 'pos.order',
                    'views': [(view.id, 'form')],
                    'view_id': view.id,
                    'target': '',
                    'context': ctx,
                }

    # Ở trạng thái hủy sẽ có thêm nút booking/meeting

    @api.multi
    def action_booking(self):
        booking = self.env['service.booking'].search([('parent_id', '=', self.id)])
        if booking:
            raise except_orm('Cảnh báo',
                             'Khách hàng đã tồn tại booking, vui lòng kiểm tra lại %s' % booking.name)
        return self.__get_view('service')

    @api.multi
    def action_meeting(self):
        meeting = self.env['service.booking'].search([('parent_id', '=', self.id)])
        if meeting:
            raise except_orm('Cảnh báo',
                             'Khách hàng đã tồn tại meeting, vui lòng kiểm tra lại %s' % meeting.name)
        return self.__get_view('meeting')

    def __get_view(self, type):
        view_id = self.env.ref('izi_crm_booking.service_booking_form_view').id
        ctx = {
            'default_crm_lead_id': self.crm_lead_id.id,
            'default_type': self.type,
            'default_customer_id': self.customer_id.id,
            'default_product_ids': self.product_ids,
            'default_team_id': self.team_id.id if self.team_id else False,
            'default_user_id': self.user_id.id if self.user_id else False,
            'default_parent_id': self.id
        }
        return {
            'name': type[0].upper() + type[1:],
            'type': 'ir.actions.act_window',
            'res_model': 'service.booking',
            'view_type': 'form',
            'view_mode': 'form',
            'views': [(view_id, 'form')],
            'target': 'current',
            'context': ctx,
        }
