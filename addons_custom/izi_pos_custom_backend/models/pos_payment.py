# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import UserError, MissingError, ValidationError, except_orm
from datetime import date, datetime
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT


class PosMakePayment(models.TransientModel):
    _inherit = 'pos.make.payment'

    def _compute_partner_id(self):
        active_id = self.env.context.get('active_id')
        if active_id:
            self.x_partner_id = self.env['pos.order'].browse(active_id).partner_id
        else:
            raise MissingError("Đơn hàng thiếu thông tin khách hàng")

    def _show_vm_amount_total(self):
        self.x_vm_amount_total = self.env['pos.virtual.money'].get_available_amount_by_partner(self.x_partner_id.id)
        self.x_show_vm_amount = True
        if self.x_vm_amount_total < self.amount:
            self.amount = self.x_vm_amount_total

    def _show_deposit_amount_residual(self):
        deposit_lines = self.env['pos.customer.deposit'].search([('partner_id', '=', self.x_partner_id.id)])
        total = 0.0
        for line in deposit_lines:
            total += line.residual
        self.x_deposit_amount_residual = total
        self.x_show_deposit_amount = True
        if self.x_deposit_amount_residual < self.amount:
            self.amount = self.x_deposit_amount_residual

    x_show_vm_amount = fields.Boolean(default=False, store=False)
    x_vm_amount_total = fields.Float('Tài khoản thẻ tiền', compute=_show_vm_amount_total, store=False)
    x_partner_id = fields.Many2one('res.partner', readonly=True, store=False, compute=_compute_partner_id)
    x_lock_amount = fields.Boolean(readonly=True, default=False, store=False)
    x_show_vc_code = fields.Boolean(readonly=True, default=False, store=False)
    x_vc_code = fields.Char('Coupon code')
    x_deposit_amount_residual = fields.Float("Deposit Amount Residualt", compute=_show_deposit_amount_residual, store=False)
    x_show_deposit_amount = fields.Boolean('Show Deposit Amount', default=False, store=False)
    x_required_ref = fields.Boolean('Required payment name', default=False, store=False)

    @api.multi
    def read(self, fields=None, load='_classic_read'):
        result = super(PosMakePayment, self).read(fields, load=load)
        for record in result:
            record['x_required_ref'] = False
            record['x_show_vm_amount'] = False
            record['x_show_deposit_amount'] = False
            record['x_lock_amount'] = False
            if isinstance(record['journal_id'], tuple):
                journal_id = self.env['account.journal'].browse(record['journal_id'][0])
            else:
                journal_id = self.env['account.journal'].browse(record['journal_id'])
            if journal_id.code.upper() == 'VM':
                record['x_show_vm_amount'] = True
                if not self.x_partner_id:
                    self._compute_partner_id()
                record['x_vm_amount_total'] = self.env['pos.virtual.money'].get_available_amount_by_partner(self.x_partner_id.id)
            elif journal_id.code.upper() == 'VC':
                record['x_show_vc_code'] = True
                record['x_lock_amount'] = True
            elif journal_id.id == self.session_id.config_id.journal_deposit_id.id:
                record['x_show_deposit_amount'] = True
                if not self.x_partner_id:
                    self._compute_partner_id()
                deposit_lines = self.env['pos.customer.deposit'].search([('partner_id', '=', self.x_partner_id.id)])
                total = 0.0
                for line in deposit_lines:
                    total += line.residual
                record['x_deposit_amount_residual'] = total
            elif journal_id.id in self.session_id.config_id.journal_exception_ids.ids:
                record['x_required_ref'] = True
        return result

    @api.onchange('x_vc_code')
    def onchange_vc_code(self):
        if self.x_vc_code:
            order = self.env['pos.order'].browse(self.env.context.get('active_id', False))
            # order_amount = order.amount_total - order.amount_paid
            vc = self.env['stock.production.lot'].search(
                [('name', '=', self.x_vc_code.upper().strip())], limit=1)
            vc._invalidate_vc_code(self.x_partner_id.id)
            # Nếu là Voucher
            if vc.x_discount == 0:
                self.amount = vc.x_amount if vc.x_amount <= order.amount_total else order.amount_total
            # Ngược lại là Coupon
            else:
                to_discount = order.amount_total * vc.x_discount / 100.0
                if vc.x_amount and to_discount > vc.x_amount:
                    to_discount = vc.x_amount
                self.amount = to_discount if to_discount <= order.amount_total else order.amount_total

    @api.onchange('journal_id')
    def _onchange_journal_id(self):
        if self.journal_id:
            order = self.env['pos.order'].browse(self.env.context.get('active_id', False))
            if not order:
                raise UserError("Order could not be found!")
            registed = 0.0
            for line in order.statement_ids:
                registed += line.amount
            self.amount = order.amount_total - registed
            self.x_lock_amount = False
            self.x_show_vm_amount = False
            self.x_show_vc_code = False
            self.x_show_deposit_amount = False
            self.x_required_ref = False
            if self.journal_id.code.upper() == 'VM':
                self._show_vm_amount_total()
            elif self.journal_id.code.upper() == 'VC':
                self.x_lock_amount = True
                self.x_show_vc_code = True
                self.onchange_vc_code()
            elif self.journal_id.id == self.session_id.config_id.journal_deposit_id.id:
                self._show_deposit_amount_residual()
            else:
                self.x_vc_code = False
            if self.journal_id.id in self.session_id.config_id.journal_exception_ids.ids:
                self.x_required_ref = True

    @api.multi
    def check(self):
        self.ensure_one()
        order = self.env['pos.order'].browse(self.env.context.get('active_id', False))
        order_amount = order.amount_total - order.amount_paid
        context = dict(self._context or {})
        context['izi_vc_id'] = False
        # Sangla thêm kiểm tra nếu là các hình thức khác ngoại tệ thì không cho phép nó thanh toán quá số tiền trong đơn hàng
        if self.journal_id.id not in self.session_id.config_id.x_journal_currency_ids.ids:
            if abs(self.amount) > abs(order_amount):
                raise except_orm("Cảnh báo!", ("Bạn không thể thanh toán sô tiền lớn hơn số tiền còn lại"))

        if self.amount == 0: raise except_orm('Thông báo', 'Không thể tạo thanh toán 0 đồng!')

        # Kiểm tra thanh toán đã đủ tiền cho hóa đơn thì không cho thanh toán dương nữa.
        if order_amount <= 0 and not order.x_pos_partner_refund_id:

            if self.amount > 0: raise except_orm('Thông báo', 'Đã thanh toán đủ tiền không thể thanh toán thêm!')
            if self.amount < order_amount: raise except_orm('Thông báo',
                                                            'Khách thanh toán thừa %s đ không thể trả lại nhiều hơn số đó' % (
                                                            str("{:,}".format(abs(order_amount))),))
        if order_amount >= 0 and order.x_pos_partner_refund_id:
            if self.amount < 0: raise except_orm('Thông báo', 'Đã thanh toán đủ tiền không thể thanh toán thêm!')
            if self.amount > order_amount: raise except_orm('Thông báo',
                                                            'Khách thanh toán thừa %s không thể trả lại nhiều hơn số đó' % (
                                                            str(abs(order_amount)),))
        if len(order.statement_ids) > 0:
            if self.amount == 0:
                raise except_orm("Thông báo!", ("Bạn không thể thanh toán số tiền bằng 0"))
            for x in order.statement_ids:
                if x.amount == 0:
                    raise except_orm("Thông báo", ("Không thể thanh toán 0 đồng cho đơn hàng"))

        # Thanh toán bằng thẻ tiền
        if self.journal_id.code.upper() == 'VM':
            # Lấy tổng tiền ảo của KH
            vm_amount = self.env['pos.virtual.money'].get_available_amount_by_partner(self.x_partner_id.id)
            # Nếu không đủ tiền thì báo lỗi
            if vm_amount < self.amount:
                raise UserError("Tài khoản thẻ tiền của khách hàng không đủ %s để thanh toán" % self.amount)
        # Thanh toán bằng tiền đặt cọc
        elif self.journal_id.id == self.session_id.config_id.journal_deposit_id.id:
            deposit_lines = self.env['pos.customer.deposit'].search([('partner_id', '=', self.x_partner_id.id)])
            total = 0.0
            for line in deposit_lines:
                total += line.residual
            if total < self.amount:
                raise UserError("Tài khoản đặt cọc của khách hàng không đủ để thanh toán")
        # Thanh toán bằng phiếu mua hàng
        elif self.journal_id.code.upper() == 'VC':
            if not self.x_partner_id:
                self._compute_partner_id()
            if self.x_vc_code:
                vc = self.env['stock.production.lot'].search(
                    [('name', '=', self.x_vc_code.upper().strip())], limit=1)
                self.x_show_vc_code = True
                vc._invalidate_vc_code(self.x_partner_id.id)
                self.x_lock_amount = True
                # Nếu là Voucher
                if vc.x_discount == 0:
                    self.amount = vc.x_amount if vc.x_amount <= order.amount_total else order.amount_total
                # Ngược lại là Coupon
                else:
                    to_discount = order.amount_total * vc.x_discount / 100.0
                    if vc.x_amount and to_discount > vc.x_amount:
                        to_discount = vc.x_amount
                    self.amount = to_discount if to_discount <= order.amount_total else order.amount_total
                context['izi_vc_id'] = vc.id
            else:
                raise UserError("Vui lòng nhập mã phiếu mua hàng!")
        # Kiểm tra xem trên đơn hàng có bán sp 2 dòng ko
        voucher_dict_payment = {}
        # Kiểm tra xem đơn hàng có gắn với hồ sơ trị liệu không
        name_therapy = order.check_therapy_record()
        if not order.x_pos_partner_refund_id and not name_therapy:
            for line in order.lines:
                if line.product_id.product_tmpl_id.x_type_card == 'pmh':
                    continue
                if line.x_is_gift == True or line.discount == 100:
                    continue
                else:
                    if line.product_id.id not in voucher_dict_payment:
                        voucher_dict_payment[line.product_id.id] = line.product_id.id
                        voucher_dict_payment['%s_amount' % line.product_id.id] = 1
                    else:
                        key = '%s_amount' % line.product_id.id
                        max_amount = voucher_dict_payment[key] + 1
                        voucher_dict_payment['%s_amount' % line.product_id.id] = max_amount
            for line in order.lines:
                if line.product_id.product_tmpl_id.x_type_card == 'pmh':
                    continue
                if line.x_is_gift == True or line.discount == 100:
                    continue
                else:
                    key = '%s_amount' % line.product_id.id
                    if voucher_dict_payment[key] > 1:
                        raise UserError("Không thể bán 1 dịch vụ hoặc sản phẩm với 2 dòng khác nhau")

        return super(PosMakePayment, self.with_context(context)).check()

    def launch_payment(self):
        if self._context.get('izi_pos_check', False):
            return {
                'name': _('Payment'),
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'pos.make.payment',
                'view_id': self.env.ref('izi_pos_custom_backend.izi_view_pos_payment_pos_order').id,
                'target': 'new',
                'views': False,
                'type': 'ir.actions.act_window',
                'context': self.env.context,
            }
        return super(PosMakePayment, self).launch_payment()
