# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import except_orm
from datetime import date, datetime


class RefungInvoiceMakePayment(models.Model):
    _name = 'refund.invoice.make.payment'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char("Name", default='New', track_visibility='onchange')
    partner_id = fields.Many2one('res.partner', "Partner", track_visibility='onchange')
    order_id = fields.Many2one('pos.order', "Order")
    invoice_id = fields.Many2one('account.invoice', "Invoice", track_visibility='onchange')
    payment_id = fields.Many2one('account.payment', "Payment", track_visibility='onchange')
    date = fields.Date(string="Date", default=fields.Datetime.now)
    state = fields.Selection([('draft', "Draft"), ('confirmed', "Confirmed"), ('done', "Done")], default='draft',
                             track_visibility='onchange')
    journal_id = fields.Many2one('account.journal', related='payment_id.journal_id', string='Journal', store=True)
    amount = fields.Monetary(related='payment_id.amount', string="Amount", store=True)
    payment_date = fields.Date(related='payment_id.payment_date', string="Payment Date", store=True)
    currency_id = fields.Many2one('res.currency', related='payment_id.currency_id', string="Currency", store=True)

    @api.multi
    def unlink(self):
        for line in self:
            if line.state != 'draft':
                raise except_orm('Cảnh báo!', ('Không thể xóa bản ghi ở trạng thái khác mới'))
        super(RefungInvoiceMakePayment, self).unlink()

    @api.model
    def create(self, vals):
        if vals.get('name', _('New')) == _('New'):
            vals['name'] = self.env['ir.sequence'].next_by_code('refund.invoice.make.payment') or _('New')
        return super(RefungInvoiceMakePayment, self).create(vals)

    @api.onchange('partner_id')
    def onchange_partner_id(self):
        ids = []
        invoice_ids = self.env['account.invoice'].sudo().search([('partner_id', '=', self.partner_id.id)])
        for line in invoice_ids:
            ids.append(line.id)
        p_ids = []
        payment_ids = self.env['account.payment'].sudo().search(
            [('payment_date', '=', self.date), ('partner_id', '=', self.partner_id.id),
             ('payment_type', '=', 'inbound'), ('partner_type', '=', 'customer'),
             ('state', 'not in', ('draft', 'cancelled')), ('x_customer_sign', '!=', None)])
        for line in payment_ids:
            p_ids.append(line.id)
        return {
            'domain': {
                'invoice_id': [('id', 'in', ids)],
                'payment_id': [('id', 'in', p_ids)]
            }
        }

    @api.onchange('invoice_id')
    def onchange_invoice_id(self):
        order = self.env['pos.order'].search([('name', '=', self.invoice_id.origin)], limit=1)
        self.order_id = order.id
        ids = []
        invoice_ids = self.env['account.invoice'].sudo().search([('partner_id', '=', self.partner_id.id)])
        for line in invoice_ids:
            ids.append(line.id)
        return {
            'domain': {
                'invoice_id': [('id', 'in', ids)],
            }
        }

    @api.onchange('payment_id')
    def onchange_payment_id(self):
        p_ids = []
        payment_ids = self.env['account.payment'].sudo().search(
            [('payment_date', '=', self.date), ('partner_id', '=', self.partner_id.id),
             ('payment_type', '=', 'inbound'), ('partner_type', '=', 'customer'),
             ('state', 'not in', ('draft', 'cancelled')), ('x_customer_sign', '!=', None)])
        for line in payment_ids:
            p_ids.append(line.id)
        return {
            'domain': {
                'payment_id': [('id', 'in', p_ids)]
            }
        }

    @api.multi
    def action_confirm(self):
        if self.state != 'draft':
            raise except_orm("Thông báo!", ("Trạng thái đã thay đổi. Vui lòng F5 hoặc load lại trang"))
        self.state = 'confirmed'
        if self.date != self.payment_id.payment_date:
            raise except_orm("Cảnh báo!", ("Bạn chỉ hủy được những đơn thanh toán công nợ trong ngày"))
        if self.invoice_id.id not in self.payment_id.invoice_ids.ids:
            raise except_orm("Cảnh báo!", "Thanh toán không thuộc hóa đơn này. Vui lòng chọn lại hóa đơn hoặc thanh toán")

    @api.multi
    def action_back(self):
        if self.state != 'confirmed':
            raise except_orm("Thông báo!", ("Trạng thái đã thay đổi. Vui lòng F5 hoặc load lại trang"))
        self.state = 'draft'

    @api.multi
    def action_done(self):
        if self.state != 'confirmed':
            raise except_orm("Thông báo!", ("Trạng thái đã thay đổi. Vui lòng F5 hoặc load lại trang"))
        self.state = 'done'
        account_bank_statement_line = self.env['account.bank.statement.line'].sudo().search(
            [('partner_id', '=', self.partner_id.id), ('amount', '=', self.payment_id.amount),
             ('journal_id', '=', self.payment_id.journal_id.id), ('date', '=', self.payment_id.payment_date),
             ('state', '=', 'open'), ('pos_statement_id', '=', None), ('name', 'like', 'INV')], limit=1)
        if account_bank_statement_line:
            if account_bank_statement_line.statement_id.pos_session_id.state != 'opened':
                raise except_orm("Thông báo!", ("Phiên của thanh toán đã đóng. Bạn không thể hủy"))
            self.payment_id.cancel()
            # config_ids = self.env['pos.config'].search([])
            for x in account_bank_statement_line.statement_id.pos_session_id.config_id:
                # Nếu là hình thức là ghi nhận doanh thu
                #  => Xóa doanh thu ghi nhận và xóa điểm được cộng khi thanh toán công nợ
                # Xóa phân bổ doanh thu
                journal_loyal_ids = x.journal_loyal_ids.ids if x.journal_loyal_ids else False
                if journal_loyal_ids:
                    if self.payment_id.journal_id.id in journal_loyal_ids:
                        # loyal_point = self._get_loyal_total(self.payment_id.amount,
                        #                                     account_bank_statement_line.statement_id.pos_session_id.config_id.id)
                        # point = self.env['izi.vip.point.history'].search(
                        #     [('partner_id', '=', self.payment_id.partner_id.id), ('order_id', '=', self.order_id.id),
                        #      ('date', '=', self.payment_id.payment_date), ('point', '=', loyal_point)], limit=1)
                        # if point:
                        #     self.partner_id.update({'x_point_total': self.partner_id.x_point_total - point.point})
                        #     point.unlink()
                        # else:
                        #     raise except_orm("1", ("1"))
                        revenue = self.env['crm.vip.customer.revenue'].search(
                            [('partner_id', '=', self.payment_id.partner_id.id), ('order_id', '=', self.order_id.id),
                             ('journal_id', '=', self.payment_id.journal_id.id),
                             ('amount', '=', self.payment_id.amount), ('date', '=', self.payment_id.payment_date)],
                            limit=1)
                        if revenue:
                            self.partner_id.update({'x_loyal_total': self.partner_id.x_loyal_total - revenue.amount})
                            revenue.unlink()
                        # else:
                        #     raise except_orm("2", ("2"))
                        # Send message về cho tư vấn co user về khách hàng thanh toán
                        # self = self.sudo()
                        # partner_ids = []
                        # revenue_allocation = self.env['pos.revenue.allocation'].search(
                        #     [('order_id', '=', self.order_id.id)], order="id asc", limit=1)
                        # if revenue_allocation:
                        #     for line in revenue_allocation.line_ids:
                        #         if line.employee_id.user_id:
                        #             if line.employee_id.user_id.partner_id:
                        #                 partner_ids.append(line.employee_id.user_id.partner_id)
                        #
                        # for partner in partner_ids:
                        #     odoobot_id = self.env['ir.model.data'].xmlid_to_res_id("base.partner_root")
                        #     channel = self.env['mail.channel.payment'].search([('partner_id', '=', partner.id)])
                        #     if channel:
                        #         message = _(
                        #             "<br/>Ngày %s khách hàng %s HỦY thanh toán công nợ của đơn hàng %s với số tiền là - %s với hình thức là %s do thanh toán sai</b>" % (
                        #                 self.date, self.order_id.partner_id.name, self.order_id.name,
                        #                 self.convert_numbers_to_text_sangla(self.amount), self.journal_id.name))
                        #         channel.mail_channel_id.sudo().message_post(body=message, author_id=odoobot_id,
                        #                                                     message_type="comment",
                        #                                                     subtype="mail.mt_comment")
                        #     else:
                        #         channel = self.env['mail.channel'].with_context(
                        #             {"mail_create_nosubscribe": True}).create({
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
                        #             "<br/>Ngày %s khách hàng %s đã HỦY thanh toán công nợ cho đơn hàng %s với số tiền là - %s với hình thức là %s do thanh toán nhâm</b>" % (
                        #                 date.today().strftime("%d-%m-%Y"), self.order_id.partner_id.name,
                        #                 self.order_id.name,
                        #                 self.convert_numbers_to_text_sangla(self.amount),
                        #                 self.journal_id.name))
                        #         channel.sudo().message_post(body=message, author_id=odoobot_id,
                        #                                     message_type="comment",
                        #                                     subtype="mail.mt_comment")
                        self.env.cr.execute("""
                                                select id from pos_revenue_allocation
                                                where partner_id = %s and order_id = %s and amount_total = %s and date::date = %s
                                                                """, (
                            self.payment_id.partner_id.id, self.order_id.id, self.amount,
                            self.payment_id.payment_date,))
                        res = self.env.cr.dictfetchall()
                        if res:
                            for r in res:
                                revenue_obj = self.env['pos.revenue.allocation'].search([('id', '=', r['id'])])
                                revenue_line_obj = self.env['pos.revenue.allocation.line'].search(
                                    [('revenue_allocation_id', '=', revenue_obj.id)])
                                for line in revenue_line_obj:
                                    line.unlink()
                                revenue_obj.unlink()
                # Nếu hình thức là tiền đặt cọc thị xóa dong dùng đặt cọc để thanh toán đi để cộng lại tiền cho khách hàng
                journal_deposit_id = x.journal_deposit_id.id if x.journal_deposit_id else False
                if journal_deposit_id:
                    if self.payment_id.journal_id.id == journal_deposit_id:
                        customer_deposit = self.env['pos.customer.deposit.line'].search(
                            [('partner_id', '=', self.payment_id.partner_id.id),
                             ('date', '=', self.payment_id.payment_date),
                             ('journal_id', '=', self.payment_id.journal_id.id),
                             ('amount', '=', self.payment_id.amount), ('x_type', '=', 'deposit'),
                             ('type', '=', 'payment')], limit=1)
                        if customer_deposit:
                            customer_deposit.state = 'draft'
                            customer_deposit.unlink()
                        else:
                            raise except_orm("5", ("5"))
                journal_vm_id = x.journal_vm_id.id if x.journal_vm_id else False
                if journal_vm_id:
                    if self.payment_id.journal_id.id == journal_vm_id:
                        vm_arg_history = []
                        self.env.cr.execute("""
                                        SELECT id
                                        FROM pos_virtual_money_history
                                        WHERE (create_date + INTERVAL '7' HOUR)::date = %s ORDER BY id desc
                                        """, (self.payment_id.payment_date,))
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
                                if amount_vm == self.payment_id.amount:
                                    break
                            for line in vm_arg_history:
                                line.vm_id.money_used -= line.amount
                                line.unlink()
                        else:
                            raise except_orm("3", ("3"))
            account_bank_statement_line.unlink()
            # self.auto_pos_payment_allocation( -self.amount, self.order_id)
            # Hủy đơn phân bổ thanh toán công nợ sai
            # Tạm thời comment lại do chưa đẩy code đoạn phân bổ thanh toán .Ngày 17/04/2019
            # for line in self.payment_id.invoice_ids:
            #     payment_allocation = self.env['pos.payment.allocation'].search(
            #         [('partner_id', '=', self.partner_id.id), ('invoice_id', '=', line.id),
            #          ('order_id', '=', self.order_id.id), ('amount_total', '=', self.amount), ('date', '=', self.date), ('state', '!=', 'cancel')],
            #         limit=1)
            #     if payment_allocation:
            #         if payment_allocation.state == 'done':
            #             payment_allocation.action_back()
            #         payment_allocation.state = 'cancel'
        #     hết Sáng la . Đẩy code module pos_payment_allocation thì bỏ comment đi
        else:
            raise except_orm("4", ("4"))

    # @api.multi
    # def _get_loyal_total(self, loyal_total, config_id):
    #     loy = self.env['izi.vip.config'].search(
    #         [('config_id', '=', config_id), ('to_date', '>=', self.date), ('active', '=', True),
    #          ('from_date', '<=', self.date), ('type', '=', 'accumulation')],
    #         limit=1)
    #     if loy.id == False:
    #         raise except_orm('Cảnh báo!', (
    #             "Bạn chưa cấu hình quy tắc tích điểm cho điểm bán hàng này. Vui lòng kiểm tra lại!"))
    #     loyal_point = loyal_total / 1000000
    #     loy_line = self.env['izi.vip.config.accumulation'].search(
    #         [('rank_id', '=', self.partner_id.x_rank.id), ('vip_config_id', '=', loy.id)], order='revenue asc')
    #     point = 0.0
    #     for loyal in loy_line:
    #         if loyal_total <= loyal.revenue:
    #             point = loyal_point * loyal.factor
    #         if point != 0:
    #             break
    #     loyal_point = round(point, int(loy.round))
    #     return loyal_point

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