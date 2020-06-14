# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from datetime import datetime, date
from odoo.exceptions import except_orm, ValidationError, UserError


class ExchangeService(models.Model):
    _name = 'izi.pos.exchange.service'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    @api.model
    def default_get(self, fields):
        res = super(ExchangeService, self).default_get(fields)
        user_id = self.env['res.users'].search([('id', '=', self.env.uid)], limit=1)
        config_id = user_id.x_pos_config_id.id
        current_session = self.env['pos.session'].search([('state', '!=', 'closed'), ('config_id', '=', config_id)],
                                                         limit=1)
        if not current_session:
            raise except_orm(("Thông báo"), ('Bạn phải mở phiên trước khi tạo đơn hàng mới.'))
        return res

    def _default_session(self):
        user_id = self.env['res.users'].search([('id', '=', self.env.uid)], limit=1)
        config_id = user_id.x_pos_config_id.id
        return self.env['pos.session'].search([('state', '=', 'opened'), ('config_id', '=', config_id)], limit=1)

    def _default_pricelist(self):
        return self._default_session().config_id.pricelist_id

    session_id = fields.Many2one(
        'pos.session', string='Session', required=True, index=True,
        readonly=True, default=_default_session, track_visibility='onchange')

    name = fields.Char("Name", default="/", copy=False, track_visibility='onchange')
    state = fields.Selection(
        selection=(('draft', 'Draft'), ('to_confirm', 'To Confirm'), ('to_payment', 'To payment'),
                   ('paid', 'Paid'), ('customer_comment', 'Customer Comment'), ('done', 'Done'), ('to_refund', 'To refund'),
                   ('wait_refund', 'Wait refund'), ('refunded', 'Refunded'), ('cancel', 'Cancel')),
        default='draft', track_visibility='onchange')
    note = fields.Text("Note", track_visibility='onchange')
    exchange_date = fields.Datetime("Exchange date", required=True, default=fields.Datetime.now, track_visibility='onchange')
    partner_id = fields.Many2one('res.partner', string='Customer', track_visibility='onchange')
    pricelist_id = fields.Many2one('product.pricelist', string='Pricelist', required=True, readonly=True,
                                   default=_default_pricelist, track_visibility='onchange')
    product_lot_id = fields.Many2one('stock.production.lot', 'Serial', track_visibility='onchange')
    pos_order_id = fields.Many2one('pos.order', 'Order', track_visibility='onchange')
    pos_rf_order_id = fields.Many2one('pos.order', 'Order Refund', track_visibility='onchange')

    serial = fields.Char("Code Card", required=True, track_visibility='onchange')
    current_detail_line_ids = fields.One2many('izi.current.exchange.service', 'exchange_id', 'Curent exchange')
    new_service_detail_line_ids = fields.One2many('izi.new.exchange.service', 'exchange_id', 'New exchange')
    amount_current = fields.Float(compute='_compute_amount_line_all', string='Amount Current')
    amount_new = fields.Float(compute='_compute_amount_line_all', string='Amount New')
    amount_total = fields.Float(compute='_compute_amount_line_all', string='Amount Total')
    statement_ids = fields.One2many('account.bank.statement.line', 'x_exchange_id', string='Payments', readonly=True)

    signature_image = fields.Binary("Signature Image", default=False, track_visibility='onchange')
    partner_id = fields.Many2one('res.partner', string="Partner")

    @api.model
    def create(self, vals):
        if vals.get('name', _('New')) == _('New'):
            vals['name'] = self.env['ir.sequence'].next_by_code('izi.pos.exchange.service') or _('New')
        return super(ExchangeService, self).create(vals)

    @api.depends('current_detail_line_ids.amount_subtract', 'new_service_detail_line_ids.amount_total')
    def _compute_amount_line_all(self):
        for exchange_service in self:
            exchange_service.amount_current = sum(current.amount_subtract for current in exchange_service.current_detail_line_ids)
            exchange_service.amount_new = sum(new.amount_total for new in exchange_service.new_service_detail_line_ids)
            a = exchange_service.amount_new - exchange_service.amount_current
            exchange_service.amount_total = a
            return a

    @api.multi
    def check_card(self):
        for line in self.current_detail_line_ids:
            line.unlink()
        PosOrderLine = self.env['pos.order.line']
        serial = self.serial.upper().strip()
        lot_obj = self.env['stock.production.lot'].search([('name', '=', serial)])
        if not lot_obj:
            raise except_orm('Thông báo', ('Thẻ có mã "%s" không tồn tại trong hệ thống!' % serial))
        elif lot_obj.x_status != 'using':
            status_lot = {'new': 'Mới', 'actived': 'Kích hoạt', 'used': 'Đã sử dụng', 'destroy': 'Hủy'}
            raise except_orm('Thông báo', 'Thẻ %s đang ở trạng thái %s. Chỉ đổi thẻ ở trạng thái Đang sử dụng.' % (str(lot_obj.name), str(lot_obj.x_status in status_lot and status_lot[lot_obj.x_status] or lot_obj.x_status), ))
        else:
            exchange = self.env['izi.pos.exchange.service'].search(
                [('product_lot_id', '=', lot_obj.id), ('state', 'in', ('draft', 'to_confirm', 'to_payment', 'paid'))])
            if len(exchange) > 1:
                raise except_orm('Thông báo', ('Thẻ có mã "%s" đang chờ thực thi ở đơn đổi khác!' % serial))
            if lot_obj.x_status == 'used':
                raise except_orm('Thông báo', ('Thẻ có mã "%s" đã sử dụng hết!' % serial))
            if lot_obj.life_date < self.exchange_date:
                raise except_orm('Thông báo', (('Thẻ có mã "%s" đã hết hạn vào ngày: ' + datetime.strptime(
                    lot_obj.life_date, "%Y-%m-%d %H:%M:%S").strftime("%d-%m-%Y")) % serial))
            if lot_obj.x_status == 'using':
                lines_lot = []
                for detail in lot_obj.x_card_detail_ids:
                    if detail.state == 'ready':
                        argvs = {
                            'card_id': detail.id,
                            'service_id': detail.product_id.id,
                            'price_unit': detail.price_unit,
                            'total_count': detail.total_qty,
                            'hand_count': detail.qty_hand,
                            'used_count': detail.qty_use,
                            'amount_total': detail.amount_total,
                            'to_subtract_count': 0,
                            'exchange_id': self.id,
                        }
                        lines_lot.append(argvs)
                self.current_detail_line_ids = lines_lot
                order = PosOrderLine.search([('lot_name', '=', lot_obj.name)])
                self.partner_id = lot_obj.x_customer_id.id
                self.product_lot_id = lot_obj.id
        return True

    @api.multi
    def action_send(self):
        if self.state != 'draft':
            return True
        self.action_compute(check=False)
        self.state = 'to_confirm'

    @api.multi
    def action_compute(self, check=True):
        if self.state != 'draft':
            raise except_orm('Thông báo', ("Trạng thái sử dụng dịch vụ đã thay đổi. Vui lòng F5 hoặc load lại trang"))
        self.state = 'to_confirm'
        for line in self.current_detail_line_ids:
            if line.to_subtract_count == 0:
                line.unlink()
            else:
                if (line.total_count - line.used_count) < line.to_subtract_count:
                    raise except_orm('Thông báo', ('Bạn đã nhập số lượng đổi lớn hơn số lượng được phép!'))
        if len(self.current_detail_line_ids) == 0:
            raise except_orm('Thông báo', ('Bạn chưa có dịch vụ đổi.'))
        for line in self.new_service_detail_line_ids:
            if line.new_count == 0:
                line.unlink()
        if len(self.new_service_detail_line_ids) == 0:
            raise except_orm('Thông báo', ('Bạn chưa nhập dịch vụ muốn đổi.'))
        for line in self.current_detail_line_ids:
            for new_line in self.new_service_detail_line_ids:
                if line.service_id.id == new_line.service_id.id:
                    raise except_orm('Thông báo', ('Bạn đã nhập dịch vụ muốn đổi trùng với dịch vụ đổi!'))
        if check == False:
            return True
        else:
            exchange = self._compute_amount_line_all()
            if exchange > 0:
                raise except_orm('Thông báo',
                                 ('Tổng giá trị dịch vụ muốn đổi lớn hơn tổng giá trị dịch vụ đổi. \n'
                                  'Số tiền phải thanh toán trong lần đổi này là: %s đ' % str("{:,}".format(exchange))))
            else:
                raise except_orm('Thông báo',
                                 ('Tổng giá trị dịch vụ muốn đổi nhỏ hơn hoặc bằng tổng giá trị dịch vụ đổi. \n'
                                  'Giá trị của dịch vụ trong thẻ giảm đi: %s đ' % str("{:,}".format(-exchange))))

    @api.multi
    def unlink(self):
        for line in self:
            if line.state != 'draft':
                raise except_orm('Thông báo!', (
                    "Không thể xóa bản ghi ở trạng thái khác bản thảo"))
        return super(ExchangeService, self).unlink()

    @api.one
    def action_cancel(self):
        if self.state in ('to_refund','wait_refund'):
            self.state = 'done'
        if self.state in ('to_confirm', 'to_payment'):
            self.state = 'cancel'

    @api.multi
    def action_confirm(self):
        if self.state != 'to_confirm':
            return True
        if self.amount_total > 0:
            self.state = 'to_payment'
        else:
            self.state = 'customer_comment'

    @api.multi
    def action_exchange(self):
        if self.state != 'customer_comment':
            return True
        a = self._compute_amount_line_all()
        self.product_lot_id.x_amount = self.product_lot_id.x_amount + a
        for line in self.current_detail_line_ids:
            line.card_id.qty_hand = line.card_id.qty_hand - line.to_subtract_count
            line.card_id.qty_use = line.card_id.qty_use + line.to_subtract_count
            if line.card_id.amount_total - (line.card_id.qty_use * line.card_id.price_unit) > 0:
                line.card_id.remain_amount = line.card_id.amount_total - (line.card_id.qty_use * line.card_id.price_unit)
            else:
                line.card_id.remain_amount = 0
            # line.card_id.amount_total = line.card_id.total_qty * line.card_id.price_unit
        list = []
        for line in self.product_lot_id.x_card_detail_ids:
            list.append(line.product_id.id)
        for new_line in self.new_service_detail_line_ids:
            if new_line.service_id.id == self.session_id.config_id.x_charge_refund_id.id:
                continue
            if new_line.service_id.id in list:
                for line in self.product_lot_id.x_card_detail_ids:
                    if new_line.service_id.id == line.product_id.id:
                        line.total_qty = line.total_qty + new_line.new_count
                        line.qty_hand = line.qty_hand + new_line.new_count
                        line.amount_total = line.total_qty * line.price_unit
                        line.remain_amount = (line.total_qty - line.qty_use) * line.price_unit
            else:
                argvs = {
                    'lot_id': self.product_lot_id.id,
                    'product_id': new_line.service_id.id,
                    'total_qty': new_line.new_count,
                    'qty_hand': new_line.new_count,
                    'qty_use': 0,
                    'price_unit': new_line.price_unit,
                    'remain_amount': new_line.price_unit * new_line.new_count,
                    'amount_total': new_line.price_unit * new_line.new_count,
                }
                card_detail = self.env['izi.service.card.detail'].create(argvs)
        if self.pos_order_id:
            self.pos_order_id.action_order_complete()
            self.pos_order_id.create_invoice()
        # self.state = 'customer_comment'
        # SangsLA thêm ngày 3/10/2018 Thêm using_service vào form khi chung của khách hàng
        pos_sum_digital_obj = self.env['pos.sum.digital.sign'].search(
            [('partner_id', '=', self.partner_id.id), ('state', '=', 'draft'), ('session_id', '=', self.session_id.id)])
        if pos_sum_digital_obj:
            self.update({'x_digital_sign_id': pos_sum_digital_obj.id})
        else:
            pos_sum_digital_id = self.env['pos.sum.digital.sign'].create({
                'partner_id': self.partner_id.id,
                'state': 'draft',
                'date': date.today(),
                'session_id': self.session_id.id,
            })
            self.update({'x_digital_sign_id': pos_sum_digital_id.id})
        #         hết

    @api.multi
    def action_customer_signature(self):
        view = self.env.ref('izi_pos_exchange_service.izi_exchange_view_pop_up_rate_service')
        return {
            'name': _('Rate Service?'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'izi.pos.exchange.service',
            'views': [(view.id, 'form')],
            'view_id': view.id,
            'target': 'new',
            'res_id': self.id,
            'context': self.env.context,
        }

    @api.multi
    def action_payment(self):
        UserObj = self.env['res.users']
        user = UserObj.search([('id', '=', self._uid)])
        if not self.pos_order_id:
            param_obj = self.env['ir.config_parameter']
            code = param_obj.get_param('default_code_exception')
            if code == False:
                raise ValidationError(
                    _(u"Bạn chưa cấu hình thông số hệ thống cho phí đổi dịch vụ default_code_exception. Xin hãy liên hệ với người quản trị."))
            product_id = self.env['product.product'].search([('default_code', '=', 'PDDV')], limit=1)
            if product_id.id == False:
                raise ValidationError(_(u"Bạn chưa cấu hình sản phẩm cho phí đổi dịch vụ."))
            PosOrder = self.env['pos.order']
            argv = {
                'session_id': self.session_id.id,
                'partner_id': self.partner_id.id,
                'branch_id': user.branch_id.id,
                'x_type': '5',
            }
            order_id = PosOrder.create(argv)
            line = {
                'product_id': product_id.id,
                'qty': 1,
                'price_unit': self.amount_total,
                'order_id': order_id.id,
            }
            self.env['pos.order.line'].create(line)
            self.pos_order_id = order_id.id
        ctx = self.env.context.copy()
        ctx.update({'active_id': self.pos_order_id.id, 'exchange_id': self.id})
        view = self.env.ref('izi_pos_custom_backend.izi_view_pos_payment_pos_order')
        return {
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'pos.make.payment',
            'views': [(view.id, 'form')],
            'view_id': view.id,
            'target': 'new',
            'context': ctx,
        }

    @api.multi
    def action_to_refund(self):
        for new_line in self.new_service_detail_line_ids:
            for line in self.product_lot_id.x_card_detail_ids:
                if new_line.service_id.id == line.product_id.id and line.qty_hand < new_line.new_count:
                    raise except_orm('Thông báo!', (
                        "Số tồn của dịch vụ muốn đổi nhỏ hơn số lượng trong đơn đổi. Đơn đổi không được hoàn tác!"))
        self.state = 'to_refund'

    @api.multi
    def action_confirm_refund(self):
        if self.state != 'to_refund':
            return True
        self.state = 'wait_refund'

    @api.multi
    def action_refund(self):
        if self.state != 'wait_refund':
            return True
        if self.product_lot_id.life_date < self.write_date:
            raise except_orm('Thông báo', ('Thẻ đã hết hạn'))
        if not self.pos_order_id:
            return self.get_refund()
        if self.pos_order_id and not self.pos_rf_order_id:
            self.pos_order_id.refund()
            pos_rf = self.env['pos.order'].search([('x_pos_partner_refund_id', '=', self.pos_order_id.id)],limit=1)
            self.pos_rf_order_id = pos_rf.id
        view = self.env.ref('point_of_sale.view_pos_pos_form')
        return {
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'pos.order',
            'views': [(view.id, 'form')],
            'view_id': view.id,
            'res_id': self.pos_rf_order_id.id,
            'context': self.env.context,
        }


    def get_refund(self):
        a = self._compute_amount_line_all()
        self.product_lot_id.x_amount = self.product_lot_id.x_amount - a
        for new_line in self.new_service_detail_line_ids:
            for line in self.product_lot_id.x_card_detail_ids:
                if new_line.service_id.id == line.product_id.id and line.qty_hand < new_line.new_count:
                    raise except_orm('Thông báo!', (
                        "Số tồn của dịch vụ muốn đổi nhỏ hơn số lượng trong đơn đổi. Đơn đổi không được hoàn tác!"))
        for line in self.current_detail_line_ids:
            line.card_id.qty_hand = line.card_id.qty_hand + line.to_subtract_count
            line.card_id.qty_use = line.card_id.qty_use - line.to_subtract_count
            if line.card_id.amount_total- (line.card_id.qty_use * line.card_id.price_unit) > 0:
                line.card_id.remain_amount = line.card_id.amount_total- (line.card_id.qty_use * line.card_id.price_unit)
            else:
                line.card_id.remain_amount = 0
            # line.card_id.amount_total = line.card_id.total_qty * line.card_id.price_unit
        for new_line in self.new_service_detail_line_ids:
            if new_line.service_id.id == self.session_id.config_id.x_charge_refund_id.id:
                continue
            for line in self.product_lot_id.x_card_detail_ids:
                if new_line.service_id.id == line.product_id.id:
                    if line.total_qty > new_line.new_count:
                        line.total_qty = line.total_qty - new_line.new_count
                        line.qty_hand = line.qty_hand - new_line.new_count
                        line.amount_total = line.total_qty * line.price_unit
                        line.remain_amount = (line.total_qty - line.qty_use) * line.price_unit
                    elif line.total_qty == new_line.new_count:
                        line.unlink()
        self.state = 'refunded'
        return True

    @api.multi
    def process_rate_service(self):
        #Đổi dịch vụ
        self.action_exchange()
        self.state = 'done'
        return {'type': 'ir.actions.act_window_close'}
