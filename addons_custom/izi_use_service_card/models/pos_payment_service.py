# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from datetime import date, datetime
from odoo.exceptions import except_orm, UserError, MissingError, ValidationError

class PosPaymentService(models.Model):
    _name = 'pos.payment.service'

    def _default_amount(self):
        active_id = self.env.context.get('active_id')
        if active_id:
            order = self.env['izi.service.card.using'].browse(active_id)
            tmp = 0
            for line in order.service_card1_ids:
                tmp += line.amount
            tmp1 = 0
            for line in order.pos_payment_service_ids:
                tmp1 += line.amount
            return (tmp - tmp1)
        return False

    def _default_journal(self):
        active_id = self.env.context.get('active_id')
        if active_id:
            pos_session = self.env['pos.session']
            pos_config_id = self.env.user.x_pos_config_id.id
            my_session = pos_session.search([('config_id', '=', pos_config_id), ('state', '=', 'opened')])
            return my_session.config_id.journal_ids and my_session.config_id.journal_ids.ids[0] or False
        return False

    def _compute_partner_id(self):
        active_id = self.env.context.get('active_id')
        if active_id:
            self.x_partner_id = self.env['izi.service.card.using'].browse(active_id).customer_id
        else:
            raise MissingError("Đơn hàng thiếu thông tin khách hàng")

    def _compute_vm_amount_total(self):
        if not self.x_partner_id:
            self._compute_partner_id()
        self.x_vm_amount_total = self.env['pos.virtual.money'].get_available_amount_by_partner(self.x_partner_id.id)
        if self.x_vm_amount_total < self.amount:
            self.amount = self.x_vm_amount_total

    def _show_deposit_amount_residual(self):
        if not self.x_partner_id:
            self._compute_partner_id()
        deposit_lines = self.env['pos.customer.deposit'].search([('partner_id', '=', self.x_partner_id.id)])
        total = 0.0
        for line in deposit_lines:
            total += line.residual
        self.x_deposit_amount_residual = total
        if self.x_deposit_amount_residual < self.amount:
            self.amount = self.x_deposit_amount_residual

    x_show_vm_amount = fields.Boolean(default=False, store=False)
    x_vm_amount_total = fields.Float('Tài khoản thẻ tiền', compute=_compute_vm_amount_total, store=False)
    x_partner_id = fields.Many2one('res.partner', readonly=True, store=False, compute=_compute_partner_id)
    x_lock_amount = fields.Boolean(readonly=True, default=False, store=False)
    x_show_vc_code = fields.Boolean(readonly=True, default=False, store=False)
    x_vc_code = fields.Char('Coupon code')
    journal_id = fields.Many2one('account.journal', "Journal")
    amount = fields.Float("Amount", default=_default_amount)
    using_service_id = fields.Many2one('izi.service.card.using', 'Using service')
    x_deposit_amount_residual = fields.Float("Deposit Amount Residualt", compute=_show_deposit_amount_residual,
                                             store=False)
    x_show_deposit_amount = fields.Boolean('Show Deposit Amount', default=False, store=False)

    @api.onchange('using_service_id')
    def _on_change_using_service(self):
        if self.using_service_id:
            pos_session = self.env['pos.session']
            pos_config_id = self.env.user.x_pos_config_id.id
            my_session = pos_session.search([('config_id', '=', pos_config_id), ('state', '=', 'opened')])
            return {
                'domain': {'journal_id': [('id', 'in', my_session.config_id.journal_ids.ids)]}
            }

    @api.onchange('journal_id')
    def onchange_journal_id(self):
        registed = 0.0
        for line in self.using_service_id.pos_payment_service_ids:
            registed += line.amount
        registed -= self.amount
        self.amount = self.using_service_id.amount_total - registed
        self.x_show_vm_amount = False
        self.x_show_vc_code = False
        self.x_show_deposit_amount = False
        if self.journal_id:
            if self.journal_id.code.upper() == 'VM':
                self._compute_vm_amount_total()
                self.x_show_vm_amount = True
            elif self.journal_id.code.upper() == 'VC':
                self.x_show_vc_code = True
            elif self.journal_id.id == self.using_service_id.pos_session_id.config_id.journal_deposit_id.id:
                self._show_deposit_amount_residual()
                self.x_show_deposit_amount = True
        ids = []
        active_id = self.env.context.get('active_id')
        if active_id:
            pos_session = self.env['pos.session']
            pos_config_id = self.env.user.x_pos_config_id.id
            my_session = pos_session.search([('config_id', '=', pos_config_id), ('state', '=', 'opened')])
            for line in my_session.config_id.journal_ids:
                ids.append(line.id)
            return {
                'domain': {
                    'journal_id': [('id', 'in', ids)]
                }
            }

    @api.onchange('x_vc_code')
    def onchange_vc_code(self):
        if not self.x_partner_id:
            self._compute_partner_id()
        if self.x_vc_code:
            vc = self.env['stock.production.lot'].search(
                [('name', '=', self.x_vc_code.upper().strip())], limit=1)
            if not vc:
                raise MissingError("Mã phiếu mua hàng không tồn tại!")
            elif vc.x_status != 'using':
                raise UserError("Phiếu mua hàng không thuộc trạng thái có thể sử dụng được!")
            elif vc.life_date and datetime.strptime(vc.life_date, '%Y-%m-%d %H:%M:%S').date() < date.today():
                raise ValidationError("Phiếu mua hàng đã quá hạn sử dụng!")
            elif vc.x_release_id.use_type == '0' and vc.x_customer_id.id != self.x_partner_id.id:
                raise ValidationError("Phiếu mua hàng đã nhập thuộc khách hàng khác và chỉ sử dụng đúng định danh!")
            else:
                self.x_lock_amount = True
                # Nếu là Voucher
                if vc.x_discount == 0:
                    self.amount = vc.x_amount if vc.x_amount <= self.amount else self.amount
                # Ngược lại là Coupon
                else:
                    to_discount = self.amount * vc.x_discount / 100.0
                    if to_discount > vc.x_amount:
                        to_discount = vc.x_amount
                    self.amount = to_discount if to_discount <= self.amount else self.amount
        else:
            self.x_lock_amount = False

    # @api.onchange('journal_id')
    # def _onchange_journal_id(self):
    #     self.x_show_vm_amount = False
    #     self.x_show_vc_code = False
    #     self.x_show_deposit_amount = False
    #     if self.journal_id.code.upper() == 'VM':
    #         self._compute_vm_amount_total()
    #         self.x_show_vm_amount = True
    #     elif self.journal_id.code.upper() == 'VC':
    #         self.x_show_vc_code = True
    #     elif self.journal_id.id == self.using_service_id.pos_session_id.config_id.journal_deposit_id.id:
    #         self._show_deposit_amount_residual()
    #         self.x_show_deposit_amount = True

    # @api.model
    # def create(self, vals):
    #     res = super(PosPaymentService, self).create(vals)
    #     if res.amount < 0:
    #         raise except_orm('Cảnh báo!', ("Bạn không thể thanh toán số tiền nhỏ hơn không"))
    #     else:
    #         return res

    @api.multi
    def process_payment_service(self):
        active_id = self.env.context.get('active_id')
        if active_id:
            order = self.env['izi.service.card.using'].browse(active_id)
            total_amount_service = 0
            for line in order.service_card1_ids:
                total_amount_service += line.amount
            total_amount_payment_service = 0
            for line in order.pos_payment_service_ids:
                total_amount_payment_service += line.amount
        total_amount = total_amount_service - total_amount_payment_service + self.amount

        if self.amount == 0: raise except_orm('Thông báo', 'Không thể thanh toán 0 đồng.')

        #Kiểm tra thanh toán đã đủ tiền cho hóa đơn thì không cho thanh toán dương nữa.
        if total_amount <= 0:
            if self.amount > 0: raise except_orm('Thông báo', 'Đã thanh toán đủ tiền không thể thanh toán thêm!')
            if self.amount < total_amount: raise except_orm('Thông báo', 'Khách thanh toán thừa %s đ không thể trả lại nhiều hơn số đó' % (str("{:,}".format(abs(total_amount))), ))

        if self.amount == 0:
            self.unlink()
            return {'type': 'ir.actions.act_window_close'}
        # if abs(self.amount) > abs(total_amount):
        #     raise UserError("Số tiền thanh toán không lớn hơn số tiền cần thanh toán!")
        if self.journal_id.code.upper() == 'VM':
            # Nếu không đủ tiền thì báo lỗi
            self._compute_vm_amount_total()
            if self.x_vm_amount_total < self.amount:
                self.unlink()
                raise UserError("Tài khoản thẻ tiền của khách hàng không đủ để thanh toán")
        elif self.journal_id.id == self.using_service_id.pos_session_id.config_id.journal_deposit_id.id:
            deposit_lines = self.env['pos.customer.deposit'].search([('partner_id', '=', self.x_partner_id.id)])
            total = 0.0
            for line in deposit_lines:
                total += line.residual
            if total < self.amount:
                raise UserError("Tài khoản đặt cọc của khách hàng không đủ %s để thanh toán" % self.amount)
        if self._default_amount() == 0:
            # self.using_service_id.update({'state': 'wait_approve'})
            return {'type': 'ir.actions.act_window_close'}
        else:
            return self.launch_payment()

    def launch_payment(self):
        # return {
        #     'name': _('Payment'),
        #     'view_type': 'form',
        #     'view_mode': 'form',
        #     'res_model': 'pos.payment.service',
        #     'view_id': False,
        #     'target': 'new',
        #     'views': [(False, 'form')],
        #     'type': 'ir.actions.act_window',
        #     'context': self.env.context,
        # }
        if self.env.context is None:
            context = {}
        ctx = self.env.context.copy()
        ctx.update({'default_using_service_id': self.using_service_id.id})
        view = self.env.ref('izi_use_service_card.view_pop_up_pos_payment_service')
        return {
            'name': _('Payment Service'),
            'type': 'ir.actions.act_window',
            'res_model': 'pos.payment.service',
            'view_mode': 'form',
            'view_type': 'form',
            'views': [(view.id, 'form')],
            'view_id': view.id,
            # 'res_id': self.id,
            'target': 'new',
            'context': self.env.context,
        }

    @api.multi
    def action_cancel(self):
        self.unlink()
        return {'type': 'ir.actions.act_window_close'}
