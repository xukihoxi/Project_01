# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from datetime import datetime, timedelta
from odoo.exceptions import except_orm, ValidationError, UserError


class ProductSearchCard(models.TransientModel):
    _name = 'izi.product.search.card'

    # @api.model
    # def _get_brand(self):
    #     if not self.env.user.branch_id: raise except_orm('Thông báo', 'Người dùng %s chưa chọn chi nhánh. Liên hệ quản trị viên để được giải quyết!' % (str(self.env.user.name)))
    #     if not self.env.user.branch_id.brand_id: raise except_orm('Thông báo', 'Chi nhánh %s chưa chọn thương hiệu. Liên hệ quản trị viên để được giải quyết!' % (str(self.env.user.branch_id.brand_id)))
    #
    #     return self.env.user.branch_id.brand_id

    partner_id = fields.Many2one('res.partner', "Partner")
    serial = fields.Char("Code", required=True)
    name = fields.Char()
    x_name = fields.Char('Name customer')
    x_code = fields.Char('Code customer')
    x_old_code = fields.Char('Code old customer')
    x_rank = fields.Char(string=u'Rank')
    x_birthday = fields.Date(u'Birthday')
    x_sex = fields.Selection([('male', 'Male'), ('female', 'Female'), ('other', 'Other')], string="Sex")
    x_crm_lead_tag_ids = fields.Many2many('crm.lead.tag', string="Tag")
    x_link_facebook = fields.Char(string="Link facebook")
    x_link_zalo = fields.Char(string="Link zalo")
    credit = fields.Float('Credit')
    email = fields.Char()
    phone = fields.Char()
    mobile = fields.Char()
    lot_id = fields.Many2one('stock.production.lot')
    old_revenue = fields.Float("Old Revenue")
    total_revenue = fields.Float("Total Revenue")
    x_manage_user_id = fields.Many2one('res.users', "Manage User")
    brand_id = fields.Many2one('res.brand', string="Brand")
    is_load_image = fields.Boolean(string="Load image", default=False)

    check_card = fields.Boolean()
    check_pmh = fields.Boolean()
    pmh_ids = fields.One2many('izi.pmh.service.lot.transient', 'x_search_id', readonly=1)
    card_ids = fields.One2many('izi.card.service.lot.transient', 'x_search_id', readonly=1)
    card_detail_ids = fields.One2many('izi.service.card.detail.transient', 'x_search_id', string='Detail', readonly=1)
    use_card_ids = fields.One2many('izi.use.card.detail.history.transient', 'x_search_id', string='Detail', readonly=1)
    exchange_card_ids = fields.One2many('izi.exchange.card.detail.history.transient', 'x_search_id', string='Detail',
                                        readonly=1)
    current_detail_line_ids = fields.One2many('izi.current.exchange.service.transient', 'x_search_id',
                                              'Curent exchange')

    virtual_money_ids = fields.One2many('pos.virtual.money.transient', 'x_search_id', u'Virtual money', readonly=1)
    virtual_money_history_ids = fields.One2many('pos.virtual.money.history.transient', 'x_search_id',
                                                u'Virtual money history', readonly=1)
    order_ids = fields.One2many('izi.pos.order.line.transient', 'x_search_id', string='Order', readonly=1)
    x_point_history_ids = fields.One2many('izi.vip.point.history.transient', 'x_search_id', string='Point', readonly=1)
    x_revenue_ids = fields.One2many('crm.vip.customer.revenue.transient', 'x_search_id', u'Revenue', readonly=1)
    vip_history_ids = fields.One2many('crm.vip.customer.history.transient', 'x_search_id', u'Lịch sử lên hạng',
                                      readonly=1)
    debit_product_ids = fields.One2many('debit.product.transient', 'x_search_id', u'Quản lý nợ hàng', readonly=1)
    invoice_ids = fields.One2many('invoice.customer.transient', 'x_search_id', u'Quản lý công nợ', readonly=1)
    deposit_ids = fields.One2many('pos.customer.deposit.transient', 'x_search_id', u'Quanr lý tiền đặt cọc', readonly=1)
    make_payment_ids = fields.One2many('invoice.make.payment.transient', 'x_search_id', u'Quản lý thanh toán công nợ', readonly=1)
    return_product_ids = fields.One2many('return.product.transient','x_search_id', u'Quản lý trả hàng', readonly=1)
    amount_money = fields.Float(compute='_compute_amount', string='Total')
    amount_money_use = fields.Float(compute='_compute_amount', string='Total')
    x_total_point = fields.Float(compute='_compute_amount', string='Total')
    x_total_revenue = fields.Float(compute='_compute_amount', string='Total')
    x_partner_note_ids = fields.One2many('res.partner.note', 'x_search_id', readonly=1)
    destroy_service_ids = fields.One2many('izi.pos.destroy.service.line.transient', 'x_search_id', readonly=1)
    # Sáng la thêm 16/12
    amount_total_money = fields.Float(compute='_compute_amount', string='Tổng tiền')
    # xem anh khahs hàng
    image_ids = fields.One2many('image.service.transient', 'x_search_id', readonly=1)
    total_deposit = fields.Float(compute='_compute_amount', string="Tổng")
    service_calender_ids = fields.One2many('crm.service.calender.reminder.transient', 'x_search_id', u'Lịch sử chăm sóc khách hàng', readonly=1)

    @api.onchange('partner_id')
    def action_onchange_partner(self):
        if self.partner_id.phone:
            self.serial = self.partner_id.phone
        elif self.partner_id.mobile:
            self.serial = self.partner_id.mobile

    @api.onchange('brand_id')
    def _onchange_brand_id(self):
        BrandObj = self.env['res.brand']
        user = self.env['res.users'].search([('id', '=', self._uid)], limit=1)
        if not user.branch_ids: raise except_orm('Thông báo', 'Người dùng %s chưa chọn chi nhánh cho phép. Vui lòng liên hệ quản trị để được giải quyết' % (
                                                               str(user.name)))
        for branch in user.branch_ids:
            if not branch: raise except_orm('Thông báo', 'Chi nhánh %s chưa chọn thương hiệu. Vui lòng liên hệ quản trị để được giải quyết' % (
                                                                    str(branch.name)))
        branch_ids = [user.branch_id and user.branch_id.id or 0]
        for branch in user.branch_ids:
            branch_ids.append(branch.id)
        brand_ids = BrandObj.get_brand_ids_by_branches(branch_ids)
        return {
            'domain': {
                'brand_id': [('id', 'in', brand_ids)]
            }
        }

    @api.depends('virtual_money_ids.money', 'virtual_money_history_ids.amount')
    def _compute_amount(self):
        for detail in self:
            total1 = 0
            total2 = 0
            total3 = 0
            total4 = 0
            total5 = 0
            total6 = 0
            for line in detail.virtual_money_ids:
                if line.state == 'ready':
                    if line.debt_amount > 0:
                        if line.money_order >0:
                            total1 += line.money_order - line.debt_amount - line.money_used
                        else:
                            total1 += line.money - line.debt_amount - line.money_used
                    else:
                        total1 += line.money - line.debt_amount - line.money_used
            for line in detail.virtual_money_history_ids:
                total2 = total2 + line.amount
            for line in detail.x_point_history_ids:
                total3 = total3 + line.point
            for line in detail.x_revenue_ids:
                total4 = total4 + line.amount
            for line in detail.virtual_money_ids:
                if line.state == 'ready':
                    total5 += line.money - line.money_used
            for line in detail.deposit_ids:
                if line.type == 'deposit':
                    total6 += line.amount
                if line.type == 'payment':
                    total6 -= line.amount
                if line.type == 'cash':
                    total6 -= line.amount
            detail.amount_money = total1
            detail.amount_money_use = total2
            detail.x_total_point = total3
            detail.x_total_revenue = total4
            detail.amount_total_money = total5
            detail.total_deposit = total6


    @api.onchange('serial')
    def _onchange_name(self):
        if self.serial:
            self.name = self.serial.upper().strip()

    @api.multi
    def action_check_card(self):
        if not self.serial:
            raise except_orm(("Cảnh báo!"), ('Xin nhập mã trước khi tìm kiếm'))
        else:
            for l in self.pmh_ids:
                l.unlink()
            for l in self.card_ids:
                l.unlink()
            for l in self.card_detail_ids:
                l.unlink()
            for l in self.use_card_ids:
                l.unlink()
            for l in self.exchange_card_ids:
                l.unlink()
            for l in self.current_detail_line_ids:
                l.unlink()
            for l in self.virtual_money_ids:
                l.unlink()
            for l in self.virtual_money_history_ids:
                l.unlink()
            for l in self.order_ids:
                l.unlink()
            for l in self.x_point_history_ids:
                l.unlink()
            for l in self.x_revenue_ids:
                l.unlink()
            for l in self.vip_history_ids:
                l.unlink()
            for l in self.debit_product_ids:
                l.unlink()
            for l in self.invoice_ids:
                l.unlink()
            for l in self.deposit_ids:
                l.unlink()
            for l in self.make_payment_ids:
                l.unlink()
            for l in self.return_product_ids:
                l.unlink()
            for l in self.x_partner_note_ids:
                l.unlink()
            for l in self.destroy_service_ids:
                l.unlink()
            for l in self.image_ids:
                l.unlink()
            for l in self.service_calender_ids:
                l.unlink()
            serial = self.serial.upper().strip()
            lot = self.env['stock.production.lot'].sudo().search([('name', '=', serial)])
            user_obj = self.env['res.users']
            ObjPartner = self.env['res.partner']
            user_id = self.env['res.users'].search([('id', '=', self._uid)])
            crm_team_ids = self.env['crm.team'].search([('x_branch_id', '=', user_id.branch_id.id)])
            group_leader_shop = user_obj.has_group('izi_res_permissions.group_leader_shop')
            group_consultant = user_obj.has_group('izi_res_permissions.group_consultant')
            group_inventory_accounting = user_obj.has_group('izi_res_permissions.group_inventory_accounting')
            group_cashier = user_obj.has_group('izi_res_permissions.group_cashier')
            group_therapist = user_obj.has_group('izi_res_permissions.group_therapist')
            group_receptionist = user_obj.has_group('izi_res_permissions.group_receptionist')
            group_member_uid_telesales = user_obj.has_group('izi_res_permissions.group_member_uid_telesales')

            group_business_manager = user_obj.has_group('izi_res_permissions.group_business_manager')

            if lot:
                if lot.product_id.product_tmpl_id.x_type_card == 'pmh':
                    self.check_pmh = True
                    self.check_card = False
                else:
                    self.check_card = True
                    self.check_pmh = False
            else:
                self.check_card = True
                self.check_pmh = True
                if group_business_manager or group_leader_shop or group_cashier or group_receptionist or group_consultant or group_member_uid_telesales:
                    customer = ObjPartner.sudo().search(['|', ('phone', '=', serial), ('mobile', '=', serial), ('x_brand_id', '=', self.brand_id.id)])
                else:
                    customer = False
                if not customer:
                    raise except_orm('Thông báo', 'Không tìm thấy KH có số điện thoại %s' % (str(serial)))
                elif len(customer) > 1:
                    raise except_orm('Thông báo', 'Có nhiều hơn 1 KH đang sở hữu cùng số điện thoại %s' % (str(serial)))
                lot = self.env['stock.production.lot'].sudo().search([('x_customer_id', '=', customer.id)])
            pmh_ids = self.env['izi.pmh.service.lot.transient']
            card_ids = self.env['izi.card.service.lot.transient']
            card_detail_ids = self.env['izi.service.card.detail.transient']
            use_card_ids = self.env['izi.use.card.detail.history.transient']
            exchange_card_ids = self.env['izi.exchange.card.detail.history.transient']
            current_exchange_card_ids = self.env['izi.current.exchange.service.transient']
            new_exchange_card_ids = self.env['izi.new.exchange.service.transient']
            order_ids = self.env['izi.pos.order.line.transient']
            x_point_history_ids = self.env['izi.vip.point.history.transient']
            x_revenue_ids = self.env['crm.vip.customer.revenue.transient']

            virtual_money_ids = self.env['pos.virtual.money.transient']
            virtual_money_history_ids = self.env['pos.virtual.money.history.transient']
            note_ids = self.env['res.partner.note']
            destroy_service_ids = self.env['izi.pos.destroy.service.line.transient']
            image_ids = self.env['image.service.transient']
            # Sangla them lích sử chăm sóc khách hàng
            service_calender_reminder_ids = self.env['crm.service.calender.reminder.transient']
            for index in lot:
                for line in index:
                    # tdv,pmh
                    vals1 = {
                        'name': line.name,
                        'product_id': line.product_id.id,
                        'x_discount': line.x_discount,
                        'x_amount': line.x_amount,
                        'x_status': line.x_status,
                        'life_date': line.life_date,
                        'x_customer_id': line.x_customer_id.id,
                        'x_user_id': line.x_user_id.id,
                        'x_search_id': self.id,
                    }
                    order = self.env['pos.order.line'].sudo().search([('lot_name', '=', line.name), ('qty', '>', 0)], limit=1)
                    vals1.update({
                        'order_id': order.order_id.id
                    })
                    if line.product_id.product_tmpl_id.x_type_card != 'pmh':
                        card_ids.create(vals1)
                    else:
                        order_payment = self.env['account.bank.statement.line'].sudo().search(
                            [('x_vc_name', '=', line.name), ('amount', '>', 0)], limit=1)
                        vals1.update({
                            'order_payment_id': order_payment.pos_statement_id.id
                        })
                        pmh_ids.create(vals1)
                    rf_order = self.env['pos.order.line'].sudo().search([('lot_name', '=', line.name), ('qty', '<', 0)], limit=1)
                    if rf_order.id != False:
                        vals1.update({
                            'order_id': rf_order.order_id.id
                        })
                        if line.product_id.product_tmpl_id.x_type_card in ('tdv', 'tbh'):
                            card_ids.create(vals1)
                        else:
                            order_payment = self.env['account.bank.statement.line'].sudo().search(
                                [('x_vc_name', '=', line.name), ('amount', '<', 0)], limit=1)
                            vals1.update({
                                'order_payment_id': order_payment.pos_statement_id.id
                            })
                            pmh_ids.create(vals1)

                    # dichvutrongthe
                    for detail in line.x_card_detail_ids:
                        debit = False
                        if line.x_order_id.invoice_id:
                            if line.x_order_id.invoice_id.residual > 0:
                                debit = True
                        states = detail.state
                        date = datetime.strptime(line.life_date, '%Y-%m-%d %H:%M:%S') + timedelta(days=1)
                        day_now = datetime.today().replace(minute=0, hour=0, second=0)
                        if date < day_now:
                            states = 'expired'
                        vals2 = {
                            'lot_id': line.id,
                            'life_date': line.life_date,
                            'product_id': detail.product_id.id,
                            'total_qty': detail.total_qty,
                            'qty_hand': detail.qty_hand,
                            'qty_use': detail.qty_use,
                            'price_unit': detail.price_unit,
                            'remain_amount': detail.remain_amount,
                            'amount_total': detail.amount_total,
                            # 'payment_amount': detail.amount_payment,
                            'x_search_id': self.id,
                            'state': states,
                            'debit': debit,
                            'note': detail.note,
                        }
                        card_detail_ids.create(vals2)
                    # su dung dich vu
                    use_card_line_obj = self.env['izi.service.card.using.line'].sudo().search([('serial_id', '=', line.id)])
                    for use_card_line_id in use_card_line_obj:
                        employee = ''
                        for x in use_card_line_id.employee_ids:
                            employee = employee + ', ' + str(x.name)
                        for y in use_card_line_id.doctor_ids:
                            employee = employee + ', ' + str(y.name)
                        vals3 = {
                            'redeem_date': use_card_line_id.using_id.redeem_date,
                            'service_id': use_card_line_id.service_id.id,
                            'quantity': use_card_line_id.quantity,
                            'uom_id': use_card_line_id.uom_id.id,
                            'employee': employee[1:],
                            'using_id': use_card_line_id.using_id.id,
                            'serial_id': use_card_line_id.serial_id.id,
                            'price_unit': use_card_line_id.price_unit,
                            'state': use_card_line_id.using_id.state,
                            'x_search_id': self.id,
                            'customer_sign': use_card_line_id.using_id.signature_image,
                            'note': use_card_line_id.note,
                            'type': 'card',
                        }
                        use_card_ids.create(vals3)

                    # doi dv
                    exchange_line_obj = self.env['izi.pos.exchange.service'].sudo().search([('product_lot_id', '=', line.id)])
                    for echange_id in exchange_line_obj:
                        vals4 = {
                            'session_id': echange_id.session_id.id,
                            'exchange_id': echange_id.id,
                            'exchange_date': echange_id.exchange_date,
                            'x_search_id': self.id,
                        }
                        ex = exchange_card_ids.create(vals4)
                        for current in echange_id.current_detail_line_ids:
                            vals41 = {
                                'service_id': current.service_id.id,
                                'total_count': current.total_count,
                                'hand_count': current.hand_count,
                                'used_count': current.used_count,
                                'to_subtract_count': current.to_subtract_count,
                                'price_unit': current.price_unit,
                                'amount_subtract': current.amount_subtract,
                                'exchange_id': ex.id,
                                'x_search_id': self.id,
                                'exchange_detail_id': echange_id.id,
                                'lot_id': echange_id.product_lot_id.id,
                                'date': echange_id.exchange_date,
                            }
                            current_exchange_card_ids.create(vals41)
                        for new in echange_id.new_service_detail_line_ids:
                            vals42 = {
                                'service_id': new.service_id.id,
                                'new_count': new.new_count,
                                'amount_total': new.amount_total,
                                'price_unit': new.price_unit,
                                'exchange_id': ex.id,
                            }
                            new_exchange_card_ids.create(vals42)
            #         HỦy dịch vụ
                    destroy_service_obj = self.env['pos.destroy.service'].sudo().search([('product_lot_id', '=', line.id)])
                    for destroy_id in destroy_service_obj:
                        for detail in destroy_id.destroy_service_detail_lines:
                            if detail.service_id.id == destroy_id.session_id.config_id.x_charge_refund_id.id:
                                continue
                            argvs = {
                                'date': destroy_id.date,
                                'lot_id': destroy_id.product_lot_id.id,
                                'service_id': detail.service_id.id,
                                'new_count': detail.quantity,
                                'price_unit': detail.price_unit,
                                'amount_total': detail.price_subtotal_incl,
                                # 'destroy_id': ex.id,
                                'pos_destroy_service_id': destroy_id.id,
                                'x_search_id': self.id,
                            }
                            destroy_service_ids.create(argvs)
            if self.check_pmh == True and self.check_card == True:
                self._search_customer(customer)
                order = self.env['pos.order'].sudo().search([('partner_id', '=', customer.id)])
                for order_id in order:
                    for line in order_id.lines:
                        vals7 = {
                            'product_id': line.product_id.id,
                            'lot_name': line.lot_name,
                            'qty': line.qty,
                            'price_unit': line.price_unit,
                            'discount': line.discount,
                            'x_discount': line.x_discount,
                            'price_subtotal_incl': line.price_subtotal_incl,
                            'order_id': order_id.id,
                            'date_order': order_id.date_order,
                            'user_id': order_id.user_id.id,
                            'state': order_id.state,
                            'x_search_id': self.id,
                            'x_type': order_id.x_type,
                        }
                        order_ids.create(vals7)

                for tt in customer.virtual_money_ids:
                    payment_amount = 0
                    if tt.typex == '1':
                        money_order = tt.order_id.amount_total
                        payment_amount = tt.order_id.amount_total - tt.debt_amount
                    else:
                        payment_amount = 0
                        money_order = 0
                    vals5 = {
                        'money': tt.money,
                        'money_order':money_order,
                        'order_id': tt.order_id.id,
                        'debt_amount': tt.debt_amount,
                        'expired': tt.expired,
                        'money_used': tt.money_used,
                        'typex': tt.typex,
                        'x_search_id': self.id,
                        'state': tt.state,
                        'payment_amount':payment_amount,
                    }
                    virtual_money_ids.create(vals5)
                #         Note trong res_partner
                for tt in customer:
                    note_ids.create({
                        'note': tt.comment,
                        'x_search_id': self.id,
                    })

                for tt in customer.virtual_money_history_ids:
                    service = ''
                    for i in tt.order_id.lines:
                        service = service + str(i.product_id.product_tmpl_id.name) + ','
                    vals6 = {
                        'order_id': tt.order_id.id,
                        'statement_id': tt.statement_id.id,
                        'amount': tt.amount,
                        'x_search_id': self.id,
                        'date': tt.create_date,
                        'service': service,
                    }
                    virtual_money_history_ids.create(vals6)
                for tt in customer.x_point_history_ids:
                    vals8 = {
                        'point': tt.point,
                        'order_id': tt.order_id.id,
                        'date': tt.date,
                        'exchange_id': tt.exchange_id.id,
                        'x_search_id': self.id,
                    }
                    x_point_history_ids.create(vals8)
                for tt in customer.x_revenue_ids:
                    vals9 = {
                        'order_id': tt.order_id.id,
                        'journal_id':tt.journal_id.id,
                        'amount': tt.amount,
                        'date': tt.date,
                        'x_search_id': self.id,
                    }
                    x_revenue_ids.create(vals9)
                new_revenue = 0
                for tt in customer.x_revenue_ids:
                    new_revenue += tt.amount
                self.x_name = customer.name
                self.x_code = customer.x_code
                self.x_old_code = customer.x_old_code
                self.x_birthday = customer.x_birthday
                self.x_sex = customer.x_sex
                self.x_crm_lead_tag_ids = customer.x_crm_lead_tag_ids
                self.x_link_facebook = customer.x_link_facebook
                self.x_link_zalo = customer.x_link_zalo
                self.x_rank = customer.x_rank.name
                self.email = customer.email
                self.phone = customer.phone
                self.mobile = customer.mobile
                self.credit = customer.credit
                self.old_revenue = customer.x_revenue_old
                self.total_revenue = customer.x_revenue_old + new_revenue
                self.x_manage_user_id = customer.x_manage_user_id.id


                use_card_line_obj = self.env['izi.service.card.using'].sudo().search(
                    [('customer_id', '=', customer.id), ('type', '!=', 'card')])
                for use_card_line_ids in use_card_line_obj:
                    for use_card_line_id in use_card_line_ids.service_card1_ids:
                        employee = ''
                        for x in use_card_line_id.employee_ids:
                            employee = employee + ', ' + str(x.name)
                        for y in use_card_line_id.doctor_ids:
                            employee = employee + ', ' + str(y.name)
                        vals3 = {
                            'order_id': use_card_line_ids.pos_order_id.id,
                            'redeem_date': use_card_line_id.using_id.redeem_date,
                            'service_id': use_card_line_id.service_id.id,
                            'quantity': use_card_line_id.quantity,
                            'uom_id': use_card_line_id.uom_id.id,
                            'employee': employee[1:],
                            'using_id': use_card_line_id.using_id.id,
                            'serial_id': use_card_line_id.serial_id.id,
                            'price_unit': use_card_line_id.price_unit,
                            'state': use_card_line_ids.state,
                            'x_search_id': self.id,
                            'customer_sign': use_card_line_id.using_id.signature_image,
                            'note': use_card_line_id.note,
                            'type': use_card_line_id.using_id.type,
                        }
                        use_card_ids.create(vals3)
                if self.is_load_image:
                    use_card_line_image_obj = self.env['izi.service.card.using'].sudo().search(
                        [('customer_id', '=', customer.id)])
                    for use_service_card_ids in use_card_line_image_obj:
                        for i in use_service_card_ids.old_image_ids:
                            vals11 = {
                                'image': i.image_small,
                                'use_service_id': use_service_card_ids.id,
                                'date': use_service_card_ids.redeem_date,
                                'x_search_id': self.id,
                            }
                            image_ids.create(vals11)
                        for i in use_service_card_ids.new_image_ids:
                            vals11 = {
                                'image': i.image_small,
                                'use_service_id': use_service_card_ids.id,
                                'date': use_service_card_ids.redeem_date,
                                'x_search_id': self.id,
                            }
                            image_ids.create(vals11)
                # for x in customer.service_calender_remider_ids:
                #     vals12 = {
                #         'date': x.date,
                #         'product_id': x.product_id.id,
                #         'note': x.note,
                #         'description': x.description,
                #         'service_calender_reminder_id': x.service_calender_reminder_id.id,
                #         'type': x.type,
                #         'total_quantity': x.total_quantity,
                #         'quantity_used': x.quantity_used,
                #         'origin': x.origin,
                #         'note_before_custom': x.note_before_custom,
                #         'employee_id': x.employee_id.id,
                #         'master_type': x.service_calender_reminder_id.type,
                #         'x_search_id': self.id,
                #     }
                #     service_calender_reminder_ids.create(vals12)
            else:
                self.lot_id = lot.id
            return True

    def _search_customer(self, partner_id):
        if partner_id:
            vip_history_ids = self.env['crm.vip.customer.history.transient']
            debit_product_ids = self.env['debit.product.transient']
            invoice_ids = self.env['invoice.customer.transient']
            deposit_ids = self.env['pos.customer.deposit.transient']
            make_payment_ids = self.env['invoice.make.payment.transient']
            return_product_ids = self.env['return.product.transient']
            # lich su len hang
            VipCustomerHistory = self.env['crm.vip.customer.history'].sudo().search([('partner_id', '=', partner_id.id)])
            for vip in VipCustomerHistory:
                vals1 = {
                    'x_search_id': self.id,
                    'rank_current': vip.rank_current.id,
                    'rank_request': vip.rank_request.id,
                    'state': vip.state,
                    'approved_uid': vip.approved_uid.id,
                    'date': vip.create_date,
                    'approved_date': vip.approved_date,

                }
                vip_history_ids.create(vals1)
            # no hang
            debit = self.env['pos.debit.good'].sudo().search([('partner_id', '=', partner_id.id)], limit=1)
            if debit.id != False:
                for x in debit.line_ids:
                    vals2 = {
                        'x_search_id': self.id,
                        'debit_id': debit.id,
                        'product_id': x.product_id.id,
                        'qty': x.qty,
                        'qty_depot': x.qty_depot,
                        'qty_debit': x.qty_debit,
                        'qty_transfer': x.qty_transfer,
                        'order_id': x.order_id.id,
                        'date': x.date,
                        'note': x.note,
                        # 'state': debit.state,
                    }
                    debit_product_ids.create(vals2)
            # cong no
            for account in partner_id.x_account_invoices:
                name = account.reference
                order_id = self.env['pos.order'].sudo().search([('name', '=', name)], limit=1)
                vals3 = {
                    'x_search_id': self.id,
                    'order_id': order_id.id,
                    'number': account.number,
                    'amount_total': account.amount_total,
                    'residual': account.residual,
                    'date_invoice': account.date_invoice,
                    'date_due': account.date_due,
                    'state': account.state,
                    'invoice_id': account.id,
                }
                invoice_ids.create(vals3)
            # tiền đặt cọc

            deposit = self.env['pos.customer.deposit'].sudo().search([('partner_id', '=', partner_id.id)], limit=1)
            if len(deposit) > 0:
                deposit_line = self.env['pos.customer.deposit.line'].sudo().search([('deposit_id', '=', deposit.id)])
                for tmp in deposit_line:
                    vals9 = {
                        'x_search_id': self.id,
                        'deposit_id': tmp.id,
                        'session_id': tmp.session_id.id if tmp.session_id  else False,
                        'order_id': tmp.order_id.id if tmp.order_id  else False,
                        'amount': tmp.amount,
                        'date': tmp.date,
                        'type': tmp.type,
                        'note': tmp.note,
                    }
                    deposit_ids.create(vals9)
            # lịch sử thanh toán
            make_pament = self.env['account.payment'].sudo().search([('partner_id', '=', partner_id.id),('payment_type','=','inbound'),('state','=','posted')])
            if len(make_pament)>0:
                for line in make_pament:
                    vals10 = {
                        'x_search_id': self.id,
                        'journal_id': line.journal_id.id,
                        'invoice_ids':[(6, 0, line.invoice_ids.ids)],
                        'amount': line.amount,
                        'payment_id': line.id,
                        'payment_date':line.payment_date,
                    }
                    make_payment_ids.create(vals10)
            # pos_customer_deposit = self.env['pos.customer.deposit.line'].sudo().search([('partner_id', '=', partner_id.id)])
            # if len(pos_customer_deposit) >0:
            #     for line in pos_customer_deposit:
            #         if (line.journal_id.type in ('bank', 'cash')):
            #             vals10 = {
            #                 'x_search_id': self.id,
            #                 'journal_id': line.journal_id.id,
            #                 # 'invoice_ids': [(6, 0, line.invoice_ids.ids)],
            #                 'amount': line.amount,
            #                 # 'payment_id': line.id,
            #                 'payment_date': line.date,
            #             }
            #             make_payment_ids.create(vals10)
            #lịch sử công nợ
            debit_good = self.env['pos.debit.good'].sudo().search([('partner_id', '=', partner_id.id)])
            if len(debit_good):
                for line in debit_good:
                    pick = self.env['stock.picking'].sudo().search([('origin','=',line.name)])
                    for line2 in pick:
                        for x in line2.move_lines:
                            vals11 = {
                                'x_search_id': self.id,
                                'picking_id': line2.id,
                                'debit_good_id':line.id,
                                'product_id': x.product_id.id,
                                'quantity_done': x.quantity_done,
                                'product_uom': x.product_uom.id,
                                'scheduled_date': line2.scheduled_date,
                            }
                            return_product_ids.create(vals11)

    @api.multi
    def action_create_pos_order(self):
        user_id = self.env['res.users'].search([('id', '=', self.env.uid)], limit=1)
        config_id = user_id.x_pos_config_id.id
        current_session = self.env['pos.session'].search(
            [('state', '=', 'opened'), ('config_id', '=', config_id)], limit=1)
        if not current_session:
            raise except_orm(("Cảnh báo!"), _('Bạn phải mở phiên trước khi tạo đơn hàng mới.'))
        partner_obj = self.env['res.partner'].search([('x_code', '=', self.x_code)])
        if len(partner_obj) > 1:
            raise except_orm('Thông báo!', ("Có 2 KH có trung mã. VUi lòng liên hệ Admintrantor"))
        if len(partner_obj) == 0:
            raise except_orm('Thông báo!', ("Không có mã KH. VUi lòng liên hệ Admintrantor"))
        ctx = self.env.context.copy()
        ctx.update(
            {'default_partner_id': partner_obj.id,
             'default_user_id': self.env.uid, 'default_session_id': current_session.id, })
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

    @api.multi
    def action_create_pos_coin(self):
        user_id = self.env['res.users'].search([('id', '=', self.env.uid)], limit=1)
        config_id = user_id.x_pos_config_id.id
        current_session = self.env['pos.session'].search(
            [('state', '=', 'opened'), ('config_id', '=', config_id)], limit=1)
        if not current_session:
            raise except_orm(("Cảnh báo!"), _('Bạn phải mở phiên trước khi tạo đơn hàng mới.'))
        partner_obj = self.env['res.partner'].search([('x_code', '=', self.x_code)])
        if len(partner_obj) > 1:
            raise except_orm('Thông báo!', ("Có 2 KH có trung mã. VUi lòng liên hệ Admintrantor"))
        if len(partner_obj) == 0:
            raise except_orm('Thông báo!', ("Không có mã KH. VUi lòng liên hệ Admintrantor"))
        ctx = self.env.context.copy()
        ctx.update(
            {'default_partner_id': partner_obj.id, 'izi_sell_vm': True,
             'default_user_id': self.env.uid, 'default_session_id': current_session.id, })
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

    @api.multi
    def action_create_deposit(self):
        user_id = self.env['res.users'].search([('id', '=', self.env.uid)], limit=1)
        config_id = user_id.x_pos_config_id.id
        current_session = self.env['pos.session'].search(
            [('state', '=', 'opened'), ('config_id', '=', config_id)], limit=1)
        if not current_session:
            raise except_orm(("Cảnh báo!"), _('Bạn phải mở phiên trước khi tạo đơn hàng mới.'))
        partner_obj = self.env['res.partner'].search([('x_code', '=', self.x_code)])
        if len(partner_obj) > 1:
            raise except_orm('Thông báo!', ("Có 2 KH có trung mã. VUi lòng liên hệ Admintrantor"))
        if len(partner_obj) == 0:
            raise except_orm('Thông báo!', ("Không có mã KH. VUi lòng liên hệ Admintrantor"))
        ctx = self.env.context.copy()
        ctx.update({'default_partner_id': partner_obj.id, 'default_x_type': 'deposit', 'default_type': 'deposit',
                    'default_session_id': current_session.id,
                    'default_user_id': self.env.uid})
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

    @api.multi
    def action_create_using(self):
        user_id = self.env['res.users'].search([('id', '=', self.env.uid)], limit=1)
        config_id = user_id.x_pos_config_id.id
        current_session = self.env['pos.session'].search(
            [('state', '=', 'opened'), ('config_id', '=', config_id)], limit=1)
        if not current_session:
            raise except_orm(("Cảnh báo!"), _('Bạn phải mở phiên trước khi tạo đơn hàng mới.'))
        partner_obj = self.env['res.partner'].search([('x_code', '=', self.x_code)])
        if len(partner_obj) > 1:
            raise except_orm('Thông báo!', ("Có 2 KH có trung mã. VUi lòng liên hệ Admintrantor"))
        if len(partner_obj) == 0:
            raise except_orm('Thông báo!', ("Không có mã KH. VUi lòng liên hệ Admintrantor"))
        ctx = self.env.context.copy()
        ctx.update({'default_customer_id': partner_obj.id, 'default_type': 'service',
                    'default_session_id': current_session.id,
                    'default_user_id': self.env.uid})
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

    @api.multi
    def action_print_history_use_service(self):
        return {
                'type': 'ir.actions.act_url',
                'url': 'report/pdf/izi_product_search_card.report_template_history_use_service/%s' %(self.id),
                'target': 'new',
                'res_id': self.id,
            }

    @api.multi
    def action_booking(self):
        return self.__get_view('service')

    @api.multi
    def action_meeting(self):
        return self.__get_view('meeting')

    def __get_view(self, type):
        view_id = self.env.ref('izi_crm_booking.service_booking_form_view').id
        partner_id = None
        if self.x_name:
            partner_id = self.env['res.partner'].sudo().search(['|', ('phone', '=', self.serial), ('mobile', '=', self.serial), ('x_brand_id', '=', self.brand_id.id)])
        ctx = {
            'default_type': type,
            'default_customer_id': partner_id.id,

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