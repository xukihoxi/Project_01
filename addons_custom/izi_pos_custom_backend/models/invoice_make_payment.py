# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from datetime import date
from odoo.exceptions import UserError, ValidationError, MissingError
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT
from odoo.exceptions import except_orm, Warning as UserError


class InvoiceMakePayment(models.TransientModel):
    _name = 'invoice.make.payment'
    _description = 'Invoice Payment'

    def _default_journal(self):
        session_id = self.env.context.get('default_session_id', False)
        if session_id:
            session = self.env['pos.session'].browse(session_id)
            return session.config_id.journal_ids and session.config_id.journal_ids.ids[0] or False
        return False

    session_id = fields.Many2one('pos.session', required=True)
    journal_id = fields.Many2one('account.journal', string='Payment Mode', required=True, default=_default_journal)
    amount = fields.Float(digits=(16, 2), required=True)
    payment_name = fields.Char(string='Payment Reference')
    payment_date = fields.Date(string='Payment Date', required=True, default=lambda *a: fields.Datetime.now())
    invoice_id = fields.Many2one('account.invoice', string='Invoice', required=True)

    vm_amount = fields.Float('Tài khoản thẻ tiền', readonly=True, store=False)
    show_vm_amount = fields.Boolean('Show vm amount', default=False, store=False)
    is_ready = fields.Boolean("Sẵn sàng", default=False)
    customer_sign = fields.Binary('Chữ ký khách hàng')

    @api.onchange('journal_id')
    def _onchange_journal_id(self):
        invoice = self.env['account.invoice'].browse(self.env.context.get('active_id', False))
        if not invoice:
            raise UserError("Invoice could not be found!")
        if self.journal_id:
            self.show_vm_amount = False
            if self.journal_id.code.upper() == 'VM':
                self.vm_amount = self.env['pos.virtual.money'].get_available_amount_by_partner(invoice.partner_id.id)
                self.show_vm_amount = True
                if self.vm_amount < self.amount:
                    self.amount = self.vm_amount

    # def _get_loyal_total(self, loyal_total):
    #     config_id = self.session_id.config_id.id
    #     today = date.today().strftime(DEFAULT_SERVER_DATE_FORMAT)
    #     loyal_config_id = self.env['izi.vip.config'].search([('config_id', '=', config_id), ('to_date', '>=', today),

    #                                                          ('from_date', '<=', today), ('type', '=', 'accumulation')],
    #                                                         limit=1)
    #     if not loyal_config_id:
    #         raise MissingError("Bạn chưa cấu hình quy tắc tích điểm cho điểm bán hàng này. Vui lòng kiểm tra lại!")
    #     loyal_point = loyal_total / 1000000
    #     loy_line = self.env['izi.vip.config.accumulation'].search(
    #         [('rank_id', '=', self.invoice_id.partner_id.x_rank.id), ('vip_config_id', '=', loyal_config_id.id)], order='revenue asc')
    #     point = 0.0
    #     for loyal in loy_line:
    #         if loyal_total <= loyal.revenue:
    #             point = loyal_point * loyal.factor
    #         if point != 0:
    #             break
    #     loyal_point = round(point, int(loyal_config_id.round))
    #     return loyal_point

    def add_payment(self):
        self.is_ready = True
        return {
            'name': _('Payment'),
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'invoice.make.payment',
            'view_id': self.env.ref('izi_pos_custom_backend.view_invoice_make_payment_form').id,
            'target': 'new',
            'views': False,
            'res_id': self.id,
            'type': 'ir.actions.act_window',
            'context': self.env.context,
        }

    # DO NOT REMOVE THIS
    def add_more_payment(self):
        pass

    def process_payment(self):
        UserObj = self.env['res.users']
        user = UserObj.search([('id', '=', self._uid)], limit=1)
        residual = self.invoice_id.residual
        # Kiểm tra số tiền
        if not self.amount or self.amount <= 0:
            raise UserError("Số tiền thanh toán không hợp lệ, vui lòng kiểm tra lại!")

        # if self.x_currency_id and (self.amount < residual):
        #     raise UserError("Thanh toán ngoại tệ không thể nhỏ hơn số tiền cần thanh toán!")
        # Thanh toán = thẻ tiền
        if self.journal_id.id == self.session_id.config_id.journal_vm_id.id:
            if self.invoice_id.x_pos_order_id and self.invoice_id.x_pos_order_id.x_type not in ('1', '3'):
                raise UserError("Thẻ tiền chỉ dùng thanh toán công nợ cho dịch vụ lẻ!")
            vm_amount = self.env['pos.virtual.money'].get_available_amount_by_partner(self.invoice_id.partner_id.id)
            if not vm_amount or vm_amount < self.amount:
                raise UserError('Số dư thẻ tiền không đủ để thanh toán!')
            vm_lines = self.env['pos.virtual.money'].search(
                [('typex', '=', '1'), ('partner_id', '=', self.invoice_id.partner_id.id), ('state', '=', 'ready')], order='id asc')
            # Tổng tiền cần thanh toán trên dòng thanh toán
            remain = self.amount
            vm_histories = {}

            def compute_payment(line, remain, amount):
                # Nếu số tiền cần thanh toán >= số tiền còn lại trên dòng đã thanh toán
                if remain >= (line.money - line.debt_amount - line.money_used):
                    # Tổng số tiền cần thanh toán giảm = số tiền còn lại trên dòng đã thanh toán
                    remain -= line.money - line.debt_amount - line.money_used
                    # Tổng tiền ảo giảm = số tiền đã trừ
                    amount -= self.amount - remain
                    # Thêm lịch sử sử dụng tiền ảo = số tiền đã dùng
                    if line.id in vm_histories:
                        vm_histories['%s_%s' % (line.id, self.id)]['amount'] += line.money - line.debt_amount - line.money_used
                    else:
                        vm_histories['%s_%s' % (line.id, self.id)] = {'vm_id': line.id,
                                                                     'amount': line.money - line.debt_amount - line.money_used,
                                                                     'order_id': self.invoice_id.x_pos_order_id.id}
                    # Dòng tiền này đã dùng hết số đã thanh toán
                    line.update({'money_used': line.money - line.debt_amount})
                # Nếu số tiền cần thanh toán < số tiền còn lại trên dòng đã thanh toán
                else:
                    # Tổng tiền cần thanh toán giảm = số tiền còn lại cần thanh toán
                    amount -= remain
                    # Thêm lịch sử sử dụng = số tiền còn lại cần thanh toán
                    if line.id in vm_histories:
                        vm_histories['%s_%s' % (line.id, self.id)]['amount'] += remain
                    else:
                        vm_histories['%s_%s' % (line.id, self.id)] = {'vm_id': line.id, 'amount': remain,
                                                                      'order_id': self.invoice_id.x_pos_order_id.id}
                    # Cập nhật tăng số tiền đã dùng = số tiền còn lại cần thanh toán
                    line.update({'money_used': line.money_used + remain})
                    remain = 0
                return remain, amount

            # Thực hiện trừ cho đến khi đủ số tiền muốn thanh toán
            for line in vm_lines:
                line_in_use = line
                # Bỏ qua các dòng thẻ tiền đã dùng hết số đã thanh toán
                if line.money - line.debt_amount == line.money_used:
                    if line.sub_amount_id and line.sub_amount_id.money - line.sub_amount_id.debt_amount > line.sub_amount_id.money_used:
                        line_in_use = line.sub_amount_id
                    else:
                        continue
                remain, vm_amount = compute_payment(line_in_use, remain, vm_amount)
                if remain and line_in_use.id == line.id and line.sub_amount_id \
                        and line.sub_amount_id.money - line.sub_amount_id.debt_amount > line.sub_amount_id.money_used:
                    line_in_use = line.sub_amount_id
                    remain, vm_amount = compute_payment(line_in_use, remain, vm_amount)
            # Ghi lịch sử sử dụng thẻ tiền
            if len(vm_histories):
                vm_history_obj = self.env['pos.virtual.money.history']
                for h in vm_histories:
                    if vm_histories[h]['amount'] != 0:
                        vm_history_obj.create(vm_histories[h])
        # Thanh toán = các phương thức khác
        self.add_more_payment()

        # Tìm mã account.bank.statement để đẩy account.bank.statement.line vào phiên
        statement_id = False
        for statement in self.session_id.statement_ids:
            if statement.journal_id.id == self.journal_id.id:
                statement_id = statement.id
                break
        if not statement_id:
            raise MissingError(_(
                'Xuất hiện một hình thức thanh toán mới không được sử dụng trong phiên làm việc của bạn, vui lòng kiểm tra lại !'))
        # Tạo account.bank.statement.line
        statement = self.env['account.bank.statement.line'].create({
            'amount': self.amount,
            'statement_id': statement_id,
            'date': date.today(),
            'name': self.invoice_id.number,
            'account_id': self.invoice_id.account_id.id,
            'partner_id': self.invoice_id.partner_id.id,
            'journal_id': self.journal_id.id,
            'x_ignore_reconcile': True,
            'ref': _('PAID_') + _(
                self.invoice_id.origin and self.invoice_id.origin or self.invoice_id.name or self.invoice_id.number),
        })
        # SangsLA thêm ngày 3/10/2018 Thêm order vào form khi chung của khách hàng

        pos_sum_digital_obj = self.env['pos.sum.digital.sign'].search(
            [('partner_id', '=', self.invoice_id.partner_id.id), ('state', '=', 'draft'), ('session_id', '=', self.session_id.id)])
        if pos_sum_digital_obj:
            statement.update({'x_digital_sign_id': pos_sum_digital_obj.id})
        else:
            pos_sum_digital_obj = self.env['pos.sum.digital.sign'].create({
                'partner_id': self.invoice_id.partner_id.id,
                'state': 'draft',
                'date': date.today(),
                'session_id': self.session_id.id,
            })
            statement.update({'x_digital_sign_id': pos_sum_digital_obj.id})
        # het
        # Sangla them nếu thanh toán quá số tiền trong công nợ => Tự động bỏ ra đặt cọc
        if self.amount - self.invoice_id.residual > 0:
            deposit_lines = self.env['pos.customer.deposit'].search(
                [('partner_id', '=', self.invoice_id.partner_id.id)])
            if not deposit_lines:
                Master = self.env['pos.customer.deposit']
                vals = {
                    'name': self.invoice_id.partner_id.name,
                    'partner_id': self.invoice_id.partner_id.id,
                    'journal_id': self.session_id.config_id.journal_deposit_id.id,
                }
                deposit_lines = Master.create(vals)
            argvs = {
                'journal_id': self.session_id.config_id.journal_deposit_id.id,
                'date': date.today(),
                'amount': self.amount - self.invoice_id.residual,
                # 'order_id': self.id,
                'deposit_id': deposit_lines[0].id,
                'type': 'deposit',
                'partner_id': self.invoice_id.partner_id.id,
                'session_id': self.session_id.id
            }
            deposit_id = self.env['pos.customer.deposit.line'].create(argvs)
            deposit_id.update({'state': 'done'})
            # hết

        payment_methods = statement.journal_id.inbound_payment_method_ids
        payment_method_id = payment_methods and payment_methods[0] or False

        if self.amount - self.invoice_id.residual >0 :
            pay = self.env['account.payment'].create({
                'amount': self.invoice_id.residual,
                'journal_id': statement.journal_id.id,
                'payment_date': statement.date,
                'comunication': statement.name,
                'payment_type': 'inbound',
                'payment_method_id': payment_method_id.id,
                'invoice_ids': [(6, 0, self.invoice_id.ids)],
                'partner_type': 'customer',
                'partner_id': statement.partner_id.id,
                'x_customer_sign': self.customer_sign,
                'branch_id': user.branch_id.id,
                'x_payment_debit': True,
            })
            pay.with_context(izi_partner_debt=True).action_validate_invoice_payment()
            statement.x_payment_id = pay.id
        else:
            pay = self.env['account.payment'].create({
                'amount': statement.amount,
                'journal_id': statement.journal_id.id,
                'payment_date': statement.date,
                'comunication': statement.name,
                'payment_type': 'inbound',
                'payment_method_id': payment_method_id.id,
                'invoice_ids': [(6, 0, self.invoice_id.ids)],
                'partner_type': 'customer',
                'partner_id': statement.partner_id.id,
                'x_customer_sign': self.customer_sign,
                'branch_id': user.branch_id.id,
                'x_payment_debit': True,
            })
            pay.with_context(izi_partner_debt=True).action_validate_invoice_payment()
            statement.x_payment_id = pay.id
        # Lấy đơn hàng đã phát sinh hoá đơn
        order_id = self.env['pos.order'].search([('name', '=', self.invoice_id.reference)])
        if order_id and len(order_id) == 1:
            # Nếu Ghi nợ không ghi nhận doanh thu thì khi trả nợ phải ghi nhận
            if order_id.session_id.config_id.journal_debt_id.id not in order_id.session_id.config_id.journal_loyal_ids.ids\
                    and self.journal_id.id != self.session_id.config_id.journal_vm_id.id and self.journal_id.id != self.session_id.config_id.journal_deposit_id.id:
                if self.amount > 0:
                    # Ghi lich su doanh thu
                    self.env['crm.vip.customer.revenue'].create({
                        'partner_id': self.invoice_id.partner_id.id,
                        'order_id': order_id.id,
                        'journal_id':self.journal_id.id,
                        'amount': self.amount,
                        'date': date.today(),
                    })
                # Cộng doanh thu cho KH
                self.invoice_id.partner_id.update({
                    'x_loyal_total': self.invoice_id.partner_id.x_loyal_total + self.amount,
                    # 'x_point_total': self.invoice_id.partner_id.x_point_total + self._get_loyal_total(self.amount),
                })
                # loyal_total = self._get_loyal_total(self.amount)
                # if loyal_total != 0:
                #     self.env['izi.vip.point.history'].create({
                #         'partner_id': self.invoice_id.partner_id.id,
                #         'order_id': order_id.id,
                #         'date': date.today(),
                #         'point': loyal_total,
                #     })
                # Sangla Công thêm điểm cho Kh giới thiệu khách hàng
                order = self.env['pos.order'].search([('partner_id', '=', order_id.partner_id.id)],order="id asc",limit=1)
                # order_len = self.env['pos.order'].search([('partner_id', '=', order_id.partner_id.x_presenter.id)])
                # if len(order_len) == 0:
                # if (order.id == order_id.id) and order_id.partner_id.x_presenter:
                #     order_id.partner_id.x_presenter.update(
                #         {'x_point_total': (self._get_loyal_total(self.amount) + order_id.partner_id.x_presenter.x_point_total)})
                #     loyal_total = self._get_loyal_total(self.amount)
                #     if loyal_total != 0:
                #         self.env['izi.vip.point.history'].create({
                #             'partner_id': order_id.partner_id.x_presenter.id,
                #             'order_id': order_id.id,
                #             'date': date.today(),
                #             'point': loyal_total,
                #         })

                # Tiennq cong han muc ghi no cho Kh hoac nguoi so huu
                if not order_id.x_owner_id:
                    order_id.partner_id.x_balance += self.amount
                else:
                    order_id.x_owner_id.x_balance += self.amount
                # Tiendz them phan bo doanh thu ngay 09/08
                self._allocation_revenua(self.amount, order_id, self.session_id)
            # Cập nhật lại số tiền nợ của đơn hàng
            for line in order_id.lines:
                # Cập nhật nợ mua thẻ tiền
                if line.product_id.default_code and line.product_id.default_code.upper() == 'COIN' and line.discount != 100:
                    vm_id = self.env['pos.virtual.money'].search(
                        [('partner_id', '=', self.invoice_id.partner_id.id),
                         ('order_id', '=', order_id.id),
                         ('typex', '=', '1')])
                    if self.amount - self.invoice_id.residual >0:
                        vm_id.update({'debt_amount': vm_id.debt_amount - vm_id.debt_amount})
                    else:
                        vm_id.update({'debt_amount': vm_id.debt_amount - self.amount})
                    if vm_id.sub_amount_id and vm_id.debt_amount == 0.0:
                        vm_id.sub_amount_id.update({'debt_amount': 0.0})

        # Send message về cho tư vấn co user về khách hàng thanh toán
        # self = self.sudo()
        # partner_ids = []
        # revenue_allocation = self.env['pos.revenue.allocation'].search([('order_id', '=', order_id.id)], order="id asc",
        #                                                                limit=1)
        # if revenue_allocation:
        #     for line in revenue_allocation.line_ids:
        #         if line.employee_id.user_id:
        #             if line.employee_id.user_id.partner_id:
        #                 partner_ids.append(line.employee_id.user_id.partner_id)
        # for partner in partner_ids:
        #     odoobot_id = self.env['ir.model.data'].xmlid_to_res_id("base.partner_root")
        #     channel = self.env['mail.channel.payment'].search([('partner_id', '=', partner.id)])
        #     if channel:
        #         message = _(
        #             "<br/>Ngày %s khách hàng %s thanh toán công nợ cho đơn hàng %s với số tiền là %s với hình thức là %s</b>" % (
        #             date.today().strftime("%d-%m-%Y"), order_id.partner_id.name, order_id.name,
        #             self.convert_numbers_to_text_sangla(self.amount), self.journal_id.name))
        #         channel.mail_channel_id.message_post(body=message, author_id=odoobot_id, message_type="comment",
        #                                                     subtype="mail.mt_comment")
        #     else:
        #         channel = self.env['mail.channel'].with_context({"mail_create_nosubscribe": True}).create({
        #             'channel_partner_ids': [(4, partner.id), (4, odoobot_id)],
        #             'public': 'private',
        #             'channel_type': 'chat',
        #             'email_send': False,
        #             'name': 'OdooBot'
        #         })
        #         self.env['mail.channel.payment'].create({'mail_channel_id': channel.id,
        #                                                  'partner_id': partner.id
        #                                                  })
        #         message = _(
        #             "<br/>Ngày %s khách hàng %s thanh toán công nợ cho đơn hàng %s với số tiền là %s với hình thức là %s</b>" % (
        #                 date.today().strftime("%d-%m-%Y"), order_id.partner_id.name, order_id.name,
        #                 self.convert_numbers_to_text_sangla(self.amount),
        #                 self.journal_id.name))
        #         channel.message_post(body=message, author_id=odoobot_id, message_type="comment",
        #                                     subtype="mail.mt_comment")
        # self.env.user.odoobot_state = 'onboarding_emoji'
        return statement

    def launch_payment(self):
        return {
            'name': _('Payment'),
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'invoice.make.payment',
            'view_id': self.env.ref('izi_pos_custom_backend.view_invoice_make_payment_form').id,
            'target': 'new',
            'views': False,
            'type': 'ir.actions.act_window',
            'context': self.env.context,
        }

    # Phân bổ doanh thu
    def _allocation_revenua(self, amount_total, order_id, session_id):
        Allocation = self.env['pos.revenue.allocation']
        AllocationLine = self.env['pos.revenue.allocation.line']
        revenua_old = Allocation.search([('order_id','=',order_id.id)], order="date asc")
        revenua_old_copy = Allocation.search([('order_id', '=', order_id.id)], order="date asc", limit=1)
        # Lấy danh sách các sản phẩm được phân bổ trong các đơn cũ
        list_product = []
        # Danh sách các sản phẩm được lấy đã phân bổ
        list_product_old = []
        # Danh sách các sản phẩm có trong order nhưng chưa được phân bổ
        list_product_new = []
        for revenua in revenua_old:
            for line in revenua.line_ids:
                if line.product_id.id not in list_product:
                    list_product.append(line.product_id.id)
        for line in order_id.lines:
            if line.product_id.id in list_product:
                perence = 0
                amount = 0
                for revenua in revenua_old:
                    for line_reven in revenua.line_ids:
                        if line.product_id == line_reven.product_id:
                            perence += line_reven.percent
                            amount += line_reven.amount/line_reven.percent
                            percent = line_reven.percent
                vals_product = {
                    'product_id': line.product_id.id,
                    'amount': amount,
                    'perent': percent,
                }
                list_product_old.append(vals_product)
            else:
                list_product_new.append(line.product_id.id)
        vals = {
            'order_id': order_id.id,
            'partner_name': order_id.partner_id.name,
            'partner_id': order_id.partner_id.id,
            'partner_code': order_id.partner_id.x_code,
            'amount_total': amount_total,
            'amount_allocated': amount_total,
            'amount_res': 0,
            'state': 'close',
            'pos_session_id': session_id.id,
        }
        # Tạo đơn phân bổ doanh thu master mới
        revenue_id = Allocation.create(vals)
        # Phâm bổ cho sản phẩm trước rồi mới phân bổ cho dịch vụ
        for line in order_id.lines:
            # Nếu là sản phẩm
            if line.product_id.type == 'product':
                for line_product in list_product_old:
                    amount_line = 0
                    if line_product['product_id'] == line.product_id.id and line.price_subtotal_incl - line_product['amount'] > 0:
                        if amount_total > line.price_subtotal_incl - line_product['amount'] :
                            amount_line = line.price_subtotal_incl - line_product['amount']
                        elif amount_total <= line.price_subtotal_incl - line_product['amount']:
                            amount_line = amount_total
                        elif amount_total == 0:
                            amount_line = 0
                        #     Lấy ra các nhân viên và được hưởng bao nhiêu tiền
                        # Tính xem mỗi nhân viên được bao nhiêu tiền đối với dịch vụ nào
                        list_employee = []
                        list_tmp = []
                        for line_reven in revenua_old:
                            obj_revenue_line_employee = AllocationLine.search([('product_id','=',line.product_id.id),('revenue_allocation_id','=',line_reven.id)])
                            for line_employee in obj_revenue_line_employee:
                                if line_employee.employee_id.id not in list_tmp:
                                    vals_employee = {
                                        'employee': line_employee.employee_id.id,
                                        'amount': line_employee.amount
                                    }
                                    list_employee.append(vals_employee)
                                    list_tmp.append(line_employee.employee_id.id)
                                else:
                                    for line_list_employee in list_employee:
                                        if line_list_employee['employee'] == line_employee.employee_id.id:
                                            line_list_employee['amount'] = line_list_employee['amount'] + line_employee.amount
                        #
                        obj_revennue_line = AllocationLine.search([('product_id','=',line.product_id.id),('revenue_allocation_id','=',revenua_old_copy.id)])
                        for line2 in obj_revennue_line:
                            for line_employee in list_employee:
                                if line_employee['employee'] == line2.employee_id.id:
                                    amount_tmp = line_employee['amount']
                                    break
                            if amount_tmp != 0 and line_product['amount'] != 0:
                                ratio = amount_tmp/line_product['amount']
                            elif amount_tmp == 0 or line_product['amount'] == 0:
                                ratio = 0
                            vals_line = {
                                'employee_id': line2.employee_id.id,
                                'amount': amount_line * line2.percent * ratio,
                                'amount_total': amount_line * line2.percent * ratio,
                                'percent': line2.percent,
                                'order_id': line2.order_id.id,
                                'product_id': line.product_id.id,
                                'note': line2.note,
                                'revenue_allocation_id': revenue_id.id,
                                'quantity': line2.quantity
                            }
                            AllocationLine.create(vals_line)
                            amount_total -= (amount_line * line2.percent * ratio)
            # Nếu là dịch vụ
            else:
                for line_product in list_product_old:
                    amount_line = 0
                    if line_product['product_id'] == line.product_id.id and line.price_subtotal_incl - line_product['amount'] > 0:
                        if amount_total > line.price_subtotal_incl - line_product['amount']:
                            amount_line = line.price_subtotal_incl - line_product['amount']
                        elif amount_total <= line.price_subtotal_incl - line_product['amount']:
                            amount_line = amount_total
                        elif amount_total == 0:
                            amount_line = 0
                        list_tmp = []
                        list_employee = []
                        for line_reven in revenua_old:
                            obj_revenue_line_employee = AllocationLine.search([('product_id','=',line.product_id.id),('revenue_allocation_id','=',line_reven.id)])
                            for line_employee in obj_revenue_line_employee:
                                if line_employee.employee_id.id not in list_tmp:
                                    vals_employee = {
                                        'employee':line_employee.employee_id.id,
                                        'amount':line_employee.amount
                                    }
                                    list_employee.append(vals_employee)
                                    list_tmp.append(line_employee.employee_id.id)
                                else:
                                    for line_list_employee in list_employee:
                                        if line_list_employee['employee'] == line_employee.employee_id.id:
                                            line_list_employee['amount'] = line_list_employee['amount'] + line_employee.amount
                        # tìm trong bản ghi đầu tiên
                        obj_revennue_line = AllocationLine.search([('product_id','=',line.product_id.id),('revenue_allocation_id','=',revenua_old_copy.id)])
                        for line2 in obj_revennue_line:
                            for line_employee in list_employee:
                                if line_employee['employee'] == line2.employee_id.id:
                                    amount_tmp = line_employee['amount']
                                    break
                            if amount_tmp != 0 and line_product['amount'] != 0:
                                ratio = amount_tmp / line_product['amount']
                            elif amount_tmp == 0 or line_product['amount'] == 0:
                                ratio = 0
                            vals_line = {
                                'employee_id': line2.employee_id.id,
                                'amount': amount_line * line2.percent * ratio,
                                'amount_total': amount_line * line2.percent * ratio,
                                'percent': line2.percent,
                                'order_id': line2.order_id.id,
                                'product_id': line.product_id.id,
                                'note': line2.note,
                                'revenue_allocation_id': revenue_id.id,
                                'quantity': line2.quantity
                            }
                            AllocationLine.create(vals_line)
                            amount_total -= (amount_line * line2.percent * ratio)
        self.auto_aloocation_product_new(amount_total,order_id,list_product_new,revenue_id,AllocationLine)
        revenue_id.amount_allocated = revenue_id.amount_total - amount_total
        revenue_id.amount_res = amount_total
        if revenue_id.amount_res != 0:
            revenue_id.state = 'draft'
        return True

    def auto_aloocation_product_new(self,amount_total,order_id, list_product_new,revenue_id,AllocationLine):
        if amount_total != 0:
            count_nvtv = 0
            for item in order_id.x_user_id:
                if item.job_id.x_code == 'NVTV':
                    count_nvtv += 1
            count = len(order_id.x_user_id)
            if (count == count_nvtv or count_nvtv == 0) and count > 0:
                if count_nvtv == 0:
                    note = 'Nhân viên thừa hưởng'
                else:
                    note = 'Nhân viên tư vấn'

                for line in order_id.lines:
                    if line.product_id.type == 'product' and line.product_id.id in list_product_new:
                        if line.price_subtotal_incl > 0 and amount_total >= 0:
                            if amount_total >= line.price_subtotal_incl:
                               amount_product = line.price_subtotal_incl / count
                            elif amount_total < line.price_subtotal_incl:
                                amount_product = amount_total / count
                            elif amount_total == 0:
                                amount_product = 0
                            for item in order_id.x_user_id:
                                vals_line = {
                                    'employee_id': item.id,
                                    'amount': amount_product,
                                    'amount_total': amount_product,
                                    'percent': 1,
                                    'order_id': order_id.id,
                                    'product_id':line.product_id.id,
                                    'note': note,
                                    'revenue_allocation_id': revenue_id.id,
                                    'quantity': line.qty
                                }
                                AllocationLine.create(vals_line)
                                amount_total -= amount_product

                for line in order_id.lines:
                    if line.product_id.type == 'service' and line.product_id.id in list_product_new:
                        if line.price_subtotal_incl > 0 and amount_total >= 0:
                            if amount_total >= line.price_subtotal_incl:
                               amount_product = line.price_subtotal_incl / count
                            elif amount_total < line.price_subtotal_incl:
                                amount_product = amount_total / count
                            elif amount_total == 0:
                                amount_product = 0
                            for item in order_id.x_user_id:
                                vals_line = {
                                    'employee_id': item.id,
                                    'amount': amount_product,
                                    'amount_total': amount_product,
                                    'percent': 1,
                                    'order_id': order_id.id,
                                    'product_id':line.product_id.id,
                                    'note': note,
                                    'revenue_allocation_id': revenue_id.id,
                                    'quantity': line.qty
                                }
                                AllocationLine.create(vals_line)
                                amount_total -= amount_product

            elif count > 0:
                for line in order_id.lines:
                    if line.product_id.type == 'product' and line.product_id.id in list_product_new:
                        amount_product_debit = 0
                        for item in order_id.x_user_id:
                            if item.job_id.x_code == 'NVTV':
                                if line.price_subtotal_incl > 0 and amount_total >= 0 :
                                    if amount_total >= line.price_subtotal_incl:
                                        amount_product = line.price_subtotal_incl / (2 * count_nvtv)
                                    elif amount_total < line.price_subtotal_incl:
                                        amount_product = amount_total / (2 * count_nvtv)
                                    elif amount_total == 0:
                                        amount_product = 0
                                    vals_line = {
                                        'employee_id': item.id,
                                        'amount': amount_product,
                                        'amount_total': amount_product,
                                        'product_id': line.product_id.id,
                                        'percent': 1,
                                        'order_id': order_id.id,
                                        'note': 'Nhân viên tư vấn',
                                        'revenue_allocation_id': revenue_id.id,
                                        'quantity': line.qty
                                    }
                                    AllocationLine.create(vals_line)
                                    amount_product_debit += amount_product
                            else:
                                if line.price_subtotal_incl > 0 and amount_total >= 0:
                                    if amount_total >= line.price_subtotal_incl:
                                        amount_product = line.price_subtotal_incl / (2 * (count - count_nvtv))
                                    elif amount_total < line.price_subtotal_incl:
                                        amount_product = amount_total / (2 * (count - count_nvtv))
                                    elif amount_total == 0:
                                        amount_product = 0
                                    vals_line = {
                                        'employee_id': item.id,
                                        'amount': amount_product,
                                        'amount_total': amount_product,
                                        'product_id': line.product_id.id,
                                        'percent': 1,
                                        'order_id': order_id.id,
                                        'note': 'Nhân viên thừa hưởng',
                                        'revenue_allocation_id': revenue_id.id,
                                        'quantity': line.qty
                                    }
                                    AllocationLine.create(vals_line)
                                    amount_product_debit += amount_product
                        amount_total -= amount_product_debit

                for line in order_id.lines:
                    if line.product_id.type == 'service' and line.product_id.id in list_product_new:
                        amount_product_debit = 0
                        for item in order_id.x_user_id:
                            if item.job_id.x_code == 'NVTV':
                                if line.price_subtotal_incl > 0 and amount_total >= 0:
                                    if amount_total >= line.price_subtotal_incl:
                                        amount_product = line.price_subtotal_incl / (2 * count_nvtv)
                                    elif amount_total < line.price_subtotal_incl:
                                        amount_product = amount_total / (2 * count_nvtv)
                                    elif amount_total == 0:
                                        amount_product = 0
                                    vals_line = {
                                        'employee_id': item.id,
                                        'amount': amount_product,
                                        'amount_total': amount_product,
                                        'product_id': line.product_id.id,
                                        'percent': 1,
                                        'order_id': order_id.id,
                                        'note': 'Nhân viên tư vấn',
                                        'revenue_allocation_id': revenue_id.id,
                                        'quantity': line.qty
                                    }
                                    AllocationLine.create(vals_line)
                                    amount_product_debit += amount_product
                            else:
                                if line.price_subtotal_incl > 0 and amount_total >= 0:
                                    if amount_total >= line.price_subtotal_incl:
                                        amount_product = line.price_subtotal_incl / (2 * (count - count_nvtv))
                                    elif amount_total < line.price_subtotal_incl:
                                        amount_product = amount_total / (2 * (count - count_nvtv))
                                    elif amount_total == 0:
                                        amount_product = 0
                                    vals_line = {
                                        'employee_id': item.id,
                                        'amount': amount_product,
                                        'amount_total': amount_product,
                                        'product_id': line.product_id.id,
                                        'percent': 1,
                                        'order_id': order_id.id,
                                        'note': 'Nhân viên thừa hưởng',
                                        'revenue_allocation_id': revenue_id.id,
                                        'quantity': line.qty
                                    }
                                    AllocationLine.create(vals_line)
                                    amount_product_debit += amount_product
                        amount_total -= amount_product_debit

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

class MailChanelPayment(models.Model):
    _name = 'mail.channel.payment'

    partner_id = fields.Many2one('res.partner', "Partner")
    mail_channel_id = fields.Many2one('mail.channel', "Mail Channel")