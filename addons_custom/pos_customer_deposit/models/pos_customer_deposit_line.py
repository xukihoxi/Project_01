# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import except_orm, ValidationError, UserError
from datetime import datetime, timedelta, date as my_date


class PosCustomerDepositLine(models.Model):
    _name = 'pos.customer.deposit.line'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    deposit_id = fields.Many2one('pos.customer.deposit', string='Deposit')
    partner_id = fields.Many2one('res.partner', string='Partner')

    @api.model
    def default_get(self, fields):
        res = super(PosCustomerDepositLine, self).default_get(fields)
        if not self._context.get('inventory_update', False):
            user_id = self.env['res.users'].search([('id', '=', self.env.uid)], limit=1)
            config_id = user_id.x_pos_config_id.id
            current_session = self.env['pos.session'].search([('state', '=', 'opened'), ('config_id', '=', config_id)],
                                                             limit=1)
            if not current_session:
                raise except_orm(("Cảnh báo!"), ('Bạn phải mở phiên trước khi tạo đơn hàng mới.'))
        return res

    def _default_session(self):
        user_id = self.env['res.users'].search([('id', '=', self.env.uid)], limit=1)
        config_id = user_id.x_pos_config_id.id
        return self.env['pos.session'].search([('state', '=', 'opened'), ('config_id', '=', config_id)], limit=1)

    def _default_employee(self):
        return self.env.uid

    session_id = fields.Many2one(
        'pos.session', string='Session', required=True, index=True,
        readonly=True, default=_default_session)

    name = fields.Char("Name", default="New", copy=False, track_visibility='onchange')
    partner_id = fields.Many2one('res.partner', string='Customer', track_visibility='onchange', required=1)
    x_type = fields.Selection([('deposit', 'Deposit'), ('cash', 'Cash')], 'Type', default='deposit')
    type = fields.Selection([('deposit', 'Deposit'), ('payment', 'Payment'), ('cash', 'Cash')], 'Type', default='deposit')
    journal_id = fields.Many2one('account.journal', string='Journal')
    date = fields.Datetime(string='Date', default=fields.Datetime.now, track_visibility='onchange')
    amount = fields.Float('Amount', required=1, track_visibility='onchange')
    charge_refund = fields.Float(string="Charge refund")
    note = fields.Text('Note')
    user_id = fields.Many2one('res.users', 'User', default=_default_employee, track_visibility='onchange')
    order_id = fields.Many2one('pos.order', 'Order')
    x_signature_image = fields.Binary('Signature Image', attachment=True)
    state = fields.Selection([('draft', 'Draft'), ('to_confirm', 'To Confirm'), ('confirm', 'Confirm'), ('done', 'Done'), ('cancel', 'Cancel')],
                             'State',
                             default='draft', track_visibility='onchange')

    # Sangla them dặt cọc đa tiền tệ
    x_currency_id = fields.Many2one('res.currency', "Currency", track_visibility='onchange')
    x_currency_rate_id = fields.Many2one('res.currency.rate', "Currency Rate")
    x_money_multi = fields.Float("Money Multi", track_visibility='onchange')
    x_show_currency_amount = fields.Boolean('Show Currency Amount')
    rate_vn = fields.Float("Rate VN", track_visibility='onchange')

    # Tiennq them phan bổ doanh thu cho nhân viên tư vấn và công doanh thu khách hàng
    revenue_id = fields.Many2one('pos.revenue.allocation', string='Allocation revenue', track_visibility='onchange')
    x_user_id = fields.Many2many('hr.employee', string='Beneficiary', track_visibility='onchange')

    @api.onchange('x_type')
    def _onchange_x_type(self):
        self.charge_refund = 0

    @api.onchange('charge_refund')
    def _onchange_charge_refund(self):
        message = ''
        if self.charge_refund < 0:
            message = 'Phí hoàn tiền phải không thể âm!'
        if self.charge_refund > self.amount:
            message = 'Phí hoàn đặt tiền không thể lớn hơn số tiền hoàn lại.'
        if message != '':
            return {
                'warning': {
                    'title': 'Thông báo',
                    'message': message
                },
                'value': {
                    'charge_refund': 0
                }
            }

    @api.onchange('user_id')
    def _onchange_default_emp(self):
        #mặc định lấy nhân viên hưởng doanh thu là người người hưởng doanh thu dự kiến
        context = self._context
        if self.user_id:
            lead_employee_ids = context.get('lead_employee_ids', False)
            if lead_employee_ids:
                self.x_user_id = lead_employee_ids
            else:
                self.x_user_id = False

    @api.onchange('journal_id')
    def _onchange_journal_id(self):
        self.x_show_currency_amount = False
        if self.journal_id.id in self.session_id.config_id.x_journal_currency_ids.ids:
            self.x_show_currency_amount = True
            if self.journal_id.x_pos_multi_currency_id:
                self.x_currency_id = self.journal_id.x_pos_multi_currency_id.id
                self.x_money_multi = 0
                self.x_currency_rate_id = False
            else:
                raise except_orm('Cảnh báo',
                                 ("Chưa cấu hình đa tiền tệ trên pos cho sổ này. Vui lòng liên hệ quản trị hệ thống"))
        else:
            self.x_currency_id = False
            self.x_money_multi = 0
            self.x_currency_rate_id = False

    @api.onchange('x_money_multi', 'rate_vn')
    def _onchange_currency_rate(self):
        total = 0
        if self.x_money_multi != 0:
            total = self.rate_vn * self.x_money_multi
            self.amount = total

    @api.model
    def create(self, vals):
        if vals.get('name', _('New')) == _('New'):
            vals['name'] = self.env['ir.sequence'].next_by_code('pos.customer.deposit.line') or _('New')
        return super(PosCustomerDepositLine, self).create(vals)

    @api.onchange('partner_id')
    def _onchange_journal(self):
        list = []
        if self.partner_id:
            user_id = self.env['res.users'].search([('id', '=', self.env.uid)], limit=1)
            config_id = user_id.x_pos_config_id
            for i in config_id.journal_deposit_ids:
                list.append(i.id)
        return {
            'domain': {'journal_id': [('id', 'in', list)]}
        }

    @api.multi
    def action_send(self):
        if self.x_show_currency_amount == True:
            if not (
                    self.rate_vn * self.x_money_multi - 10000 <= self.amount <= self.rate_vn * self.x_money_multi + 10000):
                raise except_orm('Cảnh báo!', ("Số tiền điều chỉnh không thể lớn hơn 10.000 VNĐ"))
        if self.x_type == 'deposit':
            self.type = 'deposit'
        else:
            self.type = 'cash'
        if self.state != 'draft':
            return True
        DepositObj = self.env['pos.customer.deposit']
        deposit_id = DepositObj.search([('partner_id', '=', self.partner_id.id)], limit=1)
        if self.type == 'cash':
            if not deposit_id:
                raise except_orm('Cảnh báo!', (
                    "Không có đơn quản lý của khách hàng này. Không thể hoàn tiền!"))
            else:
                if self.amount > deposit_id.residual:
                    raise except_orm('Cảnh báo!', (
                            'Số tiền hoàn lại không được lớn hơn "%s".' % deposit_id.residual))
                self.deposit_id = deposit_id.id
        if self.type == 'payment':
            raise except_orm('Cảnh báo!', (
                "Bạn chỉ có thể chọn loại là đặt cọc hoặc hoàn tiền"))
        if self.amount <= 0:
            raise except_orm('Cảnh báo!', (
                "Số tiền không được nhỏ hơn hoặc bằng 0"))
        if self.x_type == 'deposit':
            self.state = 'confirm'
        else:
            self.state = 'to_confirm'

    @api.multi
    def action_confirm(self):
        if self.state != 'to_confirm':
            return True
        self.state = 'confirm'

    @api.multi
    def action_cancel(self):
        if self.state not in ('to_confirm', 'confirm'):
            return True
        self.state = 'draft'

    @api.multi
    def action_rate(self):
        if self.state != 'confirm':
            raise except_orm('Cảnh báo!', ("Trạng thái bản ghi đã bị thay đổi vui lòng F5 hoặc load lại trang"))
        view = self.env.ref('pos_customer_deposit.pos_customer_deposit_line_form_view_deposit')
        return {
            'name': _('Customer Signature'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'pos.customer.deposit.line',
            'views': [(view.id, 'form')],
            'res_id': self.id,
            'view_id': view.id,
            'target': 'new',
            'context': self.env.context,
        }

    @api.multi
    def action_done(self):
        if self.state != 'confirm':
            return True
        DepositObj = self.env['pos.customer.deposit']
        deposit_id = DepositObj.search([('partner_id', '=', self.partner_id.id)], limit=1)
        if self.type == 'deposit':
            if not deposit_id:
                if not self.session_id.config_id.journal_deposit_id:
                    raise except_orm('Cảnh báo!', ("Điểm bán hàng của bạn chưa cấu hình phương thức ghi nhận đặt cọc"))
                vals = {
                    'name': self.partner_id.name,
                    'partner_id': self.partner_id.id,
                    'journal_id': self.session_id.config_id.journal_deposit_id.id,
                }
                master_id = DepositObj.create(vals)
                self.deposit_id = master_id.id
            else:
                self.deposit_id = deposit_id.id
            if not self.deposit_id.journal_id.default_credit_account_id: raise except_orm('Thông báo', 'Sổ nhật ký %s chưa cấu hình tài khoản ghi có mặc định!' % (str(self.deposit_id.journal_id.name),))
            if not self.deposit_id.journal_id.default_debit_account_id: raise except_orm('Thông báo', 'Sổ nhật ký %s chưa cấu hình tài khoản ghi nợ mặc định!' % (str(self.deposit_id.journal_id.name),))

            # TODO: Tiennq
            # tang x_balancce trong res_partner
            self.partner_id.x_balance = self.partner_id.x_balance + self.amount
            # cong doanh thu cho KH
            self.partner_id.x_loyal_total = self.partner_id.x_loyal_total + self.amount
            revenue = self.env['crm.vip.customer.revenue'].create({
                'partner_id': self.partner_id.id,
                'journal_id': self.journal_id.id,
                'amount': self.amount,
                'date': self.date,
                'order_id': False,
            })
            # cong điểm tích lũy cho KH
            # point = self._get_loyal_total(self.amount)
            # self.partner_id.x_point_total = self.partner_id.x_point_total + point
            # point_history = self.env['izi.vip.point.history'].create({
            #     'partner_id': self.partner_id.id,
            #     'date': self.date,
            #     'point': point,
            #     'order_id': False,
            # })
            # phan bo daonh thu cho NV
            revenue_id = self._auto_allocation(self.amount)
            self.revenue_id = revenue_id.id
            # datcoc
            move_lines = []
            credit_move_vals = {
                'name': self.name,
                'account_id': self.deposit_id.journal_id.default_credit_account_id.id,
                'credit': self.amount,
                'debit': 0.0,
                'partner_id': self.partner_id.id,
            }
            debit_move_vals = {
                'name': self.name,
                'account_id': self.journal_id.default_debit_account_id.id,
                'credit': 0.0,
                'debit': self.amount,
                'partner_id': self.partner_id.id,
            }
            move_lines.append((0, 0, debit_move_vals))
            move_lines.append((0, 0, credit_move_vals))
            vals_account = {
                'date': fields.Datetime.now(),
                'ref': self.name,
                'journal_id': self.journal_id.id,
                'line_ids': move_lines
            }
            move_id = self.env['account.move'].create(vals_account)
            move_id.post()

            # Send message về cho tư vấn co user về khách hàng thanh toán
            # self = self.sudo()
            # partner_ids = []
            # if self.partner_id.x_manage_user_id:
            #     if self.partner_id.x_manage_user_id.partner_id:
            #         partner_ids.append(self.partner_id.x_manage_user_id.partner_id)
            # for partner in partner_ids:
            #     odoobot_id = self.env['ir.model.data'].xmlid_to_res_id("base.partner_root")
            #     channel = self.env['mail.channel.payment'].search([('partner_id', '=', partner.id)])
            #     if channel:
            #         message = _(
            #             "<br/>Ngày %s khách hàng %s đặt cọc với số tiền là %s với hình thức là %s</b>" % (
            #                 my_date.today().strftime("%d-%m-%Y"), self.partner_id.name,
            #                 self.convert_numbers_to_text_sangla(self.amount),
            #                 self.journal_id.name))
            #         channel.mail_channel_id.sudo().message_post(body=message, author_id=odoobot_id,
            #                                                     message_type="comment",
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
            #             "<br/>Ngày %s khách hàng %s đặt cọc với số tiền là %s với hình thức là %s</b>" % (
            #                 my_date.today().strftime("%d-%m-%Y"), self.partner_id.name,
            #                 self.convert_numbers_to_text_sangla(self.amount),
            #                 self.journal_id.name))
            #         channel.sudo().message_post(body=message, author_id=odoobot_id, message_type="comment",
            #                                     subtype="mail.mt_comment")
        # hoantien
        if self.type == 'cash':

            if not self.deposit_id.journal_id.default_credit_account_id: raise except_orm('Thông báo', 'Sổ nhật ký %s chưa cấu hình tài khoản ghi có mặc định!' % (str(self.deposit_id.journal_id.name),))
            if not self.deposit_id.journal_id.default_debit_account_id: raise except_orm('Thông báo', 'Sổ nhật ký %s chưa cấu hình tài khoản ghi nợ mặc định!' % (str(self.deposit_id.journal_id.name),))

            # TODO: Tiennq
            # giảm x_balancce trong res_partner
            self.partner_id.x_balance = self.partner_id.x_balance - self.amount
            # giảm doanh thu của KH
            self.partner_id.x_loyal_total = self.partner_id.x_loyal_total - self.amount
            revenue = self.env['crm.vip.customer.revenue'].create({
                'partner_id': self.partner_id.id,
                'journal_id': self.journal_id.id,
                'amount': (- self.amount),
                'date': self.date,
                'order_id': False
            })
            # giảm điểm tích lũy của KH
            # point = self._get_loyal_total(self.amount)
            # self.partner_id.x_point_total = self.partner_id.x_point_total - point
            # point_history = self.env['izi.vip.point.history'].create({
            #     'partner_id': self.partner_id.id,
            #     'date': self.date,
            #     'point': (- point),
            #     'order_id': False,
            # })
            # trừ daonh thu NV
            revenue_id = self._auto_allocation(-(self.amount - self.charge_refund))
            revenue_id.amount_allocated = 0
            revenue_id.amount_res = -(self.amount - self.charge_refund)
            self.revenue_id = revenue_id.id
            # hoantien
            move_lines = []
            debit_move_vals = {
                'name': self.name,
                'account_id': self.deposit_id.journal_id.default_debit_account_id.id,
                'debit': self.amount,
                'credit': 0.0,
                'partner_id': self.partner_id.id,
            }
            credit_move_vals = {
                'name': self.name,
                'account_id': self.journal_id.default_credit_account_id.id,
                'debit': 0.0,
                'credit': self.amount,
                'partner_id': self.partner_id.id,
            }
            move_lines.append((0, 0, debit_move_vals))
            move_lines.append((0, 0, credit_move_vals))
            vals_account = {
                'date': fields.Datetime.now(),
                'ref': self.name,
                'journal_id': self.journal_id.id,
                'line_ids': move_lines
            }
            move_id = self.env['account.move'].create(vals_account)
            move_id.post()
            # Send message về cho tư vấn co user về khách hàng hoàn tiền
            # self = self.sudo()
            # partner_ids = []
            # if self.partner_id.x_manage_user_id:
            #     if self.partner_id.x_manage_user_id.partner_id:
            #         partner_ids.append(self.partner_id.x_manage_user_id.partner_id)
            # for partner in partner_ids:
            #     odoobot_id = self.env['ir.model.data'].xmlid_to_res_id("base.partner_root")
            #     channel = self.env['mail.channel.payment'].search([('partner_id', '=', partner.id)])
            #     if channel:
            #         message = _(
            #             "<br/>Ngày %s hoàn tiền cho khách hàng %s với số tiền là - %s với hình thức là %s</b>" % (
            #                 my_date.today().strftime("%d-%m-%Y"), self.partner_id.name,
            #                 self.convert_numbers_to_text_sangla(self.amount),
            #                 self.journal_id.name))
            #         channel.mail_channel_id.sudo().message_post(body=message, author_id=odoobot_id,
            #                                                     message_type="comment",
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
            #             "<br/>Ngày %s hoàn tiền cho khách hàng %s với số tiền là - %s với hình thức là %s</b>" % (
            #                 my_date.today().strftime("%d-%m-%Y"), self.partner_id.name,
            #                 self.convert_numbers_to_text_sangla(self.amount),
            #                 self.journal_id.name))
            #         channel.sudo().message_post(body=message, author_id=odoobot_id, message_type="comment",
            #                                     subtype="mail.mt_comment")
        self.deposit_id.account_move_ids = [(4, move_id.id)]
        # tạo account.bank.statement.line
        statement_id = False
        for statement in self.session_id.statement_ids:
            if statement.id == statement_id:
                journal_id = statement.journal_id.id
                break
            elif statement.journal_id.id == self.journal_id.id:
                statement_id = statement.id
                break
        company_cxt = dict(self.env.context, force_company=self.journal_id.company_id.id)
        account_def = self.env['ir.property'].with_context(company_cxt).get('property_account_receivable_id',
                                                                            'res.partner')
        account_id = self.partner_id.property_account_receivable_id.id or (account_def and account_def.id) or False
        amount = self.amount
        amount_currency = self.x_money_multi
        if self.type == 'cash':
            amount = -(self.amount - self.charge_refund)
            amount_currency = self.rate_vn and (amount / self.rate_vn) or 0
        argvs = {
            'ref': self.name,
            'name': 'Deposit',
            'partner_id': self.partner_id.id,
            'amount': amount,
            'account_id': account_id,
            'statement_id': statement_id,
            'journal_id': self.journal_id.id,
            'date': self.date,
            'x_amount_currency': amount_currency,
            'x_currency_id': self.x_currency_id.id,
            # 'x_currency_rate_id': self.x_currency_rate_id.id,
        }
        pos_make_payment_id = self.env['account.bank.statement.line'].create(argvs)
        self.state = 'done'

    # @api.multi
    # def action_cancel(self):
    #     self.state = 'cancel'

    @api.multi
    def unlink(self):
        for line in self:
            if line.state != 'draft':
                raise except_orm('Thông báo!', (
                    "Không thể xóa bản ghi ở trạng thái khác bản thảo"))
        return super(PosCustomerDepositLine, self).unlink()

    # copy code lởm(tiennq)
    # @api.multi
    # def _get_loyal_total(self, loyal_total):
    #     config_id = self.session_id.config_id.id
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

    def _auto_allocation(self, amount):
        # employee_id = self.env['hr.employee'].sudo().search(['|', ('user_id', '=', self.user_id.id), ('x_user_ids', 'in', [self.user_id.id])], limit=1)
        # if not employee_id:
        #     raise except_orm('Thông báo', 'Không tìm thấy nhân viên có liên kết với người dùng %s. Liên hệ quản lý để được giải quyết!' % (str(self.user_id.name)))
        Allocation = self.env['pos.revenue.allocation']
        AllocationLine = self.env['pos.revenue.allocation.line']
        vals = {
            'order_id': False,
            'partner_name': self.partner_id.name,
            'partner_id' : self.partner_id.id,
            'partner_code': self.partner_id.x_code,
            'amount_total': amount,
            'amount_allocated': amount,
            'amount_res': 0,
            'date': self.date,
            'state': 'close',
            'pos_session_id': self.session_id.id,
            'session_id':  self.session_id.name,
        }
        revenua_id = Allocation.create(vals)
        if amount > 0:
            note = 'KH đặt cọc'
        else:
            note = 'Hoàn tiền KH'
        count_nvtv = 0
        for item in self.x_user_id:
            if item.job_id.x_code == 'NVTV':
                count_nvtv += 1
        count = len(self.x_user_id)
        if count == count_nvtv or count_nvtv == 0:
            if count_nvtv == 0:
                note = 'Nhân viên thừa hưởng'
            else:
                note = 'Nhân viên tư vấn'
            for item in self.x_user_id:
                vals_line = {
                    'employee_id': item.id,
                    'amount': amount / count,
                    'amount_total': amount / count,
                    'product_id':False,
                    'order_id': False,
                    'note': note,
                    'percent': 1,
                    'revenue_allocation_id': revenua_id.id,
                }
                AllocationLine.create(vals_line)
        else:
            for item in self.x_user_id:
                if item.job_id.x_code == 'NVTV':
                    vals_line = {
                        'employee_id': item.id,
                        'amount': amount / (2 * count_nvtv),
                        'amount_total': amount / (2 * count_nvtv),
                        'product_id': False,
                        'order_id': False,
                        'note': 'Nhân viên tư vấn',
                        'percent': 1,
                        'revenue_allocation_id': revenua_id.id,
                    }
                    AllocationLine.create(vals_line)
                else:
                    vals_line = {
                        'employee_id': item.id,
                        'amount': amount / (2 * (count - count_nvtv)),
                        'amount_total': amount / (2 * (count - count_nvtv)),
                        'product_id': False,
                        'order_id': False,
                        'note': 'Nhân viên thừa hưởng',
                        'percent': 1,
                        'revenue_allocation_id': revenua_id.id,
                    }
                    AllocationLine.create(vals_line)
        return revenua_id

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