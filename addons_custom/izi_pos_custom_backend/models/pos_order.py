# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError, except_orm, MissingError, ValidationError
from datetime import datetime, timedelta, date as my_date
from dateutil.relativedelta import relativedelta
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT
import logging

_logger = logging.getLogger(__name__)


class PosOrderLine(models.Model):
    _inherit = 'pos.order.line'

    @api.multi
    @api.onchange('product_id', 'qty')
    def _compute_subtotal_wo_discount(self):
        for r in self:
            r.x_subtotal_wo_discount = r.qty * r.price_unit

    x_is_gift = fields.Boolean('Is gift?', default=False)
    x_subtotal_wo_discount = fields.Float('Subtotal W/O discount', compute=_compute_subtotal_wo_discount, store=False)


class PosOrder(models.Model):
    _name = 'pos.order'
    _inherit = ['pos.order', 'mail.thread', 'mail.activity.mixin']

    @api.multi
    def _compute_x_amount_total(self):
        for order in self:
            total_wo_discount = 0.0
            total_vip_discount = 0.0
            total_promo_discount = 0.0
            for line in order.lines:
                if not line.x_is_gift:
                    total_wo_discount += line.price_unit * line.qty
                    total_promo_discount += line.x_discount
                    total_vip_discount += line.discount / 100.0 * (line.x_subtotal_wo_discount - line.x_discount)
            order.x_amount_total = total_wo_discount
            order.x_vip_discount = total_vip_discount
            order.x_discount_promo = total_promo_discount

    def _default_session(self):
        user_id = self.env['res.users'].search([('id', '=', self.env.uid)], limit=1)
        config_id = user_id.x_pos_config_id.id
        return self.env['pos.session'].search([('state', '=', 'opened'), ('config_id', '=', config_id)], limit=1)

    def _compute_is_promotion_tester(self):
        rec = None
        for r in self:
            if not rec or rec.id > r.id:
                rec = r
        self = rec
        tester_uids = self.env['ir.config_parameter'].sudo().get_param('pos.promo_tester_uid')
        try:
            tester_uids = eval(tester_uids)
        except:
            pass
        if (isinstance(tester_uids, list)) and self._uid in tester_uids:
            self.x_promotion_test = True
        else:
            self.x_promotion_test = False

    session_id = fields.Many2one(
        'pos.session', string='Session', required=True, index=True,
        domain="[('state', '=', 'opened')]", states={'draft': [('readonly', False)]},
        readonly=True, default=_default_session)

    x_type = fields.Selection(selection_add=[('3', 'Service'), ('4', 'Destroy Service')])
    x_lot_number = fields.Char("Lot number", copy=False)
    x_point_bonus = fields.Float("Point Bonus", copy=False)
    x_rank_id = fields.Many2one('crm.vip.rank', "Rank", copy=False)
    state = fields.Selection(
        [('draft', 'New'), ('to_confirm', 'To confirm'), ('to_payment', "To Payment"), ('to_approve', 'To approve'),
         ('customer_comment', "Customer Comment"),
         ('cancel', 'Cancelled'), ('paid', 'Paid'), ('done', 'Posted'), ('invoiced', 'Invoiced'), ('cancel', "Cancel")],
        'Status', readonly=True, copy=False, default='draft', track_visibility='onchange')
    x_vm_main_total = fields.Float('VM main total',
                                   readonly=True, copy=False)  # tổng số tiền đã dùng trong tài khoản chính thẻ tiền
    x_vm_sub_total = fields.Float('VM main total', readonly=True, copy=False)  # tổng số tiền đã dùng trong tài khoản phụ thẻ tiền
    x_loyal_id = fields.Many2one('crm.vip.customer.revenue', 'Revenue', readonly=True, copy=False)
    x_loyal_total = fields.Float('Loyal total', store=True, copy=False)
    x_point_total = fields.Float("Point total", store=True, copy=False)
    x_pos_partner_refund_id = fields.Many2one('pos.order', "POS Order Refund", copy=False)
    x_signature_image = fields.Binary('Signature Image', attachment=True, copy=False)
    x_debt = fields.Float('Debt', compute='_compute_debt', store=True, copy=False)
    x_total_order = fields.Float('Total Order', copy=False)
    x_amount_debt = fields.Float('Amount Debt', compute='compute_amount_debt', store=False, copy=False)
    x_amount_payment = fields.Float("Amount Payment", compute='compute_amount_debt', store=False, copy=False)

    x_vip_discount = fields.Float('VIP discount', compute='_compute_x_amount_total', store=False, copy=False)
    x_amount_total = fields.Float('Total W/O discount', compute='_compute_x_amount_total', store=False, copy=False)
    # nguoi so huu
    x_owner_id = fields.Many2one('res.partner', string='Owner', copy=False)
    x_discount_computed = fields.Boolean(' Discount Compute ', default=False, copy=False)
    # x_custom_discount = fields.Boolean('Custom discount', default=False, copy=False)
    x_promotion_test = fields.Boolean('Promotion tester', store=False, compute=_compute_is_promotion_tester, readonly=True, copy=False)
    x_active_pick = fields.Boolean('Active Pick',default=False, copy=False)
    # Sangla them ngay 23/7/19 so tien con nơ va so tien thanh toan tren tree view
    x_amount_residual = fields.Float('Amount Residual', compute='compute_amount_residual', store=False, copy=False)
    x_amount_invoice_payment = fields.Float('Amount Invoice Payment', compute='compute_amount_residual', store=False, copy=False)
    x_cashier_id = fields.Many2one('res.users', "Cashier")
    x_price_warning = fields.Char("Warning", compute='compute_warning_price')
    _sql_constraints = [
        ('name_uniq', 'unique(name)', 'Name pos_order is unique')
    ]

    @api.depends('lines')
    def compute_warning_price(self):
        record = None
        for r in self:
            if not record or r.id > record.id:
                record = r
        st = []
        st.append('Đơn hàng của bạn sẽ cần PHÊ DUYỆT do có dịch ')
        count = 0
        for line in record.lines:
            price = record.pricelist_id.get_product_price(line.product_id, line.qty or 1.0, record.partner_id)
            if line.price_unit < price and line.x_custom_discount == False:
                count += 1
                st.append('%s' % (line.product_id.default_code))
                # st.append('Giá niêm yết %r ' % self.convert_numbers_to_text_sangla(price))
                # st.append('Giá bán %r ' % self.convert_numbers_to_text_sangla(line.price_unit))
                # st.append('Dưới mức giá bán tối thiểu cần phê duyêt. ')
            if line.discount > 0 and line.price_unit * (
                    100 - line.discount) / 100 < price and line.x_custom_discount == False:
                count += 1
                st.append(', ')
                st.append('%s' % (line.product_id.default_code))
                # st.append('Giá niêm yết %r ' % self.convert_numbers_to_text_sangla(price))
                # st.append('Nhập chiết khấu %r phần trăm ' % self.convert_numbers_to_text_sangla(line.discount))
                # st.append(
                #     'Giá bán %r ' % self.convert_numbers_to_text_sangla(line.price_unit * (100 - line.discount) / 100))
                # st.append('Dưới mức giá bán tối thiểu cần phê duyêt.')
            if line.x_discount > 0 and line.price_unit * line.qty - line.x_discount < price and line.x_custom_discount == False:
                count += 1
                st.append(', ')
                st.append('%s' % (line.product_id.default_code))
                # st.append('Tổng giá niêm yết %r ' % self.convert_numbers_to_text_sangla(price * line.qty))
                # st.append('Nhập giảm giá  %r tiền' % self.convert_numbers_to_text_sangla(line.x_discount))
                # st.append(
                #     'Giá bán %r ' % self.convert_numbers_to_text_sangla(line.price_unit * line.qty - line.x_discount))
                # st.append('Dưới mức giá bán tối thiểu cần phê duyêt. ')
        st.append(' dưới mức giá bán tối thiểu. Bạn có thể chọn lại bảng giá hoặc sửa lại giá để đơn hàng được hợp lệ.')
        if count > 0:
            record.x_price_warning = st

    @api.depends('invoice_id')
    def compute_amount_residual(self):
        for r in self:
            if r.invoice_id:
                r.x_amount_residual = r.invoice_id.residual
                r.x_amount_invoice_payment = r.amount_total - r.invoice_id.residual

    @api.depends('statement_ids')
    def compute_amount_debt(self):
        record = None
        for r in self:
            if not record or r.id > record.id:
                record = r
        #  tính toán số tiền ghi nợ cửa khách hàng
        money = 0
        journal_debt_id = record.config_id.journal_debt_id.id if record.config_id.journal_debt_id else False
        if journal_debt_id:
            for statement in record.statement_ids:
                if statement.journal_id.id == journal_debt_id:
                    money += statement.amount
        record.x_amount_debt = money
        record.x_amount_payment = record.amount_total - money

    @api.onchange('partner_id')
    def _onchange_x_loyal_total(self):
        if self.partner_id:
            self.x_loyal_total = self.partner_id.x_loyal_total

    @api.depends('statement_ids.journal_id')
    def _compute_debt(self):
        journal_debt_id = self.config_id.journal_debt_id.id if self.config_id.journal_debt_id else False
        for line in self:
            for tmp in line.statement_ids:
                if tmp.journal_id.id == journal_debt_id:
                    line.x_debt += tmp.amount

    @api.multi
    def unlink(self):
        for line in self:
            if line.state != 'draft':
                raise except_orm("Cảnh báo!", ("Bạn không thể xóa khi trạng thái khác tạo mới"))
            if line.state == 'draft' and line.statement_ids:
                raise except_orm("Cảnh báo!", ("Bạn không thể xóa khi đã có thanh toán"))
            # if line.x_type == '3':
            #     raise except_orm("Cảnh báo!", ("Đây là đơn hàng của sử dụng dịch vụ lẻ. Bạn không thể xóa"))
        return super(PosOrder, self).unlink()

    @api.multi
    def action_compute_order_discount(self):
        self.ensure_one()
        if self.lines:
            # Lấy thông tin các sản phẩm được giảm giá ngoại lệ theo hạng VIP của KH
            except_dict = {}
            for product in self.partner_id.x_rank.except_product_ids:
                except_dict[product.product_id.id] = product.discount
                except_dict['%s_amount' % product.product_id.id] = product.max_amount
            discount_service = self.partner_id.x_rank.discount_service
            discount_product = self.partner_id.x_rank.discount_product
            discount_except = len(self.partner_id.x_rank.except_product_ids)

            for line in self.lines:
                if line.x_is_gift or line.product_id.x_type_card != 'none':
                    continue
                if line.product_id.default_code:
                    if line.product_id.default_code.upper() == 'PDDV':
                        break
                    # elif line.product_id.default_code.upper() == 'COIN':
                    #     continue
                # Sản phẩm thuộc ngoại lệ
                if discount_except and line.product_id.id in except_dict:
                    key = '%s_amount' % line.product_id.id
                    x_discount = except_dict[line.product_id.id] * (line.price_subtotal_incl - line.x_discount) / 100.0
                    if key in except_dict:
                        # Kiểm tra giới hạn số tiền tối đa
                        max_amount = except_dict[key]
                        if max_amount and max_amount < x_discount:
                            x_discount = max_amount
                    # Qui đổi số tiền ra phần trăm
                    line.discount = round(x_discount * 100.0 / (line.x_subtotal_wo_discount - line.x_discount), 0)
                # Dịch vụ
                elif discount_service > 0 and line.product_id.type == 'service':
                    line.discount += discount_service
                # Sản phẩm
                elif discount_product > 0 and line.product_id.type == 'product':
                    line.discount += discount_product

    @api.onchange('lines')
    def onchange_order_lines(self):
        self._compute_x_amount_total()
        if not self.x_pos_partner_refund_id:
            self.x_discount_computed = False
    #     self.x_custom_discount = False

    @api.onchange('partner_id')
    def onchange_partner(self):
        partner_id = self.env['res.partner'].search([('id', '=', self.partner_id.id)])
        self.x_rank_id = partner_id.x_rank.id

    @api.model
    def default_get(self, fields):
        res = super(PosOrder, self).default_get(fields)
        if not self._context.get('inventory_update', False):
            current_session = self.env['pos.session'].search(
                [('state', '!=', 'closed'), ('config_id', '=', self.env.user.x_pos_config_id.id)], limit=1)
            if not current_session:
                raise except_orm(("Cảnh báo!"), ('Bạn phải mở phiên trước khi tạo đơn hàng mới.'))
        return res

    @api.multi
    def action_search_lot_number(self):
        PosOrderLine = self.env['pos.order.line']
        lot_list = self.x_lot_number.split(',')
        for str_lot in lot_list:
            lot_obj = self.env['stock.production.lot'].search([('name', '=', str_lot.upper().strip())])
            product_obj = lot_obj.product_id.product_tmpl_id
            if len(lot_obj) == 0:
                raise except_orm('Cảnh báo!', ('Mã "%s" không tồn tại trong hệ thống!' % str_lot.upper().strip()))
            else:
                if lot_obj.x_status == 'new':
                    raise except_orm('Cảnh báo!', ('Mã "%s" chưa được kích hoạt!' % str_lot.upper().strip()))
                elif lot_obj.x_status == 'using':
                    raise except_orm('Cảnh báo!', ('Mã "%s" đã bán và đang được sử dụng!' % str_lot.upper().strip()))
                elif lot_obj.x_status == 'used':
                    raise except_orm('Cảnh báo!', ('Mã "%s" đã sử dụng xong!' % str_lot.upper().strip()))
                elif lot_obj.x_status == 'destroy':
                    raise except_orm('Cảnh báo!', ('Mã "%s" đã bị hủy!' % str_lot.upper().strip()))
                else:
                    if lot_obj.life_date and datetime.strptime(lot_obj.life_date, '%Y-%m-%d %H:%M:%S') + timedelta(
                            days=1) <= datetime.strptime(self.date_order, '%Y-%m-%d %H:%M:%S'):
                        raise except_orm('Cảnh báo!', (('Mã "%s" hết hạn vào ngày: ' + datetime.strptime(
                            lot_obj.life_date, "%Y-%m-%d %H:%M:%S").strftime("%d-%m-%Y")) % str_lot.upper().strip()))
                    else:
                        argvs = {
                            'product_id': lot_obj.product_id.id,
                            'name': self.name,
                            'price_unit': product_obj.list_price,
                            'qty': 1,
                            'x_qty': 1,
                            'discount': 0,
                            'price_subtotal': product_obj.list_price,
                            'lot_name': str_lot.upper().strip(),
                            'order_id': self.id,
                        }
                        check_lot = PosOrderLine.search([('lot_name', '=', str_lot.upper().strip())])
                        if len(check_lot) != 0:
                            raise except_orm('Cảnh báo!', (('Mã %s đang được gắn ở đơn hàng: ' + str(
                                check_lot[0].order_id.name)) % str_lot.upper().strip()))
                        line_id = PosOrderLine.create(argvs)
                        argvs_lot = {
                            'pos_order_line_id': line_id.id,
                            'lot_name': str_lot.upper().strip(),
                        }
                        pos_lot_id = self.env['pos.pack.operation.lot'].create(argvs_lot)
        self.x_lot_number = ''

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
                    if (tmp.product_id.product_tmpl_id.x_type_card == 'tdv' or tmp.product_id.product_tmpl_id.x_type_card == 'tdt'):
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

        super(PosOrder, self.with_context(xxx=True)).action_pos_order_paid()
        if not self.x_pos_partner_refund_id:
            self.write({'state': 'customer_comment'})
            # SangsLA thêm ngày 3/10/2018 Thêm order vào form khi chung của khách hàng
            pos_sum_digital_obj = self.env['pos.sum.digital.sign'].search(
                [('partner_id', '=', self.partner_id.id), ('state', '=', 'draft'),
                 ('session_id', '=', self.session_id.id)])
            if pos_sum_digital_obj:
                self.update({'x_digital_sign_id': pos_sum_digital_obj.id})
            else:
                pos_sum_digital_obj = self.env['pos.sum.digital.sign'].create({
                    'partner_id': self.partner_id.id,
                    'state': 'draft',
                    'date': my_date.today(),
                    'session_id': self.session_id.id
                })
                self.update({'x_digital_sign_id': pos_sum_digital_obj.id})
            for line in self.lines:
                line.update({'x_digital_sign_id': pos_sum_digital_obj.id})
            for line in self.statement_ids:
                line.update({'x_digital_sign_id': pos_sum_digital_obj.id})
        else:
            self.write({'state': 'draft'})

    @api.multi
    def action_order_complete(self):
        super(PosOrder, self).action_order_complete()
        self_to_update = {'state': 'customer_comment'}
        # Cập nhật thẻ dịch vụ
        param_obj = self.env['ir.config_parameter']
        code = param_obj.get_param('default_code_exception')
        if not code:
            raise ValidationError(
                _(u"Chưa thiết lập thông số hệ thống cho mã dịch vụ ngoại lệ. Xin hãy liên hệ với người quản trị."))
        amount_payment = 0
        journal_debt_id = self.config_id.journal_debt_id.id if self.config_id.journal_debt_id else False
        if journal_debt_id:
            # Tổng tiền ghi nợ
            debt_total = 0.0
            for statement in self.statement_ids:
                if statement.journal_id.id != journal_debt_id:
                    amount_payment += statement.amount
                else:
                    debt_total += statement.amount
            if debt_total > 0.0:
                self.partner_id.x_balance -= debt_total
        list = code.split(',')
        lot = self.env['stock.production.lot']
        lot_ids = []
        for line in self.lines:
            if line.product_id.product_tmpl_id.x_type_card == 'tdv':
                lot_obj = lot.search(
                    [('name', '=', line.pack_lot_ids.lot_name), ('product_id', '=', line.product_id.id)])
                lot_ids.append(lot_obj.id)
        if len(lot_ids) != 0:
            lot_obj = lot.search([('id', '=', lot_ids[0])])
            amount = 0
            amount_product = 0
            lines_lot = []
            for line in self.lines:
                if (line.product_id.product_tmpl_id.x_type_card != 'tdv') and (
                        line.product_id.product_tmpl_id.type != 'service'):
                    amount_product += (line.price_subtotal_incl - line.x_discount)
                if line.product_id.product_tmpl_id.x_type_card == 'tdv':
                    continue
                if line.product_id.product_tmpl_id.type != 'service':
                    continue
                if line.product_id.default_code in list:
                    continue

                argvs = {
                    'lot_id': lot_obj.id,
                    'product_id': line.product_id.id,
                    'total_qty': line.qty,
                    'qty_hand': line.qty,
                    'qty_use': 0,
                    'price_unit': line.price_unit,
                    'remain_amount': line.price_subtotal_incl,
                    'amount_total': line.price_subtotal_incl,
                    'state': 'ready'
                }
                k = 0
                for i in range(len(lines_lot)):
                    if lines_lot[i]['product_id'] == line.product_id.id:
                        k = k + 1
                        lines_lot[i]['total_qty'] = lines_lot[i]['total_qty'] + line.qty
                if k == 0:
                    lines_lot.append(argvs)
                amount = amount + line.price_subtotal_incl
            lot_obj.x_card_detail_ids = lines_lot
            if lot_obj.x_release_id.expired_type == '1':
                date = datetime.strptime(self.date_order, "%Y-%m-%d %H:%M:%S") + relativedelta(
                    months=lot_obj.x_release_id.validity)
                lot_obj.life_date = date.replace(minute=0, hour=0, second=0)
            lot_obj.x_customer_id = self.partner_id.id if not self.x_owner_id else self.x_owner_id.id
            lot_obj.x_status = 'using'
            lot_obj.x_amount = amount
            lot_obj.x_payment_amount = amount_payment - amount_product
            lot_obj.x_order_id = self.id
            # tang x_balancce trong res_partner tiennq 06/08
            if not self.x_owner_id:
                self.partner_id.x_balance = self.partner_id.x_balance + lot_obj.x_payment_amount
            else:
                self.x_owner_id.x_balance = self.partner_id.x_balance + lot_obj.x_payment_amount
        # bán voucher/coupon
        for line in self.lines:
            if line.product_id.product_tmpl_id.x_type_card == 'pmh':
                lot_obj = lot.search(
                    [('name', '=', line.pack_lot_ids.lot_name), ('product_id', '=', line.product_id.id)])
                if len(lot_obj) != 0:
                    if lot_obj.x_release_id.expired_type == '1':
                        date = datetime.strptime(self.date_order, "%Y-%m-%d %H:%M:%S") + relativedelta(
                            months=lot_obj.x_release_id.validity)
                        lot_obj.life_date = date.replace(minute=0, hour=0, second=0)
                    lot_obj.x_customer_id = self.partner_id.id if not self.x_owner_id else self.x_owner_id.id
                    lot_obj.x_status = 'using'

        # Mã các phương thức thanh toán có thể ghi nhận doanh thu
        journal_loyal_ids = self.config_id.journal_loyal_ids.ids if self.config_id.journal_loyal_ids else False
        # if journal_loyal_ids:
        #     loyal_total = 0.0
        #     #ngoan sửa lại ghi nhận doanh thu trên đơn hàng
        #     for stt in self.statement_ids:
        #         if stt.journal_id.id in journal_loyal_ids:
        #             if stt.amount > 0:
        #                 revenue = self.env['crm.vip.customer.revenue'].create({
        #                     'partner_id': self.partner_id.id,
        #                     'order_id': self.id,
        #                     'journal_id':stt.journal_id.id,
        #                     'amount': stt.amount,
        #                     'date': my_date.today(),
        #                 })
        #             loyal_total += stt.amount
        #     # Ghi nhận doanh thu
        #     if loyal_total > 0:
        #         self_to_update['x_total_order'] = loyal_total
        #         # tiennq them quy doi diem tich luy
        #         # point = self._get_loyal_total(loyal_total)
        #         ####
        #         self_to_update['x_loyal_id'] = revenue.id
        #         # self_to_update['x_point_bonus'] = point
        #         # self_to_update['x_point_total'] = point + self.partner_id.x_point_total
        #         self_to_update['x_loyal_total'] = loyal_total + self.partner_id.x_loyal_total
        #         # CuuNV Fix 09/07: Thêm tổng tích điểm cho KH
        #         self.partner_id.update({'x_loyal_total': self.partner_id.x_loyal_total + loyal_total})
        #         # SangLA 15/08/2018: Thêm điểm thưởng cho người giới thiệu khách hàng
        #         order_len = self.env['pos.order'].search([('partner_id', '=', self.partner_id.id)])
        #         # if len(order_len) == 1 and self.partner_id.x_presenter:
        #         #     self.partner_id.x_presenter.update(
        #         #         {'x_point_total': (point + self.partner_id.x_presenter.x_point_total)})
        #         #     point_history = self.env['izi.vip.point.history'].create({
        #         #         'partner_id': self.partner_id.x_presenter.id,
        #         #         'order_id': self.id,
        #         #         'date': my_date.today(),
        #         #         'point': point,
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
                            q +=1
                    if q ==0:
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
                                                                         'amount': remain, 'statement_id': stt.id}
                        # Cập nhật tăng số tiền đã dùng = số tiền còn lại cần thanh toán
                        line.update({'money_used': line.money_used + remain})
                        remain = 0
                    return remain, amount

                # Thực hiện trừ cho đến khi đủ số tiền muốn thanh toán
                # Sáng la sửa lại ngùa 23/04/2019. Nếu chỉ có tiền khuyến thì trừ tiền khuyến mại. Nếu có cả 2 thì trừ như tài khoản ban đầu
                if len(vm_lines_pay) >0:
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
                    raise UserError("Tài khoản đặt cọc của khách hàng không đủ %s để thanh toán" % stt.amount)
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
        # # SangsLA thêm ngày 3/10/2018 Thêm order vào form khi chung của khách hàng
        # pos_sum_digital_obj = self.env['pos.sum.digital.sign'].search([('partner_id', '=', self.partner_id.id), ('state', '=', 'draft'), ('session_id', '=', self.session_id.id)])
        # if pos_sum_digital_obj:
        #     self.update({'x_digital_sign_id': pos_sum_digital_obj.id})
        # else:
        #     pos_sum_digital_obj = self.env['pos.sum.digital.sign'].create({
        #         'partner_id': self.partner_id.id,
        #         'state': 'draft',
        #         'date': my_date.today(),
        #         'session_id': self.session_id.id
        #     })
        #     self.update({'x_digital_sign_id': pos_sum_digital_obj.id})
        # for line in self.lines:
        #     line.update({'x_digital_sign_id': pos_sum_digital_obj.id})
        # for line in self.statement_ids:
        #     line.update({'x_digital_sign_id': pos_sum_digital_obj.id})
        # heets
        self.write(self_to_update)

    @api.multi
    def action_order_confirm(self):
        if self.state != 'to_confirm':
            raise except_orm('Cảnh báo!', ("Trạng thái đơn hàng đã thay đổi. Vui lòng F5 hoặc load lại trang"))
        self.x_cashier_id = self.env.uid
        amount_debt = 0
        journal_debt_id = self.config_id.journal_debt_id.id if self.config_id.journal_debt_id else False
        for stt in self.statement_ids:
            if journal_debt_id and stt.journal_id.id == journal_debt_id:
                amount_debt += stt.amount
        ''' Tạm thời cmt lại vì ở 3t cho thanh toán âm khi có ghi nợ
        if amount_debt != 0:
            for stt in self.statement_ids:
                if stt.amount < 0:
                    raise except_orm("Thông báo", ("Bạn không thể có thanh toán số tiền âm trên đơn có ghi nợ"))
        '''
        self.state = 'customer_comment'
        # is_debt = False
        # debt_total = 0.0
        # revenue = 0.0
        # to_debt = 0
        # exceptx = False
        # journal_debt_id = self.config_id.journal_debt_id.id if self.config_id.journal_debt_id else False
        # journal_exception_ids = self.config_id.journal_exception_ids.ids if self.config_id.journal_exception_ids else []
        # if journal_debt_id:
        #     # Ngoan sửa hạn mức xuất hàng, ngoại lệ, km ngoại lệ cần phê duyệt
        #     for statement1 in self.statement_ids:
        #         if statement1.journal_id.id == journal_debt_id:
        #             is_debt = True
        #             for statement in self.statement_ids:
        #                 obj_order_line = self.env['pos.order.line'].search([('order_id', '=', self.id)])
        #                 amount = 0
        #                 for line in obj_order_line:
        #                     obj_product = self.env['product.template'].search(
        #                         [('id', '=', line.product_id.product_tmpl_id.id), ('type', '=', 'product')])
        #                     if len(obj_product) > 0:
        #                         if line.x_qty > 0:
        #                             amount += (line.price_unit - (
        #                                         line.price_unit * line.discount / 100)) * line.x_qty - line.x_discount
        #                 if statement.journal_id.id != journal_debt_id:
        #                     debt_total += statement.amount
        #                     revenue += statement.amount
        #                 elif journal_exception_ids and statement.journal_id.id in journal_exception_ids:
        #                     exceptx = True
        #             if amount:
        #                 to_debt += debt_total - amount
        #         elif journal_exception_ids and statement1.journal_id.id in journal_exception_ids:
        #             exceptx = True
        #         else:
        #             to_debt += 0

        # Nếu đơn hàng có thanh toán nợ vượt hạn mức/ngoại lệ => Chuyển trạng thái chờ duyệt
        # if self.x_custom_discount or (is_debt and to_debt < 0.0) or exceptx:
        #     values = {'state': 'to_approve'}
        #     msg = []
        #     if self.x_custom_discount:
        #         msg.append('chiết khấu thủ công')
        #     if exceptx:
        #         msg.append('thanh toán ngoại lệ')
        #     if is_debt and to_debt < 0.0:
        #         msg.append('ghi nợ vượt hạn mức')
        #     # Thông báo quản lý phê duyệt
        #     values['message_follower_ids'] = []
        #     users = self.env['res.users'].search([
        #         ('groups_id', 'in', self.env.ref('point_of_sale.group_pos_manager').id),
        #         ('id', '!=', self._uid)])
        #     MailFollowers = self.env['mail.followers']
        #     follower_partner_ids = []
        #     for m in self.message_follower_ids:
        #         follower_partner_ids.append(m.partner_id.id)
        #     for user in users:
        #         if user.x_pos_config_id.id == self.config_id.id and \
        #                 user.partner_id.id and user.partner_id.id not in follower_partner_ids:
        #             values['message_follower_ids'] += \
        #                 MailFollowers._add_follower_command(self._name, [], {user.partner_id.id: None}, {})[0]
        #     self.write(values)
        #     self.message_post(subtype='mt_activities',
        #                       body="Đơn hàng%s cần phê duyệt!" % (' ' + ', '.join(msg) if len(msg) else ''))
        #     return {'type': 'ir.actions.act_window_close'}
        # else:
        self.action_order_complete()
        if not self.invoice_id:
            self.create_invoice()

        _logger.error("ngadv: %s" %(str('create_picking')))
        return self.create_picking()

    @api.multi
    def action_debt_approve(self):
        if self.state != 'to_approve':
            raise except_orm('Cảnh báo!', ("Trạng thái đơn hàng đã thay đổi. Vui lòng F5 hoặc load lại trang"))
        if self.amount_total == 0:
            self.action_pos_order_paid()
            self.state = 'customer_comment'
        else:
            self.state = 'to_payment'
        res_model_id = self.env['ir.model'].sudo().search([('model', '=', 'pos.order')]).id
        activity_ids = self.env['mail.activity'].sudo().search(
            [('res_model_id', '=', res_model_id), ('res_id', '=', self.id)])
        if len(activity_ids) > 0:
            activity_ids.sudo().action_done()

    @api.multi
    def action_order_cancel(self):
        if self.state not in ('to_approve', 'to_payment', 'customer_comment'):
            raise except_orm('Cảnh báo!', ("Trạng thái đơn hàng đã thay đổi. Vui lòng f5 hoặc load lại trang"))
        self.statement_ids = False
        self._compute_amount_all()
        self.update({'x_digital_sign_id': False})
        for line in self.lines:
            line.update({'x_digital_sign_id': False})
        for line in self.statement_ids:
            line.update({'x_digital_sign_id': False})
        if self.state in ('to_approve', 'to_payment'):
            if self.lines:
                for line in self.lines:
                    if line.lot_name:
                        lot_id = self.env['stock.production.lot'].search([('name', '=', line.lot_name)])
                        if lot_id:
                            lot_id.x_status = 'actived'
                        line.unlink()
            return self.write({'state': 'draft'})
        else:
            if self.x_type == '2':
                if self.lines:
                    for line in self.lines:
                        if line.lot_name:
                            lot_id = self.env['stock.production.lot'].search([('name', '=', line.lot_name)])
                            if lot_id:
                                lot_id.x_status = 'actived'
                            line.unlink()
                return self.write({'state': 'draft'})
            else:
                return self.write({'state': 'to_payment'})

    def _prepare_bank_statement_line_payment_values(self, data):
        args = super(PosOrder, self)._prepare_bank_statement_line_payment_values(data)
        if self._context.get('izi_vc_id', False):
            args['x_vc_id'] = self._context.get('izi_vc_id', False)
        return args

    def _action_create_invoice_line(self, line=False, invoice_id=False):
        invoice_line = super(PosOrder, self)._action_create_invoice_line(line, invoice_id)
        if line.discount:
            invoice_line.update({'discount': 0})
        # if line.x_discount:
        #     price_per_product = (line.x_subtotal_wo_discount - line.x_discount) / line.qty
        #     if line.discount:
        #         price_per_product -= round(price_per_product * line.discount / 100.0)
        #     discount = round((price_per_product - line.price_unit) / line.price_unit, 17)
        #     invoice_line.update({'discount': abs(discount) * 100})
        return invoice_line

    @api.multi
    def create_invoice(self):
        # Tạo hóa đơn
        invoice_obj = self.env['account.invoice']
        payment_obj = self.env['account.payment']
        journal_debt_id = self.config_id.journal_debt_id.id if self.config_id.journal_debt_id else False
        for order in self:
            total = 0.0  # Tổng đơn hàng
            residual = 0.0  # Số còn nợ
            paid_statements = []
            statement_ids = order.statement_ids.search([('id', 'in',order.statement_ids.ids )], order='amount')
            for statement in statement_ids:
                total += statement.amount
                if statement.journal_id.id == journal_debt_id:
                    residual += statement.amount
                else:
                    paid_statements.append(statement)
            # Tạo hoá đơn các đơn hàng nợ
            local_context = dict(self.env.context, force_company=order.company_id.id, company_id=order.company_id.id)
            invoice = invoice_obj.new(order._prepare_invoice())
            invoice._onchange_partner_id()
            invoice.fiscal_position_id = order.fiscal_position_id
            inv = invoice._convert_to_write({name: invoice[name] for name in invoice._cache})
            new_invoice = invoice_obj.with_context(local_context).create(inv)

            message = _("This invoice has been created from the point of sale session: <a href=# data-oe-model=pos.order data-oe-id=%d>%s</a>") % (order.id, order.name)
            new_invoice.message_post(body=message)
            discount_total = 0.0
            for line in order.lines:
                order.with_context(local_context)._action_create_invoice_line(line, new_invoice.id)
                price_per_product = line.price_unit
                if line.x_discount:
                    price_per_product = (line.x_subtotal_wo_discount - line.x_discount) / line.qty
                if line.discount:
                    price_per_product -= float(format(price_per_product * line.discount / 100.0, '.2f'))
                # Thêm dòng chiết khấu hoá đơn
                if price_per_product > 0.0:
                    # discount_total = round(discount_total)
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
                        'price_unit': -price_per_product,
                        'account_id': self.env['account.account'].search([('code', '=', '5211')], limit=1).id,
                        'name': inv_name + line.name,
                    }
                    invoice_line = InvoiceLine.new(inv_line)
                    inv_line = invoice_line._convert_to_write(
                        {name: invoice_line[name] for name in invoice_line._cache})
                    inv_line.update(price_unit=-discount_total, discount=0.0, name=inv_name)
                    InvoiceLine.create(inv_line)
                if price_per_product != line.price_unit:
                    discount_total += float(format((line.price_unit - price_per_product) * line.qty, '.2f'))
            # Thêm dòng chiết khấu tổng hoá đơn
            if discount_total > 0.0:
                discount_total = round(discount_total)
                InvoiceLine = self.env['account.invoice.line']
                discount_product = self.env['product.product'].search([('default_code', '=', 'DISCOUNT')], limit=1)
                if not discount_product:
                    raise MissingError("Chưa thiết lập sản phẩm chiết khấu đơn hàng.")
                inv_name = discount_product.name
                inv_line = {
                    'invoice_id': new_invoice.id,
                    'product_id': discount_product.id,
                    'quantity': 1,
                    'discount': 0.0,
                    'price_unit': -discount_total,
                    'account_id': self.env['account.account'].search([('code', '=', '5211')], limit=1).id,
                    'name': inv_name,
                }
                invoice_line = InvoiceLine.new(inv_line)
                inv_line = invoice_line._convert_to_write(
                    {name: invoice_line[name] for name in invoice_line._cache})
                inv_line.update(price_unit=-discount_total, discount=0.0, name=inv_name)
                InvoiceLine.create(inv_line)
            new_invoice.update({'branch_id': self.user_id.branch_id.id})
            new_invoice.with_context(local_context).compute_taxes()
            new_invoice.action_invoice_open()
            self.invoice_id = new_invoice.id
            new_invoice.x_pos_order_id = self.id
            # Hoàn tất các thanh toán không ghi nợ
            # statement_outbound = False
            pays_outbound = []
            pays_inbound = []
            for statement in paid_statements:
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
                        'invoice_ids': [(6, 0, new_invoice.ids)],
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
                for move_line in new_invoice.move_id.line_ids:
                    move_line.remove_move_reconcile()
                    if move_line.account_id.id == self.partner_id.property_account_receivable_id.id:
                        receivable_move_lines += move_line

                receivable_move_lines.filtered(lambda l: l.reconciled == False).reconcile()

            order.statement_ids.write({'x_ignore_reconcile': True})
            order.write({'state': 'invoiced', 'invoice_id': new_invoice.id})

    @api.multi
    def refund(self):
        if self.x_type == '4':
            raise except_orm("Cảnh báo!", ("Đây là đơn hàng phát sinh từ hủy dịch vụ. Bạn không thể refund đơn hàng này!"))
        # for line in self.lines:
        #     if line.product_id.x_type_card == 'pmh':
        #         lot_obj = self.env['stock.production.lot'].search([('name', '=', line.lot_name)])
        #         if datetime.strptime(lot_obj.life_date, '%Y-%m-%d %H:%M:%S') + timedelta(days=1) <= datetime.now():
        #             raise except_orm('Cảnh báo!', (('Mã "%s" hết hạn vào ngày: ' + datetime.strptime(lot_obj.life_date,
        #                                                                                              "%Y-%m-%d %H:%M:%S").strftime(
        #                 "%d-%m-%Y") + '. Bạn không thể refund') % line.lot_name.upper().strip()))
        #         if lot_obj.x_status == 'used':
        #             raise except_orm('Cảnh báo!', ("Phiếu mua hàng đã được sử dụng. Bạn không thể refund"))
        # if self.x_type != '1':
        #     raise except_orm('Cảnh báo!', ('Đơn hàng phát sinh từ dịch vụ khác không thẻ refund trên đơn hàng'))
        if self.x_pos_partner_refund_id:
            raise except_orm('Cảnh báo!', ("Đây là đơn Refund của đơn khác bạn không thể refund được "))
        pos_order_refund = self.env['pos.order'].search([('x_pos_partner_refund_id', '=', self.id)])
        if pos_order_refund:
            raise except_orm('Cảnh báo!', ("Đơn hàng này đã được refund với đơn refund %s" % pos_order_refund.name))
        # Tapj pos_order refund
        count_debt = 0
        journal_debt_id = self.config_id.journal_debt_id.id if self.config_id.journal_debt_id else False
        for line in self.statement_ids:
            if line.journal_id.id == journal_debt_id:
                count_debt += 1
                if not self.invoice_id:
                    raise except_orm('Cảnh báo!', ("Bạn cần tạo hóa đơn trước khi refund"))
        pos_session = self.env['pos.session']
        pos_config_id = self.env.user.x_pos_config_id.id
        my_session = pos_session.search([('config_id', '=', pos_config_id), ('state', '=', 'opened')])
        if not my_session:
            raise except_orm("Thông báo", "Không có phiên POS nào đang mở. Xin hãy mở phiên trước khi thao tác !!")
        Posorder = self.env['pos.order']
        PosorderLine = self.env['pos.order.line']
        argvs = {
            'name': 'RF_' + self.name,
            'partner_id': self.partner_id.id,
            'company_id': self.env.user.company_id.id,
            'x_rank_id': self.x_rank_id.id,
            # 'x_point_bonus': 0,
            'date_order': datetime.now(),
            'user_id': self.user_id.id,
            'pricelist_id': self.pricelist_id.id,
            'session_id': my_session.id,
            'x_promotion_id': self.x_promotion_id.id,
            'config_id': my_session.config_id.id,
            'state': 'draft',
            'location_id': my_session.config_id.stock_location_id.id,
            'x_pos_partner_refund_id': self.id,
            'x_type': self.x_type,
            'x_user_id': [(6, 0, self.x_user_id.ids)],
            'x_discount_computed': True,
            'x_cashier_id': self.x_cashier_id.id
        }
        pos_order_id = Posorder.create(argvs)
        pos_order_id.update({'name': 'RF_' + str(self.name)})
        if self.x_type != '2':
            if not self.session_id.config_id.x_charge_refund_id:
                raise except_orm("Thông báo!",("Vui lòng cấu hình chi phí đổi dịch vụ"))
            argvss = {
                'product_id': self.session_id.config_id.x_charge_refund_id.id,
                'name': pos_order_id.name,
                'price_unit': 0,
                'qty': 1,
                'discount': 0,
                'price_subtotal': 0,
                'price_subtotal_incl': 0,
                'lot_name': '',
                'order_id': pos_order_id.id,
                'x_is_gift': False
            }
            pos_order_line_id = PosorderLine.create(argvss)
        # Refund thẻ tiền nếu còn dư tiền trong thẻ
        for line in self.lines:
            if line.product_id.default_code == 'COIN' and line.x_is_gift == False:
                pos_virtual_money_obj = self.env['pos.virtual.money'].search([('order_id', '=', self.id)])
                for tmp in pos_virtual_money_obj:
                    if tmp.typex == '1':
                        if tmp.money == tmp.money_used:
                            raise except_orm('Cảnh báo!', ("Thẻ tiền đã sử dụng hết. Không thể refund"))
                        # if tmp.money_used >= 0.5 * tmp.money:
                        #     raise except_orm('Cảnh báo!', "Thẻ tiền sử dụng quá 50% số tiền . Bạn không thể refund")
                        else:
                            argvss = {
                                'product_id': line.order_id.session_id.config_id.x_charge_refund_id.id,
                                'name': pos_order_id.name,
                                'price_unit': tmp.money_used,
                                'qty': 1,
                                'discount': 0,
                                'price_subtotal': tmp.money_used,
                                'price_subtotal_incl': tmp.money_used,
                                'lot_name': '',
                                'order_id': pos_order_id.id,
                                'x_is_gift': False
                            }
                            pos_order_line_id = PosorderLine.create(argvss)
        # Thêm ngược sản phẩm vào pos_order_line
        for line in self.lines:
            x_total_qty = line.x_qty
            debit_good_line_obj = self.env['pos.debit.good.line'].search([('order_id', '=', self.id)])
            for x in debit_good_line_obj:
                if x.product_id.id == line.product_id.id:
                    x_total_qty = x.qty_depot
            argvss = {
                'product_id': line.product_id.id,
                'name': pos_order_id.name,
                'price_unit': line.price_unit,
                'qty': -line.qty,
                'x_qty': -x_total_qty,
                'discount': line.discount,
                'x_discount': -line.x_discount,
                'price_subtotal': -line.price_subtotal,
                'price_subtotal_incl': -line.price_subtotal_incl,
                'lot_name': line.lot_name,
                'order_id': pos_order_id.id,
                'x_is_gift': line.x_is_gift
            }
            pos_order_line_id = PosorderLine.create(argvss)
            if line.lot_name:
                argvs_lot = {
                    'pos_order_line_id': pos_order_line_id.id,
                    'lot_name': line.lot_name.upper().strip(),
                }
                pos_lot_id = self.env['pos.pack.operation.lot'].create(argvs_lot)
        # Thêm dịch vụ nếu khách hàng đã sử dụng dịch vụ trong thẻ
        for line in self.lines:
            if line.product_id.x_type_card == 'tdv' or line.product_id.x_type_card == 'tdt':
                lot_obj = self.env['stock.production.lot'].search([('name', '=', line.lot_name)])
                # exchange_service = self.env['izi.pos.exchange.service'].search([('product_lot_id', '=',lot_obj.id)])
                # if exchange_service:
                #     raise except_orm("Cảnh báo!", ("Đẫ có đơn đổi dịch vụ cho thẻ dịch vụ này. Không thể refund đơn hàng"))
                if datetime.strptime(lot_obj.life_date, '%Y-%m-%d %H:%M:%S') + timedelta(days=1) <= datetime.now():
                    raise except_orm('Cảnh báo!', (('Mã "%s" hết hạn vào ngày: ' + datetime.strptime(lot_obj.life_date,
                                                                                                     "%Y-%m-%d %H:%M:%S").strftime(
                        "%d-%m-%Y")) % line.lot_name.upper().strip()))
                for tmp in lot_obj.x_card_detail_ids:
                    # lấy giá bán lẻ để refund
                    if not self.pricelist_id:
                        raise UserError(
                            _('You have to select a pricelist in the sale form !\n'
                              'Please set one before choosing a product.'))
                    price = self.pricelist_id.get_product_price(
                        tmp.product_id, tmp.total_qty or 1.0, self.partner_id)
                    if tmp.qty_use == 0:
                        continue
                    discount = 0
                    for i in self.lines:
                        if i.product_id.id == tmp.product_id.id and i.x_is_gift == False:
                            discount = i.discount
                    argvss = {
                        'product_id': tmp.product_id.id,
                        'name': pos_order_id.name,
                        'price_unit': price,
                        'qty': tmp.qty_use,
                        'discount': discount,
                        'price_subtotal': (tmp.price_unit * tmp.qty_use) - (tmp.price_unit * tmp.qty_use) * discount,
                        'price_subtotal_incl': (tmp.price_unit * tmp.qty_use) - (
                                tmp.price_unit * tmp.qty_use) * discount,
                        'lot_name': '',
                        'order_id': pos_order_id.id,
                        'x_is_gift': False
                    }
                    pos_order_line_id = PosorderLine.create(argvss)
                #Xóa những dịch vụ đã hủy từ trước đó
                for tmp in lot_obj.x_card_detail_ids:
                    if tmp.state == 'cancel':
                        if tmp.product_id.id == line.product_id.id:
                            line.unlink()
        journal_exception_ids = self.config_id.journal_exception_ids.ids if self.config_id.journal_exception_ids else False
        journal_loyal_ids = self.config_id.journal_loyal_ids.ids if self.config_id.journal_loyal_ids else False
        journal_deposit_id = self.config_id.journal_deposit_id if self.config_id.journal_deposit_id else False
        # Có hình thức là chiết khấu ngoại lệ và dùng VC thanh toán
        for line in self.statement_ids:
            # Các hình thức tính doanh thu thêm ngược lại
            if journal_loyal_ids and line.journal_id.id in journal_loyal_ids:
                # Nếu trong cùng phiên
                if self.session_id.id == my_session.id:
                    agrsv = {
                        'ref': my_session.name,
                        'name': pos_order_id.name,
                        'partner_id': self.partner_id.id,
                        'account_id': line.account_id.id,
                        'date': datetime.now().date(),
                        'journal_id': line.journal_id.id,
                        'statement_id': line.statement_id.id,
                        'pos_statement_id': pos_order_id.id,
                        'amount': -line.amount,
                        'x_vc_id': None,
                        'x_amount_currency': -line.x_amount_currency,
                        'x_currency_id': line.x_currency_id.id,
                        'x_rate_vn': line.x_rate_vn,
                    }
                    pos_make_payment_id = self.env['account.bank.statement.line'].create(agrsv)
                # Nếu khác phiên
                else:
                    tmp = None
                    for tmp in my_session.statement_ids:
                        if tmp.journal_id.id == line.journal_id.id:
                            break
                    agrsv = {
                        'ref': my_session.name,
                        'name': pos_order_id.name,
                        'partner_id': self.partner_id.id,
                        'account_id': line.account_id.id,
                        'date': datetime.now().date(),
                        'journal_id': tmp.journal_id.id,
                        'statement_id': tmp.id,
                        'pos_statement_id': pos_order_id.id,
                        'amount': -line.amount,
                        'x_vc_id': None,
                        'x_amount_currency': -line.x_amount_currency,
                        'x_currency_id': line.x_currency_id.id,
                        'x_rate_vn': line.x_rate_vn,
                    }
                    pos_make_payment_id = self.env['account.bank.statement.line'].create(agrsv)
            # Nếu hình thức là đặt cọc
            if journal_deposit_id and line.journal_id.id == journal_deposit_id.id:
                # Nếu trong cùng phiên
                if self.session_id.id == my_session.id:
                    agrsv = {
                        'ref': my_session.name,
                        'name': pos_order_id.name,
                        'partner_id': self.partner_id.id,
                        'account_id': line.account_id.id,
                        'date': datetime.now().date(),
                        'journal_id': line.journal_id.id,
                        'statement_id': line.statement_id.id,
                        'pos_statement_id': pos_order_id.id,
                        'amount': -line.amount,
                        'x_vc_id': None
                    }
                    pos_make_payment_id = self.env['account.bank.statement.line'].create(agrsv)
                # Nếu khác phiên
                else:
                    tmp = None
                    for tmp in my_session.statement_ids:
                        if tmp.journal_id.id == line.journal_id.id:
                            break
                    agrsv = {
                        'ref': my_session.name,
                        'name': pos_order_id.name,
                        'partner_id': self.partner_id.id,
                        'account_id': line.account_id.id,
                        'date': datetime.now().date(),
                        'journal_id': tmp.journal_id.id,
                        'statement_id': tmp.id,
                        'pos_statement_id': pos_order_id.id,
                        'amount': -line.amount,
                        'x_vc_id': None
                    }
                    pos_make_payment_id = self.env['account.bank.statement.line'].create(agrsv)
            if journal_exception_ids and line.journal_id.id in journal_exception_ids:
                # Nếu trong cùng phiên
                if self.session_id.id == my_session.id:
                    agrsv = {
                        'ref': my_session.name,
                        'name': pos_order_id.name,
                        'partner_id': self.partner_id.id,
                        'account_id': line.account_id.id,
                        'date': datetime.now().date(),
                        'journal_id': line.journal_id.id,
                        'statement_id': line.statement_id.id,
                        'pos_statement_id': pos_order_id.id,
                        'amount': -line.amount,
                        'x_vc_id': None
                    }
                    pos_make_payment_id = self.env['account.bank.statement.line'].create(agrsv)
                # Nếu khác phiên
                else:
                    tmp = None
                    for tmp in my_session.statement_ids:
                        if tmp.journal_id.id == line.journal_id.id:
                            break
                    agrsv = {
                        'ref': my_session.name,
                        'name': pos_order_id.name,
                        'partner_id': self.partner_id.id,
                        'account_id': line.account_id.id,
                        'date': datetime.now().date(),
                        'journal_id': tmp.journal_id.id,
                        'statement_id': tmp.id,
                        'pos_statement_id': pos_order_id.id,
                        'amount': -line.amount,
                        'x_vc_id': None
                    }
                    pos_make_payment_id = self.env['account.bank.statement.line'].create(agrsv)
            # Nếu trong thanh toán có hình thức thanh toán bằng VC
            if line.journal_id.code.upper() == 'VC':
                x_lot_id = None
                if line.x_vc_name:
                    x_lot_id = self.env['stock.production.lot'].search(
                        [('name', '=', line.x_vc_name.upper().strip())], limit=1).id
                # Nếu trong cùng phiên
                if self.session_id.id == my_session.id:
                    agrsv = {
                        'ref': my_session.name,
                        'name': pos_order_id.name,
                        'partner_id': self.partner_id.id,
                        'account_id': line.account_id.id,
                        'date': datetime.now().date(),
                        'journal_id': line.journal_id.id,
                        'statement_id': line.statement_id.id,
                        'pos_statement_id': pos_order_id.id,
                        'amount': -line.amount,
                        'x_vc_id': x_lot_id
                    }
                    pos_make_payment_id = self.env['account.bank.statement.line'].create(agrsv)
                #         Nếu khác phiên
                else:
                    tmp = None
                    for tmp in my_session.statement_ids:
                        if tmp.journal_id.id == line.journal_id.id:
                            break
                    agrsv = {
                        'ref': my_session.name,
                        'name': pos_order_id.name,
                        'partner_id': self.partner_id.id,
                        'account_id': line.account_id.id,
                        'date': datetime.now().date(),
                        'journal_id': tmp.journal_id.id,
                        'statement_id': tmp.id,
                        'pos_statement_id': pos_order_id.id,
                        'amount': -line.amount,
                        'x_vc_id': x_lot_id
                    }
                    pos_make_payment_id = self.env['account.bank.statement.line'].create(agrsv)

            # Nếu trong thanh toán có hình thức thanh toán bằng thẻ tiền
            if line.journal_id.code.upper() == 'VM':
                x_lot_id = None
                # Nếu trong cùng phiên
                if self.session_id.id == my_session.id:
                    agrsv = {
                        'ref': my_session.name,
                        'name': pos_order_id.name,
                        'partner_id': self.partner_id.id,
                        'account_id': line.account_id.id,
                        'date': datetime.now().date(),
                        'journal_id': line.journal_id.id,
                        'statement_id': line.statement_id.id,
                        'pos_statement_id': pos_order_id.id,
                        'amount': -line.amount,
                        'x_vc_id': x_lot_id
                    }
                    pos_make_payment_id = self.env['account.bank.statement.line'].create(agrsv)
                #         Nếu khác phiên
                else:
                    tmp = None
                    for tmp in my_session.statement_ids:
                        if tmp.journal_id.id == line.journal_id.id:
                            break
                    agrsv = {
                        'ref': my_session.name,
                        'name': pos_order_id.name,
                        'partner_id': self.partner_id.id,
                        'account_id': line.account_id.id,
                        'date': datetime.now().date(),
                        'journal_id': tmp.journal_id.id,
                        'statement_id': tmp.id,
                        'pos_statement_id': pos_order_id.id,
                        'amount': -line.amount,
                        'x_vc_id': x_lot_id
                    }
                    pos_make_payment_id = self.env['account.bank.statement.line'].create(agrsv)

        # Có hình thức ghi nợ
        if count_debt != 0:
            if self.invoice_id.residual != 0:
            # kiểm tra xem đã có thanh toán cho ghi nợ không
            # invoice_make_payment_obj = self.env['invoice.make.payment'].search(
            #     [('invoice_id', '=', self.invoice_id.id)])
            # Nếu không có thanh toán cho ghi nợ
            # if not invoice_make_payment_obj:
                for line in my_session.statement_ids:
                    if line.journal_id.id == journal_debt_id:
                        # Nếu refund trong cùng phiên
                        if self.session_id.id == my_session.id:
                            agrsv = {
                                'ref': my_session.name,
                                'name': pos_order_id.name,
                                'partner_id': self.partner_id.id,
                                'account_id': line.account_id.id,
                                'date': datetime.now().date(),
                                'journal_id': line.journal_id.id,
                                'statement_id': line.id,
                                'pos_statement_id': pos_order_id.id,
                                'amount': -self.invoice_id.residual,
                                'x_vc_id': None
                            }
                            pos_make_payment_id = self.env['account.bank.statement.line'].create(agrsv)
                        # Refund khác phiên
                        else:
                            tmp = None
                            for tmp in my_session.statement_ids:
                                if tmp.journal_id.id == line.journal_id.id:
                                    break
                            agrsv = {
                                'ref': my_session.name,
                                'name': pos_order_id.name,
                                'partner_id': self.partner_id.id,
                                'account_id': line.account_id.id,
                                'date': datetime.now().date(),
                                'journal_id': tmp.journal_id.id,
                                'statement_id': tmp.id,
                                'pos_statement_id': pos_order_id.id,
                                'amount': -self.invoice_id.residual,
                                'x_vc_id': None
                            }
                            pos_make_payment_id = self.env['account.bank.statement.line'].create(agrsv)
            # Nếu có thanh toán cho hình thức ghi nợ
            # else:
            #     total = 0
            #     journal_id = None
            #     for invoice in invoice_make_payment_obj:
            #         total += invoice.amount
            #         journal_id = invoice.journal_id
            #     for line in self.statement_ids:
            #         # Nếu refund trong cùng phiên
            #         if self.session_id.id == my_session.id:
            #             # tạo account_bank_statement_line khi hình thức là ghi nợ
            #             if line.journal_id.id == journal_debt_id:
            #                 money = line.amount - total
            #                 agrsv = {
            #                     'ref': my_session.name,
            #                     'name': pos_order_id.name,
            #                     'partner_id': self.partner_id.id,
            #                     'account_id': line.account_id.id,
            #                     'date': datetime.now().date(),
            #                     'journal_id': line.journal_id.id,
            #                     'statement_id': line.statement_id.id,
            #                     'pos_statement_id': pos_order_id.id,
            #                     'amount': -money,
            #                     'x_vc_id': None
            #                 }
            #                 pos_make_payment_id = self.env['account.bank.statement.line'].create(agrsv)
            #         # # Refund khác phiên
            #         else:
            #             x_lot_id = None
            #             if line.x_vc_name:
            #                 x_lot_id = self.env['stock.production.lot'].search(
            #                     [('name', '=', line.x_vc_name.upper().strip())], limit=1).id
            #             tmp = None
            #             for tmp in my_session.statement_ids:
            #                 if tmp.journal_id.id == line.journal_id.id:
            #                     break
            #             # tạo account_bank_statement_line khi hình thức là ghi nợ
            #             if line.journal_id.id == journal_debt_id:
            #                 money = line.amount - total
            #                 agrsv = {
            #                     'ref': my_session.name,
            #                     'name': pos_order_id.name,
            #                     'partner_id': self.partner_id.id,
            #                     'account_id': line.account_id.id,
            #                     'date': datetime.now().date(),
            #                     'journal_id': tmp.journal_id.id,
            #                     'statement_id': tmp.id,
            #                     'pos_statement_id': pos_order_id.id,
            #                     'amount': -money,
            #                     'x_vc_id': x_lot_id
            #                 }
            #                 pos_make_payment_id = self.env['account.bank.statement.line'].create(agrsv)
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
            'res_id': pos_order_id.id,
            'context': self.env.context,
        }

    @api.multi
    def send_refund(self):
        if len(self.lines) == 0:
            raise except_orm("Cảnh báo!", ('Bạn không thể gửi đơn duyệt refund khi không có dịch vụ hoặc sản phẩm nào!'))
        for line in self.lines:
            if line.product_id.x_type_card == 'pmh':
                lot_obj = self.env['stock.production.lot'].search([('name', '=', line.lot_name)])
                if datetime.strptime(lot_obj.life_date, '%Y-%m-%d %H:%M:%S') + timedelta(days=1) <= datetime.now():
                    raise except_orm('Cảnh báo!', (('Mã "%s" hết hạn vào ngày: ' + datetime.strptime(lot_obj.life_date,
                                                                                                     "%Y-%m-%d %H:%M:%S").strftime(
                        "%d-%m-%Y") + '. Bạn không thể refund') % line.lot_name.upper().strip()))
                if lot_obj.x_status == 'used':
                    raise except_orm('Cảnh báo!', ("Phiếu mua hàng đã được sử dụng. Bạn không thể refund"))
        for line in self.lines:
            if line.product_id.x_type_card == 'tdv' or line.product_id.x_type_card == 'tdt':
                lot_obj = self.env['stock.production.lot'].search([('name', '=', line.lot_name)])
                exchange_service = self.env['izi.pos.exchange.service'].search([('product_lot_id', '=',lot_obj.id), ('state', '!=', 'refunded')])
                if exchange_service:
                    raise except_orm("Cảnh báo!", ("Đẫ có đơn đổi dịch vụ cho thẻ dịch vụ này. Không thể refund đơn hàng"))
        # for order in self:
        #     for statement in order.statement_ids:
        #         if statement.amount > 0:
        #             raise except_orm("Cảnh báo!", ("Số tiền thanh toán không lớn hơn không trong đơn refund"))
        total = 0
        for line in self.statement_ids:
            total += line.amount
        if self.amount_total != total:
            raise except_orm('Cảnh báo!', "Bạn cần thanh toán đủ trước khi gửi refund")
        picking = self.env['stock.picking']
        for line in self.x_pos_partner_refund_id.picking_id:
            if line.state != 'done':
                picking = line
                break
        for line in self.lines:
            # if line.product_id.product_tmpl_id.type == 'product':
            #     debit_good_obj = self.env['pos.debit.good.line'].search([('product_id', '=', line.product_id.id), ('order_id', '=', self.x_pos_partner_refund_id.id)])
            #     count_debit_product = 0 #đếm số lượng hàng còn nợ trên đơn hàng
            #     count_product_order = 0 #đếm số lượng hàng trên đơn hàng
            #     if not debit_good_obj:
            #         continue
            #     for i in debit_good_obj:
            #         count_debit_product +=i.qty_debit
            #     pos_order_line = self.env['pos.order.line'].search([('product_id', '=', line.product_id.id), ('order_id', '=', self.id)])
            #     for i in pos_order_line:
            #         count_product_order += i.qty
            #     if count_debit_product > abs(count_product_order):
            #         raise except_orm("Cảnh báo!", ("Còn nợ hàng. Bạn phải xuất hàng cho khách hàng trước khi refund"))
            if line.product_id.x_type_card == 'tdv' or line.product_id.x_type_card == 'tdt':
                lot_obj = self.env['stock.production.lot'].search([('name', '=', line.lot_name)])
                for tmp in lot_obj.x_card_detail_ids:
                    if tmp.state == 'cancel':
                        raise except_orm("Cảnh báo!", (
                            "Đã có dịch vụ được hủy 1 phần. Bạn cần xóa những dịch vụ và sản phẩm khuyến mại cho dịch vụ đó và thẻ dịch vụ"))
        param_obj = self.env['ir.config_parameter']
        code = param_obj.get_param('default_code_exception')
        if not code:
            raise ValidationError(
                _(u"Bạn chưa cấu hình thông số hệ thống cho mã dịch vụ ngoại lệ. Xin hãy liên hệ với người quản trị."))
        list = code.split(',')
        if len(self.lines) != 0:
            k = 0
            i = 0
            for line in self:
                for tmp in line.lines:
                    if (tmp.product_id.product_tmpl_id.x_type_card == 'tdv' or tmp.product_id.product_tmpl_id.x_type_card == 'tdt'):
                        i = i + 1

                    if (
                            tmp.product_id.product_tmpl_id.type == 'service' and tmp.product_id.product_tmpl_id.default_code not in list):
                        if tmp.product_id not in line.session_id.config_id.product_edit_price_ids:
                            k = k + 1
            if i >= 2:
                raise except_orm('Cảnh báo!', 'Bạn không thể hủy 2 thẻ dịch vụ trên cùng 1 đơn hàng')
            if i == 0 and k > 0 and self.x_type == '1':
                raise except_orm('Cảnh báo!', 'Bạn phải gắn thẻ dịch vụ cho các dịch vụ vừa chọn!')
            if i == 1 and k == 0:
                raise except_orm('Cảnh báo!', 'Không cho phép hủy thẻ dịch vụ không gắn với dịch vụ nào.\n'
                                              ' Vui lòng gắn dịch vụ cho thẻ dịch vụ vừa chon!')
        # Sangla thêm 11/04/2019 kiểm tra nếu trong đơn bán có dịch vụ thì trong đơn refund phải có những dịch vụ đó
        # for line in self.x_pos_partner_refund_id.lines:
        #     count = 0
        #     for tmp in self.lines:
        #         if line.product_id.id  == tmp.product_id.id:
        #             count +=1
        #     if count == 0:
        #         raise except_orm("Cảnh báo!", ("Khi hủy dịch vụ trên đơn hàng. Bạn cần phải hủy tất cả dịch vụ trong thẻ!"))
        journal_loyal_ids = self.config_id.journal_loyal_ids.ids if self.config_id.journal_loyal_ids else False
        if journal_loyal_ids:
            loyal_total = 0.0
            for stt in self.statement_ids:
                if journal_loyal_ids and stt.journal_id.id in journal_loyal_ids:
                    loyal_total += stt.amount
            # Tính lại giá trị của điểm thưởng
            if loyal_total < 0:
                # point = self._get_loyal_total(loyal_total)
                # ####
                # self.update({'x_point_bonus': point})
                self.update({'x_total_order': loyal_total})
        # count_picking = 0
        amount_debt = 0
        journal_debt_id = self.config_id.journal_debt_id.id if self.config_id.journal_debt_id else False
        for stt in self.statement_ids:
            if journal_debt_id and stt.journal_id.id == journal_debt_id:
                amount_debt += stt.amount
        if self.x_pos_partner_refund_id.invoice_id:
            amount_residual = self.x_pos_partner_refund_id.invoice_id.residual
            if amount_residual < abs(amount_debt):
                raise except_orm("Thông báo!", ("Không thể trả lại ghi nợ nhiều hơn số tiền ghi nợ hiện tại của khách hàng. Vui lòng kiểm tra lại hình thức trả lại"))
        else:
            raise except_orm("Thông báo!", (
                "Bạn không thể trả bằng hình thức ghi nợ do đơn ban đầu không bán nợ. Vui lòng kiểm tra lại hình thức trả lại"))
        self.state = 'to_approve'

    @api.multi
    def action_cancel_refund(self):
        self.state = 'draft'

    @api.multi
    def confirm_refund(self):
        if self.state not in ('to_approve','draft'):
            raise except_orm('Cảnh báo!', ("Trạng thái đơn hàng đã thay đổi. Vui lòng F5 hoặc load lại trang"))
        self.state = 'customer_comment'
        #  Tạo lại đơn trả lại tiền
        journal_debt_id = self.config_id.journal_debt_id.id if self.config_id.journal_debt_id else False
        count = 0  # biến điếm thanh toán bằng tiên ào
        for line in self.statement_ids:
            # cập nhật lại phiếu mua hàng
            if line.x_vc_id:
                line.x_vc_id.x_status = 'using'
                line.x_vc_id.x_user_id = False
            if line.journal_id.code.upper() == 'VM':
                count += 1
            # đẩy vào tiền đặt cọc khi chọn hình thức refund là đặt cọc
            if line.journal_id.id == self.session_id.config_id.journal_deposit_id.id:
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
                    'journal_id': line.journal_id.id,
                    'date': self.date_order,
                    'amount': -line.amount,
                    'order_id': self.id,
                    'deposit_id': deposit_lines[0].id,
                    'type': 'deposit',
                    'x_type': 'deposit',
                    'partner_id': self.partner_id.id,
                    'session_id': self.session_id.id
                }
                deposit_id = self.env['pos.customer.deposit.line'].create(argvs)
                deposit_id.update({'state': 'done'})
                # tang x_balancce trong res_partner
                self.partner_id.x_balance = self.partner_id.x_balance - line.amount
        # cập nhật lại tiền ảo
        vm_histories = []
        if count > 0:
            vm_history_obj = self.env['pos.virtual.money.history'].search(
                [('order_id', '=', self.x_pos_partner_refund_id.id)])
            for line in vm_history_obj:
                line.vm_id.money_used -= line.amount
                vm_histories.append(
                    {'vm_id': line.vm_id.id, 'order_id': self.id, 'amount': -line.amount})
        for h in vm_histories:
            self.env['pos.virtual.money.history'].create(h)
        #  Cập nhật lại thông tin hàng hóa
        # Nếu là bán tiền ảo thì trừ tiền ảo trong thẻ tiền của khách hàng
        for line in self.lines:
            if line.product_id.x_type_card == 'tdv' or line.product_id.x_type_card == 'pmh' or line.product_id.x_type_card == 'tdt':
                product_lot = self.env['stock.production.lot'].search([('name', '=', line.lot_name)])
                product_lot.x_status = 'destroy'
                for tmp in product_lot.x_card_detail_ids:
                    tmp.state = 'cancel'
                # product_lot.x_customer_id = False
                # for tmp in product_lot.x_card_detail_ids:
                #     tmp.unlink()
            if line.product_id.default_code == 'COIN':
                pos_virtual_money_obj = self.env['pos.virtual.money'].search(
                    [('order_id', '=', self.x_pos_partner_refund_id.id)])
                for tmp in pos_virtual_money_obj:
                    tmp.state = 'cancel'
                    if tmp.typex == '1':
                        # Cập nhật hạn mức ghi nợ của KH = số tiền đã thanh toán cho thẻ tiền
                        if not self.x_owner_id:
                            self.partner_id.x_balance += tmp.money - tmp.debt_amount - tmp.money_used
                        else:
                            self.x_owner_id.x_balance += tmp.money - tmp.debt_amount - tmp.money_used
        # Kiểm tra và ghi nhận doanh thu
        # Mã các phương thức thanh toán có thể ghi nhận doanh thu
        journal_loyal_ids = self.config_id.journal_loyal_ids.ids if self.config_id.journal_loyal_ids else False
        if journal_loyal_ids:
            loyal_total = 0.0
            for stt in self.statement_ids:
                if stt.journal_id.id in journal_loyal_ids:
                    if stt.amount < 0:
                        revenue = self.env['crm.vip.customer.revenue'].create({
                            'partner_id': self.partner_id.id,
                            'order_id':self.id,
                            'journal_id': stt.journal_id.id,
                            'amount': stt.amount,
                            ' date': my_date.today(),
                        })
                    loyal_total += stt.amount
            # Ghi nhận doanh thu
            if loyal_total < 0:
                # point_history = self.env['izi.vip.point.history'].create({
                #     'partner_id': self.partner_id.id,
                #     'order_id': self.id,
                #     'date': my_date.today(),
                #     'point': self.x_point_bonus,
                # })
                self.x_loyal_id = revenue.id
                self.partner_id.update({'x_loyal_total': self.partner_id.x_loyal_total + loyal_total})
                # self.x_loyal_total = self.partner_id.x_loyal_total
                # self.x_point_total = self.partner_id.x_point_total
                self.update({'x_total_order': loyal_total})
                self.update({'x_loyal_total': self.partner_id.x_loyal_total})
                # self.x_total_order = loyal_total
        self.state = 'customer_comment'
        # self.x_pos_partner_refund_id.state = 'done'

        # Tạo hóa đơn ngược so với hóa đơn nợ hàng
        # if self.x_pos_partner_refund_id.invoice_id:
            # invoice_id = self.create_invoice()
            # self.invoice_id = invoice_id.id
            # for inv in self.x_pos_partner_refund_id.invoice_id:
            #     # date = form.date or False
            #     # description = form.description or inv.name
            #     # refund = inv.refund(form.date_invoice, date, description, inv.journal_id.id)
            #     # created_inv.append(refund.id)
            #     # if mode in ('cancel', 'modify'):
            #     movelines = inv.move_id.line_ids
            #     to_reconcile_ids = {}
            #     to_reconcile_lines = self.env['account.move.line']
            #     for line in movelines:
            #         if line.account_id.id == inv.account_id.id:
            #             to_reconcile_lines += line
            #             to_reconcile_ids.setdefault(line.account_id.id, []).append(line.id)
            #         if line.reconciled:
            #             line.remove_move_reconcile()
            #     # invoice_id.action_invoice_open()
            #     for tmpline in self.invoice_id.move_id.line_ids:
            #         if tmpline.account_id.id == inv.account_id.id:
            #             to_reconcile_lines += tmpline
            #     to_reconcile_lines.filtered(lambda l: l.reconciled == False).reconcile()
        if self.x_pos_partner_refund_id.invoice_id:
            # Tạo hóa đơn
            invoice_obj = self.env['account.invoice']
            payment_obj = self.env['account.payment']
            journal_debt_id = self.config_id.journal_debt_id.id if self.config_id.journal_debt_id else False
            total = 0.0  # Tổng đơn hàng
            residual = 0.0  # Số còn nợ
            paid_statements = []
            for order in self:
                for statement in order.statement_ids:
                    total += statement.amount
                    if statement.journal_id.id == journal_debt_id:
                        residual += statement.amount
                    else:
                        paid_statements.append(statement)
                # Tạo hoá đơn các đơn hàng nợ
                local_context = dict(self.env.context, force_company=order.company_id.id,
                                     company_id=order.company_id.id)
                invoice = invoice_obj.new(order._prepare_invoice())
                invoice._onchange_partner_id()
                invoice.fiscal_position_id = order.fiscal_position_id
                inv = invoice._convert_to_write({name: invoice[name] for name in invoice._cache})
                new_invoice = invoice_obj.with_context(local_context).create(inv)

                message = _(
                    "This invoice has been created from the point of sale sessionxx: <a href=# data-oe-model=pos.order data-oe-id=%d>%s</a>") % (
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
                    invoice_line = InvoiceLine.new(inv_line)
                    inv_line = invoice_line._convert_to_write(
                        {name: invoice_line[name] for name in invoice_line._cache})
                    inv_line.update(price_unit=discount_total, discount=0.0, name=inv_name)
                    InvoiceLine.create(inv_line)
                new_invoice.with_context(local_context).compute_taxes()
                new_invoice.action_invoice_open()
                self.invoice_id = new_invoice.id
                new_invoice.x_pos_order_id = self.id
            # invoice_id = self.create_invoice()
            # self.invoice_id = invoice_id.id
            if self.invoice_id:
                self.statement_ids.write({'x_ignore_reconcile': True})
                # statement_outbound = False
                pays_outbound = []
                pays_inbound = []
                for statement in paid_statements:
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
                            'invoice_ids': [(6, 0, new_invoice.ids)],
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
                    for move_line in new_invoice.move_id.line_ids:
                        move_line.remove_move_reconcile()
                        if move_line.account_id.id == self.partner_id.property_account_receivable_id.id:
                            receivable_move_lines += move_line

                    receivable_move_lines.filtered(lambda l: l.reconciled == False).reconcile()
            #     for line in self.statement_ids:
            #         payment_methods = line.journal_id.inbound_payment_method_ids
            #         payment_method_id = payment_methods and payment_methods[0] or False
            #         journal_debt_id = self.config_id.journal_debt_id.id if self.config_id.journal_debt_id else False
            #         if line.journal_id.id == journal_debt_id:
            #             continue
            #         argvas = {
            #             'amount': abs(line.amount),
            #             'journal_id': line.journal_id.id,
            #             'payment_date': line.date,
            #             'communication': line.name,
            #             'payment_method_id': payment_method_id.id,
            #             'payment_type': 'outbound',
            #             'invoice_ids': [(6, 0, new_invoice.ids)],
            #             'partner_type': 'customer',
            #             'partner_id': self.partner_id.id,
            #         }
            #         account_payment = self.env['account.payment'].create(argvas)
            #         account_payment.with_context(izi_partner_debt=True).action_validate_invoice_payment()
            # + TH1 nếu đơn ban đầu thanh toán hết thì lúc refund không bỏ reconcile ban đầu mà tạo reconcile các bút toán sau khi refund
            # + TH2 nếu đơn ban đầu lức có nợ thì bỏ reconcile đơn ban đầu sau đó reconcile lại toàn bộ cả đơn ban đầu và đơn refund
            if self.invoice_id:
                if residual != 0:
                    for inv in self.x_pos_partner_refund_id.invoice_id:
                        movelines = inv.move_id.line_ids
                        to_reconcile_ids = {}
                        to_reconcile_lines = self.env['account.move.line']
                        for line in movelines:
                            if line.account_id.id == inv.account_id.id:
                                to_reconcile_lines += line
                                to_reconcile_ids.setdefault(line.account_id.id, []).append(line.id)
                            if line.reconciled:
                                line.remove_move_reconcile()
                        for tmpline in self.invoice_id.move_id.line_ids:
                            if tmpline.account_id.id == inv.account_id.id:
                                to_reconcile_lines += tmpline
                                # tmpline.remove_move_reconcile()
                        # for x in payment:
                        #     for y in x.move_line_ids:
                        #         if y.account_id.id == inv.account_id.id:
                        #             to_reconcile_lines += y
                        to_reconcile_lines.filtered(lambda l: l.reconciled == False).reconcile()
            # if self.invoice_id:
            #     for inv in self.x_pos_partner_refund_id.invoice_id:
            #         # date = form.date or False
            #         # description = form.description or inv.name
            #         # refund = inv.refund(form.date_invoice, date, description, inv.journal_id.id)
            #         # created_inv.append(refund.id)
            #         # if mode in ('cancel', 'modify'):
            #         movelines = inv.move_id.line_ids
            #         to_reconcile_ids = {}
            #         to_reconcile_lines = self.env['account.move.line']
            #         for line in movelines:
            #             if line.account_id.id == inv.account_id.id:
            #                 to_reconcile_lines += line
            #                 to_reconcile_ids.setdefault(line.account_id.id, []).append(line.id)
            #             if line.reconciled:
            #                 line.remove_move_reconcile()
            #         # invoice_id.action_invoice_open()
            #         for tmpline in self.invoice_id.move_id.line_ids:
            #             if tmpline.account_id.id == inv.account_id.id:
            #                 to_reconcile_lines += tmpline
            #         to_reconcile_lines.filtered(lambda l: l.reconciled == False).reconcile()
            # argvs = {
            #     'description': self.name,
            #     'date_invoice': datetime.now().date()
            # }
            # account_invoice_refund = self.env['account.invoice.refund'].create(argvs)
            # ctx = account_invoice_refund.env.context.copy()
            # ctx.update({'active_ids': self.x_pos_partner_refund_id.invoice_id.id,
            #             'active_id': self.x_pos_partner_refund_id.invoice_id.id, 'active_model': 'account.invoice'})
            # invoice_refund_id = account_invoice_refund.with_context(ctx).invoice_refund()
            # invoice_refund_obj = self.env['account.invoice'].browse(invoice_refund_id['invoice_id'][0])
            # invoice_refund_obj.action_invoice_open()
            # self.invoice_id = invoice_refund_obj.id
            # account_move_line_obj = self.env['account.move.line'].search(
            #     [('invoice_id', '=', self.x_pos_partner_refund_id.invoice_id.id),
            #      ('account_id', '=', self.x_pos_partner_refund_id.invoice_id.account_id.id),
            #      ('amount_residual', '>', 0)])
            # for account_move_line_id in account_move_line_obj:
            #     new_invoice.assign_outstanding_credit(account_move_line_id.id)
            # if self.invoice_id:
            #     self.statement_ids.write({'x_ignore_reconcile': True})
            #     for line in self.statement_ids:
            #         payment_methods = line.journal_id.inbound_payment_method_ids
            #         payment_method_id = payment_methods and payment_methods[0] or False
            #         journal_debt_id = self.config_id.journal_debt_id.id if self.config_id.journal_debt_id else False
            #         if line.journal_id.id == journal_debt_id:
            #             continue
            #         argvas = {
            #             'amount': abs(line.amount),
            #             'journal_id': line.journal_id.id,
            #             'payment_date': line.date,
            #             'communication': line.name,
            #             'payment_method_id': payment_method_id.id,
            #             'payment_type': 'outbound',
            #             'invoice_ids': [(6, 0, new_invoice.ids)],
            #             'partner_type': 'customer',
            #             'partner_id': self.partner_id.id,
            #         }
            #         account_payment = self.env['account.payment'].create(argvas)
            #         account_payment.with_context(izi_partner_debt=True).action_validate_invoice_payment()
                    # self.statement_ids.write({'x_ignore_reconcile': True})
        # Tạo picking nhập lại hàng
        for line in self.lines:
            if line.product_id.product_tmpl_id.type == 'product':
                line.update({'x_qty': line.qty})
                debit_good_obj = self.env['pos.debit.good.line'].search([('product_id', '=', line.product_id.id), ('order_id', '=', self.x_pos_partner_refund_id.id)])
                count_debit_product = 0 #đếm số lượng hàng còn nợ trên đơn hàng
                count_product_order = 0 #đếm số lượng hàng trên đơn hàng
                for i in debit_good_obj:
                    count_debit_product +=i.qty_debit
                if abs(line.qty) <= count_debit_product:
                    line.update({'x_qty': line.qty})
                    line.update({'qty': 0})
                else:
                    line.qty += count_debit_product
        self.create_picking()
        for line in self.lines:
            if line.product_id.product_tmpl_id.type == 'product':
                debit_good_obj = self.env['pos.debit.good.line'].search([('product_id', '=', line.product_id.id), ('order_id', '=', self.x_pos_partner_refund_id.id)])
                debit_master = debit_good_obj.debit_id
                count_debit_product = 0 #đếm số lượng hàng còn nợ trên đơn hàng
                count_product_order = 0 #đếm số lượng hàng trên đơn hàng
                for i in debit_good_obj:
                    count_debit_product +=i.qty_debit
                line.update({'qty': line.x_qty})
                x_total_qty = line.x_qty
                debit_good_line_obj = self.env['pos.debit.good.line'].search([('order_id', '=', self.x_pos_partner_refund_id.id)])
                for x in debit_good_line_obj:
                    if x.product_id.id == line.product_id.id:
                        x_total_qty = x.qty_depot
                line.update({'x_qty': -x_total_qty})
                line.x_quantity_refund += abs(line.qty)
                if abs(line.qty) >= debit_good_obj.qty_debit:
                    debit_good_obj.unlink()
                else:
                    debit_good_obj.qty -= abs(line.qty)
                    debit_good_obj.qty_debit = debit_good_obj.qty - debit_good_obj.qty_depot

        # DebitLine = self.env['pos.debit.good.line']
        # debit_line = DebitLine.search([('order_id', '=', self.x_pos_partner_refund_id.id)], limit=1)
        # debit_line.unlink()
                if debit_master:
                    i = 0
                    for dbl in debit_master.line_ids:
                        if dbl.qty_debit == 0:
                            i = i + 1
                    if i == len(debit_master.line_ids):
                        debit_master.state = 'done'

                # pos_order_line = self.env['pos.order.line'].search([('product_id', '=', line.product_id.id), ('order_id', '=', self.id)])
                # for i in pos_order_line:
                #     count_product_order += i.qty
                #
                # if count_debit_product < abs(count_product_order):
                #     raise except_orm("Cảnh báo!", ("Còn nợ hàng. Bạn phải xuất hàng cho khách hàng trước khi refund"))

        # picking = self.env['stock.picking']
        # for line in self.x_pos_partner_refund_id.picking_id:
        #     if line.state != 'done':
        #         picking = line
        #         break
        # for line in self.lines:
        #     for tmp in picking.move_lines:
        #         if line.product_id.id == tmp.product_id.id:
        #             if -line.qty < tmp.product_uom_qty:
        #                 raise except_orm("Cảnh báo!",
        #                                  ("Bạn còn nợ hàng khách hàng. Vui lòng xuất hàng trước khi refund"))
        # count_picking = 0
        # count_picking_done = 0
        # for line in self.x_pos_partner_refund_id:
        #     for tmp in line.picking_id:
        #         if tmp.state != 'done':
        #             tmp.state = 'cancel'
                #     count_picking += 1
                # else:
                #     count_picking_done += 1
        # if count_picking == 0:
        #     self.create_picking()
        # else:
        # if count_picking_done != 0:
        # for line in self.x_pos_partner_refund_id.picking_id:
        #     if line.state != 'done':
        #         for tmp in line.move_lines:
        #             for i in self.lines:
        #                 if i.product_id.id == tmp.product_id.id:
        #                     i.qty += tmp.product_uom_qty
        #                     i.x_qty = 0
        # self.create_picking()
        # for line in self.x_pos_partner_refund_id.picking_id:
        #     if line.state != 'done':
        #         for tmp in line.move_lines:
        #             for i in self.lines:
        #                 if i.product_id.id == tmp.product_id.id:
        #                     i.qty -= tmp.product_uom_qty
        # Chuyển trạng thái của lần sử dụng dịch vụ lẻ khi refund xong đơn hàng
        # if self.x_type == '3':
        #     using_service = self.env['izi.service.card.using'].search([('pos_order_id', '=', self.x_pos_partner_refund_id.id)])
        #     using_service.state = 'cancel'
        # SangsLA thêm ngày 3/10/2018 Thêm order vào form khi chung của khách hàng
        pos_sum_digital_obj = self.env['pos.sum.digital.sign'].search(
            [('partner_id', '=', self.partner_id.id), ('state', '=', 'draft'), ('session_id', '=', self.session_id.id)])
        if pos_sum_digital_obj:
            self.update({'x_digital_sign_id': pos_sum_digital_obj.id})
        else:
            pos_sum_digital_obj = self.env['pos.sum.digital.sign'].create({
                'partner_id': self.partner_id.id,
                'state': 'draft',
                'date': my_date.today(),
                'session_id': self.session_id.id,
            })
            self.update({'x_digital_sign_id': pos_sum_digital_obj.id})
        for line in self.lines:
            line.update({'x_digital_sign_id': pos_sum_digital_obj.id})
        for line in self.statement_ids:
            line.update({'x_digital_sign_id': pos_sum_digital_obj.id})
    #         heets


    @api.multi
    def action_customer_signature(self):
        if self.state != 'customer_comment':
            raise except_orm("Cảnh báo!", 'Trạng thái của đơn hàng đã thay đổi. Vui lòng load lại trang hoặc F5')
        Debit = self.env['pos.debit.good']
        DebitLine = self.env['pos.debit.good.line']
        if self.x_pos_partner_refund_id ==False:
            for line in self.picking_id:
                # if line.state not in ['done','cancel']:
                #     raise except_orm("Cảnh báo!", ("Xác nhận đơn xuất kho %s trước khi ký xác nhận!" % (str(line.name))))
                # else:
                if line.state == 'cancel' and self.x_type == '1' and self.x_active_pick == False:
                    for line_order in self.lines:
                        move_cancel = self.env['stock.move'].search([('picking_id','=',line.id),('state','=','cancel'),('product_id','=',line_order.product_id.id)])
                        for move_cancel_line in move_cancel:
                            line_order.x_qty -= move_cancel_line.product_uom_qty
                            db = Debit.search([('partner_id', '=', self.partner_id.id)], limit=1)
                            if db.id != False:
                                debit_line = DebitLine.search([('order_id', '=', self.id),('product_id','=',line.product_id.id)])
                                if debit_line.id !=False:
                                    debit_line.qty_debit = line_order.qty
                                    debit_line.qty_depot = 0
                                    if db.state == 'done':
                                        db.state = 'debit'
                                else:
                                    debit_vals_line = {
                                        'order_id': self.id,
                                        'product_id': line_order.product_id.id,
                                        'qty': abs(line_order.qty),
                                        'qty_depot': abs(line_order.x_qty),
                                        'qty_debit': abs(line_order.qty) - abs(line_order.x_qty),
                                        # 'amount_payment': , chưa thme vi chua lam thanh toan chi tiet tung dong
                                        'date': self.date_order,
                                        'debit_id': db.id,
                                    }
                                    DebitLine.create(debit_vals_line)
                            else:
                                debit_vals = {
                                    'partner_id': self.partner_id.id,
                                    'code': self.partner_id.x_code,
                                    'old_code': self.partner_id.x_old_code,
                                    'phone': self.partner_id.phone,
                                    'mobile': self.partner_id.mobile,
                                    'state': 'debit',
                                }
                                debit_id = Debit.create(debit_vals)
                                debit_vals_line = {
                                    'order_id': self.id,
                                    'product_id': line_order.product_id.id,
                                    'qty': abs(line_order.qty),
                                    'qty_depot': abs(line_order.x_qty),
                                    'qty_debit': abs(line_order.qty) - abs(line_order.x_qty),
                                    # 'amount_payment': , chưa thme vi chua lam thanh toan chi tiet tung dong
                                    'date': self.date_order,
                                    'debit_id': debit_id.id,
                                }
                                DebitLine.create(debit_vals_line)
                self.x_active_pick = True
        # else:
        #     for line in self.picking_id:
        #         if line.state != 'done':
        #             raise except_orm("Cảnh báo!", ("Xác nhận đơn xuất kho %s trước khi ký xác nhận!" % (str(line.name))))
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
        # view = self.env.ref('izi_pos_custom_backend.view_pop_up_signature_customer')
        # return {
        #     'name': _('Sign Customer?'),
        #     'type': 'ir.actions.act_window',
        #     'view_type': 'form',
        #     'view_mode': 'form',
        #     'res_model': 'pos.order',
        #     'views': [(view.id, 'form')],
        #     'view_id': view.id,
        #     'target': 'new',
        #     'res_id': self.id,
        #     'context': self.env.context,
        # }

    @api.multi
    def action_setting_picking(self):
        for line in self.picking_id:
            if line.state == 'cancel' and self.x_type == '1':
                line.state = 'draft'
                for line_move in line.move_lines:
                    line_move.state = 'draft'

    @api.multi
    def process_customer_signature(self):
        # Lấy tổng tiền ảo của KH
        vm_amount = self.env['pos.virtual.money'].get_available_amount_by_partner(self.partner_id.id)

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
                if stt.journal_id.code.upper() == 'VM':
                    vm_amount -= stt.amount
                if stt.journal_id.id == self.session_id.config_id.journal_deposit_id.id:
                    deposit_lines = self.env['pos.customer.deposit'].search(
                        [('partner_id', '=', self.partner_id.id)])
                    total = 0.0
                    for line in deposit_lines:
                        total += line.residual
                    if total < stt.amount:
                        raise UserError("Tài khoản đặt cọc của khách hàng không đủ %s để thanh toán" % stt.amount)
            # Ghi nhận doanh thu
            if loyal_total > 0:
                self.x_total_order = loyal_total
                # tiennq them quy doi diem tich luy
                # point = self._get_loyal_total(loyal_total)
                ####
                self.x_loyal_id = revenue.id
                # self_to_update['x_point_bonus'] = point
                # self_to_update['x_point_total'] = point + self.partner_id.x_point_total
                self.x_loyal_total = loyal_total + self.partner_id.x_loyal_total
                # CuuNV Fix 09/07: Thêm tổng tích điểm cho KH
                self.partner_id.update({'x_loyal_total': self.partner_id.x_loyal_total + loyal_total})
                # SangLA 15/08/2018: Thêm điểm thưởng cho người giới thiệu khách hàng
                # order_len = self.env['pos.order'].search([('partner_id', '=', self.partner_id.id)])
                # if len(order_len) == 1 and self.partner_id.x_presenter:
                #     self.partner_id.x_presenter.update(
                #         {'x_point_total': (point + self.partner_id.x_presenter.x_point_total)})
                #     point_history = self.env['izi.vip.point.history'].create({
                #         'partner_id': self.partner_id.x_presenter.id,
                #         'order_id': self.id,
                #         'date': my_date.today(),
                #         'point': point,
                #     })
        if vm_amount < 0:
            raise except_orm("Thông báo!", ("Bạn không đủ số tiền để thanh toán thẻ tiền. Vui lòng kiểm tra lại"))
        # if not self.x_signature_image:
        #     raise except_orm('Cảnh báo!', 'Bạn cần phải ký để xác nhận!')
        # Send message về cho tư vấn co user về khách hàng thanh toán
        # self = self.sudo()
        # partner_ids = []
        # if self.x_user_id:
        #     for line in self.x_user_id:
        #         if line.user_id.partner_id:
        #             partner_ids.append(line.user_id.partner_id)
        # if self.partner_id.x_manage_user_id:
        #     if self.partner_id.x_manage_user_id.partner_id and (
        #             self.partner_id.x_manage_user_id.partner_id not in partner_ids):
        #         partner_ids.append(self.partner_id.x_manage_user_id.partner_id)
        # journal_loyal_id = self.session_id.config_id.journal_loyal_ids.ids if self.session_id.config_id.journal_loyal_ids else False
        # for partner in partner_ids:
        #     odoobot_id = self.env['ir.model.data'].xmlid_to_res_id("base.partner_root")
        #     channel = self.env['mail.channel.payment'].search([('partner_id', '=', partner.id)])
        #     if channel:
        #         for x in self.statement_ids:
        #             if journal_loyal_id:
        #                 if x.journal_id.id not in journal_loyal_id:
        #                     continue
        #             message = ''
        #             if x.amount >= 0:
        #                 message = _(
        #                     "<br/>Ngày %s khách hàng %s thanh toán cho đơn hàng %s với số tiền là %s với hình thức là %s</b>" % (
        #                         my_date.today().strftime("%d-%m-%Y"), self.partner_id.name, self.name,
        #                         self.convert_numbers_to_text_sangla(x.amount),
        #                         x.journal_id.name))
        #             else:
        #                 message = _(
        #                     "<br/>Ngày %s khách hàng %s thanh toán cho đơn hàng %s với số tiền là - %s với hình thức là %s</b>" % (
        #                         my_date.today().strftime("%d-%m-%Y"), self.partner_id.name, self.name,
        #                         self.convert_numbers_to_text_sangla(x.amount),
        #                         x.journal_id.name))
        #             channel.mail_channel_id.sudo().message_post(body=message, author_id=odoobot_id,
        #                                                         message_type="comment",
        #                                                         subtype="mail.mt_comment")
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
        #         for x in self.statement_ids:
        #             if journal_loyal_id:
        #                 if x.journal_id.id not in journal_loyal_id:
        #                     continue
        #             message = ''
        #             if x.amount >= 0:
        #                 message = _(
        #                     "<br/>Ngày %s khách hàng %s thanh toán  cho đơn hàng %s với số tiền là %s với hình thức là %s</b>" % (
        #                         my_date.today().strftime("%d-%m-%Y"), self.partner_id.name, self.name,
        #                         self.convert_numbers_to_text_sangla(x.amount),
        #                         x.journal_id.name))
        #             else:
        #                 message = _(
        #                     "<br/>Ngày %s khách hàng %s thanh toán  cho đơn hàng %s với số tiền là - %s với hình thức là %s</b>" % (
        #                         my_date.today().strftime("%d-%m-%Y"), self.partner_id.name, self.name,
        #                         self.convert_numbers_to_text_sangla(x.amount),
        #                         x.journal_id.name))
        #             channel.sudo().message_post(body=message, author_id=odoobot_id, message_type="comment",
        #                                         subtype="mail.mt_comment")
        # self.env.user.odoobot_state = 'onboarding_emoji'
        if self.state == 'paid' or self.state == 'invoiced':
            raise except_orm("Cảnh báo!", ("Trạng thái của đơn hàng đã thay đổi. Vui lòng F5 hoặc load lại trang"))
        # if self.x_debt:
        #     self.state = 'invoiced'
        # else:
        #     self.state = 'paid'
        # if self.x_pos_partner_refund_id.id == False:
        #     if self.x_debt:
        # if not self.invoice_id:
        #     self.create_invoice()
        if self.x_pos_partner_refund_id:
            self.state = 'invoiced'
        else:
            self.state = 'to_confirm'
        return {'type': 'ir.actions.act_window_close'}

    # @api.multi
    # def _get_loyal_total(self, loyal_total):
    #     config_id = self.session_id.config_id.id
    #     loy = self.env['izi.vip.config'].search(
    #         [('config_id', '=', config_id), ('to_date', '>=', self.date_order), ('active', '=', True),
    #          ('from_date', '<=', self.date_order), ('type', '=', 'accumulation')],
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

    @api.multi
    def action_send_payment(self):
        if not self.lines:
            raise except_orm("Cảnh báo!", ('Đơn hàng bán đang không có sản phẩm hoặc dịch vụ'))
        if self.x_type == '3': #Đơn hàng của đơn dịch vụ
            raise except_orm('Thông báo', 'Đơn hàng được sinh ra từ các đơn dịch vụ, vui lòng không thao tác ở đây!')

        if self.x_pos_partner_refund_id:
            self.state = 'to_payment'
        have_service = False
        have_card_service = False
        approve_price = False
        msg = []
        for line in self.lines:
            '''
            ** Dự án Amia không sử dụng chức năng bán dưới giá 29/11/2019 **
            price = self.pricelist_id.get_product_price(line.product_id, line.qty or 1.0, self.partner_id)
            if line.price_unit < price and line.x_custom_discount == False:
                approve_price = True
                msg.append('Dịch vụ %s ' % (line.product_id.name))
                msg.append('Giá niêm yết %r ' % self.convert_numbers_to_text_sangla(price))
                msg.append('Giá bán %r ' % self.convert_numbers_to_text_sangla(line.price_unit))
                msg.append('Dưới mức giá bán tối thiểu cần phê duyêt. ')
            if line.x_custom_discount == False and line.discount > 0 and line.price_unit * (100-line.discount) /100 < price :
                approve_price = True
                msg.append('Dịch vụ %s ' % (line.product_id.name))
                msg.append('Giá niêm yết %r ' % self.convert_numbers_to_text_sangla(price))
                msg.append('Nhập chiết khấu %r phần trăm ' % self.convert_numbers_to_text_sangla(line.discount))
                msg.append('Giá bán %r ' % self.convert_numbers_to_text_sangla(line.price_unit * (100 - line.discount )/100))
                msg.append('Dưới mức giá bán tối thiểu cần phê duyêt.')
            if line.x_custom_discount == False and line.x_discount > 0 and line.price_unit * line.qty - line.x_discount < price :
                approve_price = True
                msg.append('Dịch vụ %s ' % (line.product_id.name))
                msg.append('Tổng giá niêm yết %r ' % self.convert_numbers_to_text_sangla(price * line.qty))
                msg.append('Nhập giảm giá  %r tiền' % self.convert_numbers_to_text_sangla(line.x_discount))
                msg.append('Giá bán %r ' % self.convert_numbers_to_text_sangla(line.price_unit * line.qty - line.x_discount))
                msg.append('Dưới mức giá bán tối thiểu cần phê duyêt. ')'''
            if line.product_id.type == 'service' and line.product_id.x_type_card == 'none' and self.x_type != '2':
                have_service = True
            if line.product_id.default_code == 'TDV':
                have_card_service = True

        if have_service and not have_card_service:
            self._add_service_to_service_card()
        if approve_price:
            # do nothing
            '''
            ** Dự án Amia không sử dụng chức năng bán dưới giá 29/11/2019 **
            self.state = 'to_approve'
            #Ngoant NT thêm thông báo bán dưới giá tối thiểu
            values = {'state': 'to_approve'}
            # Thông báo quản lý phê duyệt
            values['message_follower_ids'] = []
            users = self.env['res.users'].search([
                ('groups_id', 'in', self.env.ref('point_of_sale.group_pos_manager').id),
                ('id', '!=', self._uid)])
            MailFollowers = self.env['mail.followers']
            follower_partner_ids = []
            for m in self.message_follower_ids:
                follower_partner_ids.append(m.partner_id.id)
            for user in users:
                if user.x_pos_config_id.id == self.config_id.id and \
                        user.partner_id.id and user.partner_id.id not in follower_partner_ids:
                    values['message_follower_ids'] += \
                        MailFollowers._add_follower_command(self._name, [], {user.partner_id.id: None}, {})[0]
                # if user.x_pos_config_id.id == self.config_id.id:
                #     self.schedule_activity(msg, user.id, self.date_order, self.id)
            self.write(values)
            self.message_post(subtype='mt_activities',
                               body=" %s !" % (' ' + ', '.join(msg) if len(msg) else ''))
            return {'type': 'ir.actions.act_window_close'}'''
        else:
            if self.amount_total:
                self.state = 'to_payment'
            else:
                self.action_pos_order_paid()
                self.state = 'customer_comment'


    #lấy ngẫu nhiên service card trong kho của người bán
    def _get_service_card(self):
        ProductionLotObj = self.env['stock.production.lot']
        ProductObj = self.env['product.product']

        code_product_service_card = 'TDV'
        product = ProductObj.search([('default_code', '=', code_product_service_card)], limit=1)
        if not product: raise except_orm('Thông báo', 'Chưa có sản phẩm là Thẻ dịch vụ[%s]. Vui lòng cấu hình trước khi bán dịch vụ.' % (str(code_product_service_card)))

        if not self.session_id.config_id.x_card_picking_type_id: raise except_orm('Thông báo', 'Chưa cấu hình loại dịch chuyển của thẻ dịch vụ cho điểm bán hàng %s.' % (self.session_id.config_id.name, ))
        if not self.session_id.config_id.x_card_picking_type_id.default_location_src_id: raise except_orm('Thông báo', 'Loại dịch chuyển của thẻ dịch vụ của điểm bán hàng %s chưa chọn địa điểm nguồn mặc định.' % (self.session_id.config_id.name, ))
        location = self.session_id.config_id.x_card_picking_type_id.default_location_src_id

        query = ''' SELECT a.id FROM stock_production_lot a, izi_product_release b
                    WHERE a.x_release_id = b.id and b.product_id = %s AND b.location_id = %s
                    AND b.state = %s AND a.x_status = %s AND
                    ((a.life_date is not null and a.life_date >= now()) OR a.life_date is null) 
                    and not exists (select 1 from pos_order_line where lot_name = a.name)
                    ORDER BY a.create_date LIMIT 1 for update nowait'''
        print(query % (product.id, location.id, 'done', 'actived', ) )
        self._cr.execute(query , (product.id, location.id, 'done', 'actived', ))
        res = self._cr.dictfetchone()
        if not res: raise except_orm('Thông báo', 'Đã hết thẻ dịch vụ trong kho [%s]%s. Liên hệ quản lý để phát hành thêm trước khi bán.' % (str(location.x_code), str(location.name), ))
        service_card = ProductionLotObj.search([('id', '=', res['id'])])
        service_card.update({'x_status': 'using'})

        return service_card

    #Thêm dịch vụ vào thẻ dịch vụ
    def _add_service_to_service_card(self):
        PosOrderLineObj = self.env['pos.order.line']
        PosPackProductionLotObj = self.env['pos.pack.operation.lot']
        service_card = self._get_service_card()
        argvs = {
            'product_id': service_card.product_id.id,
            'name': self.name,
            'price_unit': service_card.product_id.list_price,
            'qty': 1,
            'x_qty': 1,
            'discount': 0,
            'price_subtotal': service_card.product_id.list_price,
            'lot_name': service_card.name.upper().strip(),
            'order_id': self.id,
        }
        check_lot = PosOrderLineObj.search([('lot_name', '=', service_card.name.upper().strip())])
        if len(check_lot) != 0:
            raise except_orm('Cảnh báo!', (('Mã %s đang được gắn ở đơn hàng: ' + str(
                check_lot[0].order_id.name)) % service_card.name.upper().strip()))
        line_id = PosOrderLineObj.create(argvs)
        argvs_lot = {
            'pos_order_line_id': line_id.id,
            'lot_name': service_card.name.upper().strip(),
        }
        PosPackProductionLotObj.create(argvs_lot)

    def check_therapy_record(self):
        return False

