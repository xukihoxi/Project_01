# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError, except_orm, MissingError, ValidationError
from datetime import datetime, timedelta, date as my_date
from dateutil.relativedelta import relativedelta

class PosChangePayment(models.Model):
    _inherit = 'pos.order'

    x_status = fields.Selection([('new', "New"), ('change', 'Change'), ('done',"Done")], default='new')
    change_payment_ids = fields.One2many('pos.change.payment','order_id', "Change Payment")

    @api.multi
    def action_pos_order_paid(self):
        if not self.test_paid():
            raise UserError(_("Order is not paid."))
        param_obj = self.env['ir.config_parameter']
        code = param_obj.get_param('default_code_exception')
        if not code:
            raise ValidationError(
                _(u"Bạn chưa cấu hình thông số hệ thống cho mã dịch vụ ngoại lệ. Xin hãy liên hệ với người quản trị."))
        list = code.split(',')
        if len(self.lines) != 0:
            k = 0
            i = 0
            check_therapy = self.check_therapy_record()
            for line in self:
                for tmp in line.lines:
                    if (
                            tmp.product_id.product_tmpl_id.x_type_card == 'tdv' or tmp.product_id.product_tmpl_id.x_type_card == 'tdt'):
                        i = i + 1
                    if (
                            tmp.product_id.product_tmpl_id.type == 'service' and tmp.product_id.product_tmpl_id.default_code not in list):
                        if tmp.product_id not in line.session_id.config_id.product_edit_price_ids:
                            k = k + 1

            if i >= 2:
                raise except_orm('Cảnh báo!', 'Bạn không thể bán 2 thẻ dịch vụ trên cùng 1 đơn hàng')
            if i == 0 and k > 0 and self.x_type == '1' and not check_therapy:
                raise except_orm('Cảnh báo!', 'Bạn phải gắn thẻ dịch vụ cho các dịch vụ vừa chọn!')
            if i == 1 and k == 0:
                raise except_orm('Cảnh báo!', 'Không cho phép bán thẻ dịch vụ không gắn với dịch vụ nào.\n'
                                              ' Vui lòng gắn dịch vụ cho thẻ dịch vụ vừa chon!')

        super(PosChangePayment, self.with_context(xxx=True)).action_pos_order_paid()
        if self.x_status != 'new':
            self.write({'state': 'invoiced'})

    @api.multi
    def action_change_payment(self):
        if self.x_pos_partner_refund_id:
            raise except_orm("Thông báo!", ("Bạn không thể thay đổi hình thức thanh toán cho đơn refund"))
        order_obj = self.env['pos.order'].search([('x_pos_partner_refund_id', '=', self.id)])
        if len(order_obj) >0:
            raise except_orm("Thông báo!", ("Bạn không thể thay đổi hình thức thanh toán cho đơn đã bị refung"))
        self.x_status = 'change'
        stt = 0
        pos_change_obj = self.env['pos.change.payment'].search([('order_id', '=',self.id)], order='id desc', limit=1)
        if pos_change_obj:
            stt = pos_change_obj.stt+1
        else:
            stt =1
        #     copy sang 1 bảng khác để lưu lại lịch sử.
        pos_change = self.env['pos.change.payment']
        for line in self.statement_ids:
            argvs = {
                'journal_id': line.journal_id.id,
                'statement_id': line.statement_id.id,
                'amount': line.amount,
                'amount_currency': line.amount_currency,
                'currency_id': line.x_currency_id.id,
                'order_id': line.pos_statement_id.id,
                'stt': stt,
                'statement_line_id': line.id,
            }
            pos_change.create(argvs)

        for line in self.statement_ids:
            if line.x_payment_id:
                line.x_payment_id.cancel()
            # # Hủy hết thanh toán đi
            # for q in self.invoice_id.move_id.line_ids:
            #     if q.journal_id == line.journal_id and q.account_id.id == self.partner_id.property_account_receivable_id.id and q.move_id.amount == line.amount:
            #         print(1)
            #         print("Lê anh sag")
            #         line.x_payment_id.cancel()
            # cập nhật lại phiếu mua hàng
            count = 0
            if line.x_vc_id:
                line.x_vc_id.x_status = 'using'
                line.x_vc_id.x_user_id = False
            # Nếu là hình thức là ghi nhận doanh thu
            #  => Xóa doanh thu ghi nhận và xóa điểm được cộng khi thanh toán công nợ
            for x in line.statement_id.pos_session_id.config_id:
                journal_loyal_ids = x.journal_loyal_ids.ids if x.journal_loyal_ids else False
                if journal_loyal_ids:
                    if line.journal_id.id in journal_loyal_ids:
                        revenue = self.env['crm.vip.customer.revenue'].search(
                            [('partner_id', '=', line.partner_id.id), ('order_id', '=', line.pos_statement_id.id),
                             ('journal_id', '=', line.journal_id.id),
                             ('amount', '=', line.amount), ('date', '=', line.date)],
                            limit=1)
                        if revenue:
                            self.partner_id.update({'x_loyal_total': self.partner_id.x_loyal_total - revenue.amount})
                            revenue.unlink()
                        # else:
                        #     raise except_orm("2", ("2"))
                # Nếu hình thức là tiền đặt cọc thị xóa dong dùng đặt cọc để thanh toán đi để cộng lại tiền cho khách hàng
                journal_deposit_id = x.journal_deposit_id.id if x.journal_deposit_id else False
                if journal_deposit_id:
                    if line.journal_id.id == journal_deposit_id:
                        customer_deposit = self.env['pos.customer.deposit.line'].search(
                            [('partner_id', '=', line.partner_id.id),
                             ('journal_id', '=', line.journal_id.id),
                             ('amount', '=', line.amount), ('x_type', '=', 'deposit'),
                             ('order_id', '=', self.id),
                             ('type', '=', 'payment')], limit=1)
                        if customer_deposit:
                            customer_deposit.state = 'draft'
                            customer_deposit.unlink()
                        else:
                            raise except_orm("5", ("5"))
                # Nếu là thẻ tiền thì trả tiền cho khách hàng sau đó xóa lịch sủ sử dụng thẻ tiền
                journal_vm_id = x.journal_vm_id.id if x.journal_vm_id else False
                if journal_vm_id:
                    if line.journal_id.id == journal_vm_id:
                        vm_arg_history = []
                        self.env.cr.execute("""
                                                               SELECT id
                                                               FROM pos_virtual_money_history
                                                               WHERE (create_date + INTERVAL '7' HOUR)::date = %s ORDER BY id desc
                                                               """, (line.date,))
                        res = self.env.cr.fetchall()
                        columns = []
                        for data in res:
                            columns.append(data[0])
                        print(res)
                        print(columns)
                        if columns:
                            count = 1
                            amount_vm = 0
                            date = datetime.today().date()
                            for x in columns:
                                print(x)
                                y = self.env['pos.virtual.money.history'].search([('id', '=', str(x))])
                                if count == 1:
                                    amount_vm = 0
                                    date = y.create_date
                                    count += 1
                                if date == y.create_date:
                                    amount_vm += y.amount
                                    vm_arg_history.append(y)
                                else:
                                    count = 1
                                    vm_arg_history = []
                                if amount_vm == self.amount:
                                    break
                            for z in vm_arg_history:
                                z.vm_id.money_used -= line.amount
                                z.unlink()
                        else:
                            raise except_orm("3", ("3"))



    @api.multi
    def action_change_payment_done(self):
        self.x_status = 'done'
        self.state = 'invoiced'
        receivable_move_lines = self.env['account.move.line']
        #ngoant add them xoá phan bo doanh thu
        for line in self.x_allocation_ids:
            line.unlink()
        obj_pos_revenue = self.env['pos.revenue.allocation'].search([('order_id','=',self.id),('line_ids','=',False)])
        if len(obj_pos_revenue) > 0:
            obj_pos_revenue.unlink()
        self.statement_ids.write({'x_ignore_reconcile': True})
        # pos_change1 = self.env['pos.change.payment'].search([('order_id', '=', self.id)], order='id desc', limit=1)
        # pos_change = self.env['pos.change.payment'].search([('stt', '=', pos_change1.stt)])
        # journal_debt_id = self.config_id.journal_debt_id.id if self.config_id.journal_debt_id else False
        # for line in pos_change:
        #     if not line.statement_line_id:
        #         for x in self.invoice_id.move_id.line_ids:
        #             if x.journal_id == line.journal_id and x.account_id.id == self.partner_id.property_account_receivable_id.id and x.move_id.amount == line.amount:
        #                 x.payment_id.cancel()
        #     else:
        #         for x in self.invoice_id.move_id.line_ids:
        #             if x.journal_id == line.journal_id and x.account_id.id == self.partner_id.property_account_receivable_id.id and x.move_id.amount == line.amount:
        #                 x.remove_move_reconcile()
        #                 if x.account_id.id == self.partner_id.property_account_receivable_id.id:
        #                     receivable_move_lines += x
        journal_debt_id = self.config_id.journal_debt_id.id if self.config_id.journal_debt_id else False
        pays_outbound = []
        pays_inbound = []
        payment_obj = self.env['account.payment']
        # for statement in self.statement_ids:
        # Mã các phương thức thanh toán có thể ghi nhận doanh thu
        journal_loyal_ids = self.config_id.journal_loyal_ids.ids if self.config_id.journal_loyal_ids else False
        if journal_loyal_ids:
            loyal_total = 0.0
            # ngoan sửa lại ghi nhận doanh thu trên đơn hàng
            for stt in self.statement_ids:
                if stt.journal_id.id in journal_loyal_ids:
                    if stt.amount > 0:
                        revenue = self.env['crm.vip.customer.revenue'].create({
                            'partner_id': self.partner_id.id,
                            'order_id': self.id,
                            'journal_id': stt.journal_id.id,
                            'amount': stt.amount,
                            'date': my_date.today(),
                        })
                    loyal_total += stt.amount
            # Ghi nhận doanh thu
            if loyal_total >= 0:
                self.x_total_order = loyal_total
                # tiennq them quy doi diem tich luy
                # point = self._get_loyal_total(loyal_total)
                ####
                if loyal_total > 0:
                    self.x_loyal_id = revenue.id
                # self_to_update['x_point_bonus'] = point
                # self_to_update['x_point_total'] = point + self.partner_id.x_point_total
                self.x_loyal_total = loyal_total + self.partner_id.x_loyal_total
                # CuuNV Fix 09/07: Thêm tổng tích điểm cho KH
                self.partner_id.update({'x_loyal_total': self.partner_id.x_loyal_total + loyal_total})
                # SangLA 15/08/2018: Thêm điểm thưởng cho người giới thiệu khách hàng
                order_len = self.env['pos.order'].search([('partner_id', '=', self.partner_id.id)])
                # if len(order_len) == 1 and self.partner_id.x_presenter:
                #     self.partner_id.x_presenter.update(
                #         {'x_point_total': (point + self.partner_id.x_presenter.x_point_total)})
                #     point_history = self.env['izi.vip.point.history'].create({
                #         'partner_id': self.partner_id.x_presenter.id,
                #         'order_id': self.id,
                #         'date': my_date.today(),
                #         'point': point,
                #     })

        # Lấy tổng tiền ảo của KH
        vm_amount = self.env['pos.virtual.money'].get_available_amount_by_partner(self.partner_id.id)
        # Lịch sử sử dụng thẻ tiền
        vm_histories = {}
        # Ghi nhận thanh toán
        for stt in self.statement_ids:
            # Thanh toán bằng thẻ tiền
            if stt.journal_id.code.upper() == 'VM':
                # Nếu không đủ tiền thì báo lỗi
                vm_lines_pay = []
                if vm_amount < stt.amount:
                    raise UserError("Tài khoản thẻ tiền của khách hàng không đủ %s để thanh toán" % stt.amount)
                vm_lines = self.env['pos.virtual.money'].search(
                    [('typex', '=', '1'), ('partner_id', '=', self.partner_id.id), ('state', '=', 'ready')],
                    order='id asc')
                for a in vm_lines:
                    vm_lines_pay.append(a)
                vm_lines_km = self.env['pos.virtual.money'].search(
                    [('typex', '=', '2'), ('partner_id', '=', self.partner_id.id), ('state', '=', 'ready')],
                    order='id asc')
                for x in vm_lines_km:
                    q = 0
                    for y in vm_lines:
                        if x.id == y.sub_amount_id.id:
                            q += 1
                    if q == 0:
                        vm_lines_pay.append(x)

                # Tổng tiền cần thanh toán trên dòng thanh toán
                remain = stt.amount

                def compute_payment(line, remain, amount):
                    # Nếu số tiền cần thanh toán >= số tiền còn lại trên dòng đã thanh toán
                    if remain >= (line.money - line.debt_amount - line.money_used):
                        # Tổng số tiền cần thanh toán giảm = số tiền còn lại trên dòng đã thanh toán
                        remain -= line.money - line.debt_amount - line.money_used
                        # Tổng tiền ảo giảm = số tiền đã trừ
                        amount -= stt.amount - remain
                        # Thêm lịch sử sử dụng tiền ảo = số tiền đã dùng
                        if line.id in vm_histories:
                            vm_histories['%s_%s' % (line.id, stt.id)][
                                'amount'] += line.money - line.debt_amount - line.money_used
                        else:
                            vm_histories['%s_%s' % (line.id, stt.id)] = {'vm_id': line.id, 'order_id': self.id,
                                                                         'amount': line.money - line.debt_amount - line.money_used,
                                                                         'statement_id': stt.id}
                        # Dòng tiền này đã dùng hết số đã thanh toán
                        line.update({'money_used': line.money - line.debt_amount})
                    # Nếu số tiền cần thanh toán < số tiền còn lại trên dòng đã thanh toán
                    else:
                        # Tổng tiền cần thanh toán giảm = số tiền còn lại cần thanh toán
                        amount -= remain
                        # Thêm lịch sử sử dụng = số tiền còn lại cần thanh toán
                        if line.id in vm_histories:
                            vm_histories['%s_%s' % (line.id, stt.id)]['amount'] += remain
                        else:
                            vm_histories['%s_%s' % (line.id, stt.id)] = {'vm_id': line.id, 'order_id': self.id,
                                                                         'amount': remain,
                                                                         'statement_id': stt.id}
                        # Cập nhật tăng số tiền đã dùng = số tiền còn lại cần thanh toán
                        line.update({'money_used': line.money_used + remain})
                        remain = 0
                    return remain, amount

                # Thực hiện trừ cho đến khi đủ số tiền muốn thanh toán
                # Sáng la sửa lại ngùa 23/04/2019. Nếu chỉ có tiền khuyến thì trừ tiền khuyến mại. Nếu có cả 2 thì trừ như tài khoản ban đầu
                if len(vm_lines_pay) > 0:
                    for line in vm_lines_pay:
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
                else:
                    raise except_orm("Cảnh báo!", "Không tìm thấy để trừ thẻ tiền")
            # thanh toán bằng tiền đặt cọc
            elif stt.journal_id.id == self.session_id.config_id.journal_deposit_id.id:
                deposit_lines = self.env['pos.customer.deposit'].search(
                    [('partner_id', '=', self.partner_id.id)])
                total = 0.0
                for line in deposit_lines:
                    total += line.residual
                if total < stt.amount:
                    raise UserError("Tài khoản đặt cọc của khách hàng không đủ %s để thanh toán" % self.amount)
                else:
                    argvs = {
                        'journal_id': stt.journal_id.id,
                        'date': self.date_order,
                        'amount': stt.amount,
                        'order_id': self.id,
                        'deposit_id': deposit_lines[0].id,
                        'type': 'payment',
                        'partner_id': self.partner_id.id
                    }
                    deposit_id = self.env['pos.customer.deposit.line'].create(argvs)
                    deposit_id.update({'state': 'done'})
                # giam x_balancce trong res_partner
                self.partner_id.x_balance = self.partner_id.x_balance - stt.amount
            # Thanh toán bằng phiếu mua hàng
            elif stt.journal_id.code.upper() == 'VC':
                vc = self.env['stock.production.lot'].search(
                    [('name', '=', stt.x_vc_id.name.upper().strip())], limit=1)
                vc._invalidate_vc_code(self.partner_id.id, stt.id)
                vc.update({'x_status': 'used', 'x_user_id': self.partner_id.id})
        # Ghi lịch sử sử dụng thẻ tiền
        if len(vm_histories):
            vm_history_obj = self.env['pos.virtual.money.history']
            for h in vm_histories:
                vm_history_obj.create(vm_histories[h])
        #add them phan bo doanh thu moi
        if self.x_user_id:
            self._auto_allocation()
        # Tiến hàng reconsile đơn hàng
        for statement in self.statement_ids:
            if statement.journal_id.id != journal_debt_id:
                inbound_payment_methods = statement.journal_id.inbound_payment_method_ids
                inbound_payment_method_id = inbound_payment_methods and inbound_payment_methods[0] or False

                outbound_payment_methods = statement.journal_id.outbound_payment_method_ids
                outbound_payment_method_id = outbound_payment_methods and outbound_payment_methods[0] or False
                if statement.amount < 0:
                    pay_outbound = payment_obj.create({
                        'amount': abs(statement.amount),
                        'journal_id': statement.journal_id.id,
                        'payment_date': statement.date,
                        'communication': statement.name,
                        'payment_type': 'outbound',
                        'payment_method_id': outbound_payment_method_id.id,
                        'partner_type': 'customer',
                        'partner_id': statement.partner_id.id,
                        'branch_id': self.user_id.branch_id.id,
                    })
                    pay_outbound.with_context(izi_partner_debt=True).post()
                    pays_outbound.append(pay_outbound)
                    statement.x_payment_id = pay_outbound.id
                else:
                    pay_inbound = payment_obj.create({
                        'amount': statement.amount,
                        'journal_id': statement.journal_id.id,
                        'payment_date': statement.date,
                        'communication': statement.name,
                        'payment_type': 'inbound',
                        'payment_method_id': inbound_payment_method_id.id,
                        'invoice_ids': [(6, 0, self.invoice_id.ids)],
                        'partner_type': 'customer',
                        'partner_id': statement.partner_id.id,
                        'branch_id': self.user_id.branch_id.id,
                    })
                    pay_inbound.with_context(izi_partner_debt=True).action_validate_invoice_payment()
                    pays_inbound.append(pay_inbound)
                    statement.x_payment_id = pay_inbound.id
        if pays_outbound:
            receivable_move_lines = self.env['account.move.line']
            for pay in pays_inbound:
                for move_line in pay.move_line_ids:
                    move_line.remove_move_reconcile()
                    if move_line.account_id.id == self.partner_id.property_account_receivable_id.id:
                        receivable_move_lines += move_line

            for pay in pays_outbound:
                for move_line in pay.move_line_ids:
                    move_line.remove_move_reconcile()
                    if move_line.account_id.id == self.partner_id.property_account_receivable_id.id:
                        receivable_move_lines += move_line
            for move_line in self.invoice_id.move_id.line_ids:
                move_line.remove_move_reconcile()
                if move_line.account_id.id == self.partner_id.property_account_receivable_id.id:
                    receivable_move_lines += move_line

            receivable_move_lines.filtered(lambda l: l.reconciled == False).reconcile()