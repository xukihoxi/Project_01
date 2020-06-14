# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import except_orm, UserError, MissingError
from datetime import datetime, date as my_date


class PosDestroyService(models.Model):
    _name = 'pos.destroy.service'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    @api.model
    def default_get(self, fields):
        res = super(PosDestroyService, self).default_get(fields)
        user_id = self.env['res.users'].search([('id', '=', self.env.uid)], limit=1)
        config_id = user_id.x_pos_config_id.id
        current_session = self.env['pos.session'].search([('state', '!=', 'closed'), ('config_id', '=', config_id)],
                                                         limit=1)
        if not current_session:
            raise except_orm(("Cảnh báo!"), ('Bạn phải mở phiên trước khi tạo đơn hàng mới.'))
        return res

    def _default_session(self):
        user_id = self.env['res.users'].search([('id', '=', self.env.uid)], limit=1)
        config_id = user_id.x_pos_config_id.id
        return self.env['pos.session'].search([('state', '=', 'opened'), ('config_id', '=', config_id)], limit=1)

    def _default_pricelist(self):
        return self._default_session().config_id.pricelist_id

    name = fields.Char("Name", default="/", copy=False, track_visibility='onchange')
    serial = fields.Char("Serial", track_visibility='onchange')
    partner_id = fields.Many2one('res.partner', 'Partner', track_visibility='onchange')
    product_lot_id = fields.Many2one('stock.production.lot', 'Product Lot', track_visibility='onchange')
    date = fields.Date("Date", required=True, default=fields.Date.context_today, track_visibility='onchange')
    new_order_id = fields.Many2one('pos.order', "Order", track_visibility='onchange')
    note = fields.Text("Note", track_visibility='onchange')
    pricelist_id = fields.Many2one('product.pricelist', string='Pricelist', required=True, readonly=True,
                                   default=_default_pricelist, track_visibility='onchange')
    signature_image = fields.Binary("Signature Image", default=False, attachment=True, track_visibility='onchange')
    destroy_service_lines = fields.One2many('pos.destroy.service.line', 'pos_destroy_service_id', "Destroy Service")
    destroy_service_detail_lines = fields.One2many('pos.destroy.service.line.detail', 'pos_destroy_service_id', "Detail")
    session_id = fields.Many2one(
        'pos.session', string='Session', required=True, index=True,
        readonly=True, default=_default_session)
    pos_order_id = fields.Many2one('pos.order', 'Old Order', track_visibility='onchange')
    state = fields.Selection(
        selection=(('draft', 'Draft'), ('wait_confirm', 'Wait Confirm'), ('wait_signature', "Wait Singature"), ('signature', "Signature"),('done', 'Done'), ('to_refund', 'To refund'), ('refunded', 'Refunded'),
                   ('cancel', 'Cancel')),
        default='draft', track_visibility='onchange')
    amount_total = fields.Float("Amount Total", compute='_compute_amount_total', store=True, track_visibility='onchange')
    payment_destroy_service_ids = fields.One2many('pos.payment.destroy.service','destroy_service_id', "Paymnet Destroy Service")
    partner_id = fields.Many2one('res.partner', string="Partner")

    @api.multi
    def unlink(self):
        for line in self:
            if line.state != 'draft':
                raise except_orm('Thông báo!', (
                    "Không thể xóa bản ghi ở trạng thái khác bản thảo"))
        return super(PosDestroyService, self).unlink()


    @api.depends('destroy_service_detail_lines')
    def _compute_amount_total(self):
        for line in self:
            for tmp in line.destroy_service_detail_lines:
                line.amount_total += tmp.price_subtotal_incl

    @api.onchange('destroy_service_detail_lines')
    def _onchange_quantity(self):
        for line in self:
            amount = 0
            amount_residual = self.pos_order_id.invoice_id.residual
            for tmp in line.destroy_service_detail_lines:
                amount += tmp.price_subtotal_incl
            if amount_residual == 0:
                for i in line.payment_destroy_service_ids:
                    if i.journal_id.id == self.session_id.config_id.journal_deposit_id.id:
                        i.amount = self.amount_total
                    if i.journal_id.id == self.session_id.config_id.journal_debt_id.id:
                        i.amount = 0
            else:
                if amount_residual > abs(amount):
                    for i in line.payment_destroy_service_ids:
                        if i.journal_id.id == self.session_id.config_id.journal_debt_id.id:
                            i.amount = self.amount_total
                        if i.journal_id.id == self.session_id.config_id.journal_deposit_id.id:
                            i.amount = 0
                else:
                    for i in line.payment_destroy_service_ids:
                        if i.journal_id.id == self.session_id.config_id.journal_debt_id.id:
                            i.amount = -amount_residual
                        if i.journal_id.id == self.session_id.config_id.journal_deposit_id.id:
                            i.amount = amount + amount_residual



    @api.model
    def create(self, vals):
        if vals.get('name', _('New')) == _('New'):
            vals['name'] = self.env['ir.sequence'].next_by_code('pos.destroy.service') or _('New')
        return super(PosDestroyService, self).create(vals)

    @api.multi
    def check_card(self):
        for line in self.destroy_service_lines:
            line.unlink()
        for line in self.destroy_service_detail_lines:
            line.unlink()
        PosOrderLine = self.env['pos.order.line']
        serial = self.serial.upper().strip()
        lot_obj = self.env['stock.production.lot'].search([('name', '=', serial)])
        if not lot_obj:
            raise except_orm('Cảnh báo!', ('Thẻ có mã "%s" không tồn tại trong hệ thống!' % serial))
        else:
            exchange = self.env['pos.destroy.service'].search(
                [('product_lot_id', '=', lot_obj.id), ('state', 'in', ('draft', 'wait_confirm', 'wait_signature', 'signature'))])
            if len(exchange) > 1:
                raise except_orm('Cảnh báo!', ('Thẻ có mã "%s" đang chờ thực thi ở đơn hủy khác!' % serial))
            if lot_obj.x_status == 'used':
                raise except_orm('Cảnh báo!', ('Thẻ có mã "%s" đã sử dụng hết!' % serial))
            if lot_obj.life_date and lot_obj.life_date < self.date:
                raise except_orm('Cảnh báo!', (('Thẻ có mã "%s" đã hết hạn vào ngày: ' + datetime.strptime(
                    lot_obj.life_date, "%Y-%m-%d %H:%M:%S").strftime("%d-%m-%Y")) % serial))
            if lot_obj.x_status == 'using':
                lines_lot = []
                for detail in lot_obj.x_card_detail_ids:
                    if detail.state == 'cancel':
                        continue
                    argvs = {
                        'card_id': detail.id,
                        'service_id': detail.product_id.id,
                        'price_unit': detail.price_unit,
                        'total_count': detail.total_qty,
                        'hand_count': detail.qty_hand,
                        'used_count': detail.qty_use,
                        'amount_total': detail.amount_total,
                        'remain_amount': detail.remain_amount,
                        'pos_destroy_service_id': self.id,
                    }
                    lines_lot.append(argvs)
                self.destroy_service_lines = lines_lot
                order = PosOrderLine.search([('lot_name', '=', lot_obj.name)])
                self.partner_id = lot_obj.x_customer_id.id
                self.product_lot_id = lot_obj.id
                self.pos_order_id = lot_obj.x_order_id.id
        return True

    @api.multi
    def process_rate_service(self):
        self.state = 'signature'
        return {'type': 'ir.actions.act_window_close'}


    @api.multi
    def action_compute(self):
        count_destroy = 0
        destroy_detail = self.env['pos.destroy.service.line.detail']
        for i in self.destroy_service_detail_lines:
            i.unlink()
        for y in self.payment_destroy_service_ids:
            y.unlink()
        for line in self.destroy_service_lines:
            if line.destroy_service == True:
                if line.total_count == line.used_count:
                    raise except_orm("Cảnh báo!", ("Dịch vụ %s này đã hết bạn không thể hủy" % line.service_id.name))
                count_destroy += 1
                # count = 0
                for tmp in self.product_lot_id.x_order_id.lines:
                    # Lấy dịch vụ có trong đơn hàng
                    if tmp.product_id.id == line.service_id.id and tmp.x_is_gift == False:
                        # count += 1
                        if tmp.x_quantity_refund == 0:
                            argvs = {
                                'service_id': tmp.product_id.id,
                                'quantity': -(tmp.qty - tmp.x_quantity_refund),
                                'price_unit': tmp.price_unit,
                                'discount': 0,
                                'x_discount': 0,
                                'subtotal_wo_discount': -tmp.x_subtotal_wo_discount,
                                'price_subtotal_incl': -tmp.price_subtotal_incl,
                                'pos_destroy_service_id': self.id
                            }
                            destroy_detail_id = destroy_detail.create(argvs)
                        else:
                            argvs = {
                                'service_id': tmp.product_id.id,
                                'quantity': -(tmp.qty - tmp.x_quantity_refund),
                                'price_unit': tmp.price_unit,
                                'discount': 0,
                                'x_discount': 0,
                                'subtotal_wo_discount': -(tmp.qty - tmp.x_quantity_refund)*tmp.price_unit,
                                'price_subtotal_incl': -(tmp.qty - tmp.x_quantity_refund)*tmp.price_unit,
                                'pos_destroy_service_id': self.id
                            }
                            destroy_detail_id = destroy_detail.create(argvs)
                # if count == 0:
                #     raise except_orm("Cảnh báo!", ("Dịch vụ này được đổi từ dich vụ khác bạn không thể hủy"))
                # count_service = 0
                # for tmp in self.product_lot_id.x_order_id.lines:
                #     if tmp.product_id.id == line.service_id.id:
                #         count_service += tmp.qty
                # if count_service != line.total_count:
                #     raise except_orm("Cảnh báo!", ("Dịch vụ này đã được đổi trong đơn đổi dịch vụ! Bạn không thể hủy"))
                # Tính số lần sử dụng dịch vụ trong thẻ
                for tmp in self.product_lot_id.x_card_detail_ids:
                    if tmp.product_id.id == line.service_id.id:
                        if tmp.qty_use == 0:
                            continue
                        argvs = {
                            'service_id': tmp.product_id.id,
                            'quantity': tmp.qty_use,
                            'price_unit': tmp.product_id.product_tmpl_id.list_price,
                            'discount': 0,
                            'x_discount': 0,
                            'subtotal_wo_discount': tmp.qty_use*tmp.product_id.product_tmpl_id.list_price,
                            'price_subtotal_incl': tmp.qty_use*tmp.product_id.product_tmpl_id.list_price,
                            'pos_destroy_service_id': self.id
                        }
                        destroy_detail_id = destroy_detail.create(argvs)
        if count_destroy == 0:
            raise except_orm("Cảnh báo!", ("Bạn phải chọn dịch vụ để hủy"))
        if not self.session_id.config_id.x_charge_refund_id:
            raise except_orm("Cảnh báo", ("Chưa cấu hình chi phí refund. Vui lòng liên hệ quản trị viên"))
        # Thêm 1 dòng chi phí refund vào phẩn hủy
        # destroy_detail.create({
        #     'service_id': self.session_id.config_id.x_charge_refund_id.id,
        #     'quantity': 1,
        #     'price_unit': 0,
        #     'discount': 0,
        #     'x_discount': 0,
        #     'subtotal_wo_discount': 0,
        #     'price_subtotal_incl': 0,
        #     'pos_destroy_service_id': self.id
        # })
        amount_residual = self.pos_order_id.invoice_id.residual
        # Nếu không còn ghi nợ trong đơn hàng ban đầu
        payment_destroy_obj = self.env['pos.payment.destroy.service']
        if amount_residual == 0:
            payment_destroy_obj.create({
                'journal_id': self.session_id.config_id.journal_deposit_id.id,
                'date': self.date,
                'amount': self.amount_total,
                'destroy_service_id': self.id
            })
            payment_destroy_obj.create({
                'journal_id': self.session_id.config_id.journal_debt_id.id,
                'date': self.date,
                'amount': 0,
                'destroy_service_id': self.id,
            })
        else:
            payment_destroy_obj = self.env['pos.payment.destroy.service']
            #  Số tiền nợ nhiều hơn số tiền mà khách hàng refund => Tạo bank  line với tất cả đều là nợ
            if amount_residual > abs(self.amount_total):
                payment_destroy_obj.create({
                    'journal_id': self.session_id.config_id.journal_debt_id.id,
                    'date': self.date,
                    'amount': self.amount_total,
                    'destroy_service_id': self.id,
                })
                payment_destroy_obj.create({
                    'journal_id': self.session_id.config_id.journal_deposit_id.id,
                    'date': self.date,
                    'amount': 0,
                    'destroy_service_id': self.id,
                })
            # Vừa tạo nợ và đặt coc
            else:
                payment_destroy_obj.create({
                    'journal_id': self.session_id.config_id.journal_debt_id.id,
                    'date': self.date,
                    'amount': -amount_residual,
                    'destroy_service_id': self.id,
                })
                payment_destroy_obj.create({
                    'journal_id': self.session_id.config_id.journal_deposit_id.id,
                    'date': self.date,
                    'amount': self.amount_total + amount_residual,
                    'destroy_service_id': self.id,
                })


    @api.multi
    def action_send(self):
        self.state = 'wait_confirm'
        if not self.destroy_service_detail_lines:
            raise except_orm("Cảnh báo!", ("Không có sản phẩm nào chọn để hủy"))
        if self.amount_total > 0:
            raise except_orm("Cảnh báo!", ("Bạn không gửi hủy dịch vụ. Số tiền khách hàng dùng lớn hơn số tiền còn lại!"))
        for line in self.destroy_service_detail_lines:
            for tmp in self.product_lot_id.x_card_detail_ids:
                if tmp.product_id.id == line.service_id.id:
                    if tmp.total_qty < -line.quantity:
                        raise except_orm('Cảnh báo!', ('Bạn không thể hủy số lượng dịch vụ lớn hơn sô dịch vụ trong thẻ'))
        a = 0 # tong tiền thanh toán
        for line in self.payment_destroy_service_ids:
            journal_count = 0
            for x in self.session_id.statement_ids:
                if line.journal_id.id == x.journal_id.id:
                    journal_count += 1
            if journal_count == 0:
                raise except_orm("Thông báo!", ("Không có hình thức trong phiên. VUi lòng kiểm tra hình thưc"))

        debit_amount = 0
        deposit_amount = 0
        for line in self.payment_destroy_service_ids:
            a += line.amount
            if line.journal_id.id == self.session_id.config_id.journal_deposit_id.id:
                deposit_amount += line.amount
            if line.journal_id.id == self.session_id.config_id.journal_debt_id.id:
                debit_amount += line.amount
        if a != self.amount_total:
            raise except_orm('Cảnh báo!', ("Số tiền thanh toán khác số tiền hủy. Vui lòng kiểm tra lại"))
        # if a == 0:
        #     raise except_orm('Cảnh báo!', ('Bạn không thể hủy dịch vụ mà số tiền cấn trừ bằng 0'))
        if self.pos_order_id.invoice_id:
            amount_residual = self.pos_order_id.invoice_id.residual
            total = 0
            for x in self.payment_destroy_service_ids:
                if x.journal_id.id == self.session_id.config_id.journal_debt_id.id:
                    total += x.amount
            if amount_residual == 0:
                if total != 0:
                    raise except_orm('Cảnh báo!', ("Hóa đơn hết công nợ không thể thể giảm công nợ"))
            amount_total = self.pos_order_id.invoice_id.amount_total
            amount_payment = 0
            account_payment_obj = self.pos_order_id.invoice_id.payment_ids
            total_payment_destroy = 0
            destroy_obj = self.env['pos.destroy.service'].search([('product_lot_id', '=', self.product_lot_id.id)])
            for x in destroy_obj:
                for y in x.payment_destroy_service_ids:
                    if y.journal_id.id == self.session_id.config_id.journal_deposit_id.id:
                        total_payment_destroy += y.amount
            for i in account_payment_obj:
                amount_payment += i.amount
            if abs(total_payment_destroy) > amount_payment:
                raise except_orm('Cảnh báo!', ("Số tiền đặt cọc không thể lớn hơn số tiền đã thanh toán"))
            if abs(debit_amount) > self.pos_order_id.invoice_id.residual:
                raise except_orm('Cảnh báo!', ("Số tiền ghi nợ không thể nhiều hơn số tiền còn lại trong hóa đơn"))

        else:
            total = 0
            for x in self.payment_destroy_service_ids:
                if x.journal_id.id == self.session_id.config_id.journal_debt_id.id:
                    total += x.amount
            if total != 0 :
                raise except_orm('Cảnh báo', ("Đơn hàng không còn công nợ vui lòng chuyển hết thanh toán sang tiền đặt cọc"))



    @api.multi
    def action_confirm(self):
        if self.state != 'wait_confirm':
            raise except_orm('Cảnh báo!', ('Trạng thái đơn hủy đã thay đổi. Vui lòng kiểm tra lại!'))
        # SangsLA thêm ngày 3/10/2018 Thêm using_service vào form khi chung của khách hàng
        pos_sum_digital_obj = self.env['pos.sum.digital.sign'].search(
            [('partner_id', '=', self.partner_id.id), ('state', '=', 'draft'), ('session_id', '=', self.session_id.id)])
        if pos_sum_digital_obj:
            self.update({'x_digital_sign_id': pos_sum_digital_obj.id})
        else:
            pos_sum_digital_id = self.env['pos.sum.digital.sign'].create({
                'partner_id': self.partner_id.id,
                'state': 'draft',
                'date': my_date.today(),
                'session_id': self.session_id.id,
            })
            self.update({'x_digital_sign_id': pos_sum_digital_id.id})
        #         hết
        self.state = 'wait_signature'

    @api.multi
    def action_back(self):
        if self.state != 'wait_confirm':
            raise except_orm('Cảnh báo!', ('Trạng thái đơn hủy đã thay đổi. Vui lòng kiểm tra lại!'))
        self.state = 'draft'

    @api.multi
    def action_signature(self):
        if self.state != 'wait_signature':
            raise except_orm('Cảnh báo!', ('Trạng thái đơn hủy đã thay đổi. Vui lòng kiểm tra lại!'))
        view = self.env.ref('pos_destroy_service.pos_destroy_service_view_pop_up')
        return {
            'name': _('Destroy Signature?'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'pos.destroy.service',
            'views': [(view.id, 'form')],
            'view_id': view.id,
            'target': 'new',
            'res_id': self.id,
            'context': self.env.context,
        }

    @api.multi
    def process_destroy_service(self):
        if self.signature_image == False:
            raise except_orm("Cảnh báo!", ("Bạn phải ký trước khi hoàn thành!"))
        self.update({'state': 'signature'})
        return {'type': 'ir.actions.act_window_close'}

    @api.multi
    def cancel(self):
        self.signature_image = ''
        return {'type': 'ir.actions.act_window_close'}

    @api.multi
    def action_done(self):
        if self.state == 'done':
            raise except_orm("Cảnh báo", ("Đơn hủy dịch vụ đã được hoàn thành. Vui lòng kiểm tra lại"))
        self.state = 'done'
        for line in self.destroy_service_detail_lines:
            for tmp in self.product_lot_id.x_card_detail_ids:
                if tmp.product_id.id == line.service_id.id:
                    if line.quantity < 0 :
                        if tmp.total_qty == -line.quantity:
                            tmp.state = 'cancel'
                            tmp.total_qty += line.quantity
                            tmp.amount_total += line.price_subtotal_incl
                            a = tmp.remain_amount + line.price_subtotal_incl
                            if a >= 0:
                                tmp.remain_amount += line.price_subtotal_incl
                            else:
                                tmp.remain_amount = 0
                        else:
                            tmp.total_qty += line.quantity
                            tmp.amount_total += line.price_subtotal_incl
                            a = tmp.remain_amount + line.price_subtotal_incl
                            if a >= 0:
                                tmp.remain_amount += line.price_subtotal_incl
                            else:
                                tmp.remain_amount = 0
        for x in self.product_lot_id.x_card_detail_ids:
            if x.state == 'cancel':
                for line in self.destroy_service_detail_lines:
                    if x.product_id.id == line.service_id.id:
                        if line.quantity < 0:
                                x.total_qty -= line.quantity
        for line in self.destroy_service_detail_lines:
            for tmp in self.pos_order_id.lines:
                if tmp.product_id.id == line.service_id.id and tmp.discount != 100:
                    tmp.update({'x_quantity_refund': -line.quantity})
                if tmp.product_id.id == line.service_id.id and tmp.discount == 100 and line.discount == 100:
                    tmp.update({'x_quantity_refund': -line.quantity})
        # Tạo pos_order cho đơn hủy
        if self.amount_total != 0:
            pos_order_obj = self.env['pos.order']
            argvs = {
                'session_id': self.session_id.id,
                'partner_id': self.partner_id.id,
                'x_rank_id': self.partner_id.x_rank.id,
                'user_id': self.pos_order_id.user_id.id,
                'pricelist_id': self.partner_id.property_product_pricelist.id,
                'date_order': self.date,
                'x_type': '4'
            }
            pos_order_id = pos_order_obj.create(argvs)
            self.new_order_id = pos_order_id.id
            # self.new_order_id.action_order_complete()
            # self.new_order_id.write({'state': 'paid'})
            pos_order_line_obj = self.env['pos.order.line']
            total_fee = 0
            for line in self.destroy_service_detail_lines:
                total_fee += line.change_fee
                argvs = {
                    'product_id': line.service_id.id,
                    'qty': line.quantity,
                    'price_unit': line.price_unit,
                    'discount': line.discount,
                    'x_discount': line.x_discount,
                    'price_subtotal': line.subtotal_wo_discount,
                    'price_subtotal_incl': line.price_subtotal_incl,
                    'order_id': pos_order_id.id,
                    'x_is_gift': False,
                }
                pos_order_line_obj.create(argvs)
            # Đẩy thêm 1 dòng là phí đổi dịch vụ vào đơn hàng
            argvs1 = {
                'product_id': self.session_id.config_id.x_charge_refund_id.id,
                'qty': 1,
                'price_unit': total_fee,
                'discount': 0,
                'x_discount': 0,
                'price_subtotal': total_fee,
                'price_subtotal_incl': total_fee,
                'order_id': pos_order_id.id,
                'x_is_gift': False,
            }
            pos_order_line_obj.create(argvs1)
            amount_residual = self.pos_order_id.invoice_id.residual
            debit_amount = 0
            deposit_amount = 0
            for line in self.payment_destroy_service_ids:
                if line.journal_id.id == self.session_id.config_id.journal_deposit_id.id:
                    deposit_amount += line.amount
                if line.journal_id.id == self.session_id.config_id.journal_debt_id.id:
                    debit_amount += line.amount
            # Nếu không còn ghi nợ trong đơn hàng ban đầu
            if debit_amount == 0 and deposit_amount != 0:
        #        Tạo bank statemant line cho đặt cọc
                x_lot_id = None
                statement_id = False
                for statement in self.session_id.statement_ids:
                    if statement.id == statement_id:
                        journal_id = statement.journal_id.id
                        break
                    elif statement.journal_id.id == self.session_id.config_id.journal_deposit_id.id:
                        statement_id = statement.id
                        break
                if not statement_id:
                    raise UserError(_('You have to open at least one cashbox.'))
                company_cxt = dict(self.env.context, force_company=self.session_id.config_id.journal_deposit_id.company_id.id)
                account_def = self.env['ir.property'].with_context(company_cxt).get('property_account_receivable_id',
                                                                                    'res.partner')
                account_id = (self.partner_id.property_account_receivable_id.id) or (
                        account_def and account_def.id) or False
                argvs = {
                    'ref': self.session_id.name,
                    'name': self.name,
                    'partner_id': self.partner_id.id,
                    'amount': deposit_amount,
                    'account_id': account_id,
                    'statement_id': statement_id,
                    'pos_statement_id': self.new_order_id.id,
                    'journal_id': self.session_id.config_id.journal_deposit_id.id,
                    'date': self.date,
                    'x_vc_id': x_lot_id
                }
                pos_make_payment_id = self.env['account.bank.statement.line'].create(argvs)
                # Dẩy ra tiền đặt cọc
                deposit_lines = self.env['pos.customer.deposit'].search(
                    [('partner_id', '=', self.partner_id.id)])
                if not deposit_lines:
                    Master = self.env['pos.customer.deposit']
                    vals = {
                        'name': self.partner_id.name,
                        'partner_id': self.partner_id.id,
                        'journal_id': self.session_id.config_id.journal_deposit_id.id,
                    }
                    deposit_lines = Master.create(vals)
                argvs = {
                    'journal_id': self.session_id.config_id.journal_deposit_id.id,
                    'date': self.date,
                    'amount': -deposit_amount,
                    # 'order_id': self.id,
                    'deposit_id': deposit_lines[0].id,
                    'type': 'deposit',
                    'partner_id': self.partner_id.id,
                    'session_id': self.session_id.id
                }
                deposit_id = self.env['pos.customer.deposit.line'].create(argvs)
                deposit_id.update({'state': 'done'})
                # Trừ doanh thu và trừ điểm tích lũy của khách hàng (2018)
                # 1/2019 Sang la comment lại do đặt cọc không trừ doanh thu
                # if deposit_amount < 0:
                #     revenue = self.env['crm.vip.customer.revenue'].create({
                #         'order_id': self.new_order_id.id,
                #         'journal_id': self.session_id.config_id.journal_deposit_id.id,
                #         'partner_id': self.partner_id.id,
                #         'amount': deposit_amount,
                #         'date': my_date.today(),
                #     })
                #     point_history = self.env['izi.vip.point.history'].create({
                #         'partner_id': self.partner_id.id,
                #         'order_id': self.new_order_id.id,
                #         'date': my_date.today(),
                #         'point': self._get_loyal_total(deposit_amount),
                #     })
                #     self.partner_id.update({'x_loyal_total': self.partner_id.x_loyal_total + deposit_amount,
                #                             'x_point_total': self.partner_id.x_point_total + self._get_loyal_total(deposit_amount)})
                #     # self.x_loyal_total = self.partner_id.x_loyal_total
                #     self.new_order_id.x_point_total = self.partner_id.x_point_total
                #     self.new_order_id.x_point_bonus =  self._get_loyal_total(deposit_amount)
                #     self.new_order_id.update({'x_total_order': deposit_amount})
                #     self.new_order_id.update({'x_loyal_total': self.partner_id.x_loyal_total})
                deposit_lines.update({'amount_total': -deposit_amount,
                                      'residual': -deposit_amount})
            # Nếu còn nợ tiền trong đơn hàng bán thẻ dịch vụ
            else:
    #           Số tiền nợ nhiều hơn số tiền mà khách hàng refund => Tạo bank statemant line với tất cả đều là nợ
                if deposit_amount == 0 and debit_amount !=0:
                    x_lot_id = None
                    statement_id = False
                    for statement in self.session_id.statement_ids:
                        if statement.id == statement_id:
                            journal_id = statement.journal_id.id
                            break
                        elif statement.journal_id.id == self.session_id.config_id.journal_debt_id.id:
                            statement_id = statement.id
                            break
                    if not statement_id:
                        raise UserError(_('You have to open at least one cashbox.'))
                    company_cxt = dict(self.env.context, force_company=self.session_id.config_id.journal_debt_id.company_id.id)
                    account_def = self.env['ir.property'].with_context(company_cxt).get('property_account_receivable_id',
                                                                                        'res.partner')
                    account_id = (self.partner_id.property_account_receivable_id.id) or (
                            account_def and account_def.id) or False
                    argvs = {
                        'ref': self.session_id.name,
                        'name': self.name,
                        'partner_id': self.partner_id.id,
                        'amount': debit_amount,
                        'account_id': account_id,
                        'statement_id': statement_id,
                        'pos_statement_id': self.new_order_id.id,
                        'journal_id': self.session_id.config_id.journal_debt_id.id,
                        'date': self.date,
                        'x_vc_id': x_lot_id,
                        'x_ignore_reconcile': True
                    }
                    pos_make_payment_id = self.env['account.bank.statement.line'].create(argvs)
    #           Số tiền trong hóa đơn nợ ít hơn số tiền khách hàng refund
                else:
                    # Tạo bank_statement với số tiền nợ của khách hàng
                    x_lot_id = None
                    statement_id = False
                    for statement in self.session_id.statement_ids:
                        if statement.id == statement_id:
                            journal_id = statement.journal_id.id
                            break
                        elif statement.journal_id.id == self.session_id.config_id.journal_debt_id.id:
                            statement_id = statement.id
                            break
                    if not statement_id:
                        raise UserError(_('You have to open at least one cashbox.'))
                    company_cxt = dict(self.env.context, force_company=self.session_id.config_id.journal_debt_id.company_id.id)
                    account_def = self.env['ir.property'].with_context(company_cxt).get('property_account_receivable_id',
                                                                                        'res.partner')
                    account_id = (self.partner_id.property_account_receivable_id.id) or (
                            account_def and account_def.id) or False
                    argvs = {
                        'ref': self.session_id.name,
                        'name': self.name,
                        'partner_id': self.partner_id.id,
                        'amount': debit_amount,
                        'account_id': account_id,
                        'statement_id': statement_id,
                        'pos_statement_id': self.new_order_id.id,
                        'journal_id': self.session_id.config_id.journal_debt_id.id,
                        'date': self.date,
                        'x_vc_id': x_lot_id,
                        'x_ignore_reconcile': True
                    }
                    pos_make_payment_id = self.env['account.bank.statement.line'].create(argvs)
    #               Tạo bank_statement_line với số tiền mà khách hàng được trả lại đưa hết ra tiền đặt cọc
                    x_lot_id = None
                    statement_id = False
                    for statement in self.session_id.statement_ids:
                        if statement.id == statement_id:
                            journal_id = statement.journal_id.id
                            break
                        elif statement.journal_id.id == self.session_id.config_id.journal_deposit_id.id:
                            statement_id = statement.id
                            break
                    if not statement_id:
                        raise UserError(_('You have to open at least one cashbox.'))
                    company_cxt = dict(self.env.context,
                                       force_company=self.session_id.config_id.journal_deposit_id.company_id.id)
                    account_def = self.env['ir.property'].with_context(company_cxt).get('property_account_receivable_id',
                                                                                        'res.partner')
                    account_id = (self.partner_id.property_account_receivable_id.id) or (
                            account_def and account_def.id) or False
                    argvs = {
                        'ref': self.session_id.name,
                        'name': self.name,
                        'partner_id': self.partner_id.id,
                        'amount': deposit_amount,
                        'account_id': account_id,
                        'statement_id': statement_id,
                        'pos_statement_id': self.new_order_id.id,
                        'journal_id': self.session_id.config_id.journal_deposit_id.id,
                        'date': self.date,
                        'x_vc_id': x_lot_id,
                        'x_ignore_reconcile': True
                    }
                    pos_make_payment_id = self.env['account.bank.statement.line'].create(argvs)
                    # Dẩy ra tiền đặt cọc
                    deposit_lines = self.env['pos.customer.deposit'].search(
                        [('partner_id', '=', self.partner_id.id)])
                    if not deposit_lines:
                        Master = self.env['pos.customer.deposit']
                        vals = {
                            'name': self.partner_id.name,
                            'partner_id': self.partner_id.id,
                            'journal_id': self.session_id.config_id.journal_deposit_id.id,
                        }
                        deposit_lines = Master.create(vals)
                    argvs = {
                        'journal_id': self.session_id.config_id.journal_deposit_id.id,
                        'date': self.date,
                        'amount': -(deposit_amount),
                        # 'order_id': self.id,
                        'deposit_id': deposit_lines[0].id,
                        'type': 'deposit',
                        'partner_id': self.partner_id.id,
                        'session_id': self.session_id.id
                    }
                    deposit_id = self.env['pos.customer.deposit.line'].create(argvs)
                    deposit_id.update({'state': 'done'})
                    # Trừ doanh thu và trừ điểm tích lũy của khách hàng (2018)
                    # 1/2019 sáng la coment lại do đặt cọc không trừ doanh thu
                    # if deposit_amount < 0:
                    #     revenue = self.env['crm.vip.customer.revenue'].create({
                    #         'order_id': self.new_order_id.id,
                    #         'journal_id': self.session_id.config_id.journal_deposit_id.id,
                    #         'partner_id': self.partner_id.id,
                    #         'amount': (deposit_amount),
                    #         'date': my_date.today(),
                    #     })
                    #     point_history = self.env['izi.vip.point.history'].create({
                    #         'partner_id': self.partner_id.id,
                    #         'order_id': self.new_order_id.id,
                    #         'date': my_date.today(),
                    #         'point': self._get_loyal_total((deposit_amount)),
                    #     })
                    #     self.partner_id.update({'x_loyal_total': self.partner_id.x_loyal_total + (deposit_amount),
                    #                             'x_point_total': self.partner_id.x_point_total + self._get_loyal_total(
                    #                                 (deposit_amount))})
                    #     # self.x_loyal_total = self.partner_id.x_loyal_total
                    #     self.new_order_id.x_point_total = self.partner_id.x_point_total
                    #     self.new_order_id.x_point_bonus = self._get_loyal_total((deposit_amount))
                    #     self.new_order_id.update({'x_total_order': (deposit_amount)})
                    #     self.new_order_id.update({'x_loyal_total': self.partner_id.x_loyal_total})
                    deposit_lines.update({'amount_total': -deposit_amount,
                                          'residual': -deposit_amount})
            # Tạo hóa đơn và reconcile chúng với nhau để giảm công nợ của khách hàng
            # Tạo hóa đơn
            invoice_obj = self.env['account.invoice']
            payment_obj = self.env['account.payment']
            journal_debt_id = self.new_order_id.config_id.journal_debt_id.id if self.new_order_id.config_id.journal_debt_id else False
            for order in self.new_order_id:
                total = 0.0  # Tổng đơn hàng
                residual = 0.0  # Số còn nợ
                paid_statements = []
                for statement in order.statement_ids:
                    total += statement.amount
                    if statement.journal_id.id == journal_debt_id:
                        residual += statement.amount
                    else:
                        paid_statements.append(statement)
                # Tạo hoá đơn các đơn hàng nợ
                local_context = dict(self.new_order_id.env.context, force_company=order.company_id.id,
                                     company_id=order.company_id.id)
                if 1==1:
                    invoice = invoice_obj.new(order._prepare_invoice())
                    invoice._onchange_partner_id()
                    invoice.fiscal_position_id = order.fiscal_position_id
                    inv = invoice._convert_to_write({name: invoice[name] for name in invoice._cache})
                    new_invoice = invoice_obj.with_context(local_context).sudo().create(inv)

                    message = _(
                        "This invoice has been created from the point of sale session: <a href=# data-oe-model=pos.order data-oe-id=%d>%s</a>") % (
                                  order.id, order.name)
                    new_invoice.message_post(body=message)
                    discount_total = 0.0
                    for line in order.lines:
                        order.with_context(local_context)._action_create_invoice_line(line, new_invoice.id)
                        price_per_product = line.price_unit
                        if line.x_discount:
                            price_per_product = (line.x_subtotal_wo_discount - line.x_discount) / line.qty
                        if line.discount:
                            price_per_product -= round(price_per_product * line.discount / 100.0)
                        if price_per_product != line.price_unit:
                            discount_total += (line.price_unit - price_per_product) * line.qty
                        # Thêm dòng chiết khấu tổng hoá đơn
                    if discount_total != 0.0:
                        InvoiceLine = self.env['account.invoice.line']
                        discount_product = self.env['product.product'].search([('default_code', '=', 'DISCOUNT')],
                                                                              limit=1)
                        if not discount_product:
                            raise MissingError("Chưa thiết lập sản phẩm chiết khấu đơn hàng.")
                        inv_name = discount_product.name
                        inv_line = {
                            'invoice_id': new_invoice.id,
                            'product_id': discount_product.id,
                            'quantity': 1,
                            'discount': 0.0,
                            'price_unit': discount_total,
                            'account_id': self.env['account.account'].search([('code', '=', '5211')], limit=1).id,
                            'name': inv_name,
                        }
                        invoice_line = InvoiceLine.sudo().new(inv_line)
                        inv_line = invoice_line._convert_to_write(
                            {name: invoice_line[name] for name in invoice_line._cache})
                        inv_line.update(price_unit=discount_total, discount=0.0, name=inv_name)
                        InvoiceLine.sudo().create(inv_line)
                    new_invoice.with_context(local_context).sudo().compute_taxes()
                    new_invoice.action_invoice_open()
                    self.new_order_id.invoice_id = new_invoice.id
                    new_invoice.x_pos_order_id = self.new_order_id.id
            # self.new_order_id.create_invoice()
            # Tạo thanh toán hóa đơn trước khi reconsilr
            self.new_order_id.state = 'invoiced'
            if self.new_order_id.invoice_id:
                self.new_order_id.state = 'invoiced'
                for line in self.new_order_id.statement_ids:
                    payment_methods = line.journal_id.inbound_payment_method_ids
                    payment_method_id = payment_methods and payment_methods[0] or False
                    journal_debt_id = self.new_order_id.config_id.journal_debt_id.id if self.new_order_id.config_id.journal_debt_id else False
                    if line.journal_id.id == journal_debt_id:
                        continue
                    argvas = {
                        'amount': abs(line.amount),
                        'journal_id': line.journal_id.id,
                        'payment_date': line.date,
                        'communication': line.name,
                        'payment_method_id': payment_method_id.id,
                        'payment_type': 'outbound',
                        'invoice_ids': [(6, 0, self.new_order_id.invoice_id.ids)],
                        'partner_type': 'customer',
                        'partner_id': self.new_order_id.partner_id.id,
                    }
                    account_payment = self.env['account.payment'].create(argvas)
                    account_payment.with_context(izi_partner_debt=True).action_validate_invoice_payment()
            # Hàm reconcile move trong hóa đơn.
            if self.new_order_id.invoice_id:
                if self.pos_order_id.invoice_id.residual > 0:
                    for inv in self.pos_order_id.invoice_id:
                        movelines = inv.move_id.line_ids
                        to_reconcile_ids = {}
                        to_reconcile_lines = self.env['account.move.line']
                        for line in movelines:
                            if line.account_id.id == inv.account_id.id:
                                to_reconcile_lines += line
                                to_reconcile_ids.setdefault(line.account_id.id, []).append(line.id)
                            if line.reconciled:
                                line.remove_move_reconcile()
                        # invoice_id.action_invoice_open()
                        for tmpline in self.new_order_id.invoice_id.move_id.line_ids:
                            if tmpline.account_id.id == inv.account_id.id:
                                to_reconcile_lines += tmpline
                        to_reconcile_lines.filtered(lambda l: l.reconciled == False).reconcile()
        # if self.new_order_id.invoice_id:
        #     for line in self.new_order_id.statement_ids:
        #         payment_methods = line.journal_id.inbound_payment_method_ids
        #         payment_method_id = payment_methods and payment_methods[0] or False
        #         journal_debt_id = self.new_order_id.config_id.journal_debt_id.id if self.new_order_id.config_id.journal_debt_id else False
        #         if line.journal_id.id == journal_debt_id:
        #             continue
        #         argvas = {
        #             'amount': abs(line.amount),
        #             'journal_id': line.journal_id.id,
        #             'payment_date': line.date,
        #             'communication': line.name,
        #             'payment_method_id': payment_method_id.id,
        #             'payment_type': 'outbound',
        #             'invoice_ids': [(6, 0, self.new_order_id.invoice_id.ids)],
        #             'partner_type': 'customer',
        #             'partner_id': self.new_order_id.partner_id.id,
        #         }
        #         account_payment = self.env['account.payment'].create(argvas)
        #         account_payment.with_context(izi_partner_debt=True).action_validate_invoice_payment()

    # @api.multi
    # def _get_loyal_total(self, loyal_total):
    #     config_id = self.new_order_id.session_id.config_id.id
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