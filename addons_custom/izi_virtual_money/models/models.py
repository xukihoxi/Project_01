# -*- coding: utf-8 -*-
from odoo import api, fields, models, tools, SUPERUSER_ID, _
from odoo.exceptions import AccessDenied, AccessError, UserError, ValidationError


class PostOrder(models.Model):
    _inherit = 'pos.order'

    @api.multi
    def _get_has_paid(self):
        for r in self:
            r.x_has_paid = bool(r.statement_ids)

    x_has_paid = fields.Boolean('Has payment', compute=_get_has_paid, store=False)

    def _izi_compute_journal_domain(self):
        for line in self:
            journal_vm_ids = line.config_id.journal_vm_ids.ids if line.config_id.journal_vm_ids else False
            if journal_vm_ids:
                line.x_vm_journal = ','.join(str(x) for x in journal_vm_ids)
            break

    x_expired = fields.Date(u'Ngày hết hạn')
    x_type = fields.Selection([('1', 'Default'), ('2', 'Thẻ tiền')], default='1')
    x_vm_journal = fields.Char(compute=_izi_compute_journal_domain, store=False, string='Journal for vm')

    @api.onchange('lines')
    def _onchange_lines(self):
        if self._context.get('izi_sell_vm', False) and not self.lines:
            product_obj = self.env['product.product']
            product_id = product_obj.search([('default_code', '=', 'COIN')], limit=1)
            if product_id:
                if not self.pricelist_id:
                    raise UserError(
                        _('You have to select a pricelist in the sale form !\n'
                          'Please set one before choosing a product.'))
                price = self.pricelist_id.get_product_price(product_id, 1.0, self.partner_id)
                self.lines = [{
                    'product_id': product_id.id,
                    'qty': 1,
                    'price_unit': price,
                    'order_id': self.id,
                }]

    @api.multi
    def action_compute_order_discount(self):
        pass

    @api.multi
    def action_order_complete(self):
        vm_obj = self.env['pos.virtual.money']
        # Lấy mã phương thức ghi nợ
        journal_debt_id = self.config_id.journal_debt_id.id if self.config_id.journal_debt_id else False
        journal_exception_ids = self.config_id.journal_exception_ids.ids if self.config_id.journal_exception_ids else False
        if journal_debt_id == False:
            raise UserError(
                _('Vui lòng cấu hình các hình thức thanh toán ghi nợ  ở điểm bán hàng  !\n'
                  'Truy cập vào Cấu hình/ điểm bán hàng/ thiếp lập để cấu hình phương thức thanh toán ghi nợ .'))
        if journal_exception_ids == False:
            raise UserError(
                _('Vui lòng cấu hình các hình thức thanh toán ngoại lệ ở điểm bán hàng  !\n'
                  'Truy cập vào Cấu hình/ điểm bán hàng/ thiếp lập để cấu hình phương thức thanh toán ngoại .'))
        # Kiểm tra đơn mua thẻ tiền này có ghi nợ không
        debt_total = 0.0
        deposit_total = 0.0
        for stt in self.statement_ids:
            if stt.journal_id.id == journal_debt_id:
                debt_total += stt.amount
            if stt.journal_id.id in journal_exception_ids:
                deposit_total += stt.amount
        # sub_amount_id
        main_amount = None
        sub_amount = None
        # tiennq tinh toan cong tien ao cho kh thanh toán bằng chiết khâu ngoại lệ
        a = 0
        for line in self.lines:
            if line.product_id.default_code == 'COIN':
                if line.price_subtotal_incl == 0:
                    a += 1
        if a == 0:
            for line in self.lines:
                if line.product_id.default_code == 'COIN':
                    if deposit_total > 0 and (line.price_unit * line.qty - deposit_total) > 0:
                        main_amount = vm_obj.create({
                            'partner_id': self.partner_id.id if not self.x_owner_id else self.x_owner_id.id,
                            'money': line.price_unit * line.qty - deposit_total,
                            'debt_amount': debt_total,
                            'order_id': self.id,
                            'expired': self.x_expired,
                            'money_used': 0,
                            'typex': '1'
                        })
                        sub_amount = vm_obj.create({
                            'partner_id': self.partner_id.id if not self.x_owner_id else self.x_owner_id.id,
                            'money': deposit_total,
                            'debt_amount': 0,
                            'order_id': self.id,
                            'expired': self.x_expired,
                            'money_used': 0,
                            'typex': '2'
                        })
                    elif (line.price_unit * line.qty - deposit_total) == 0:
                        sub_amount = vm_obj.create({
                            'partner_id': self.partner_id.id if not self.x_owner_id else self.x_owner_id.id,
                            'money': line.price_unit * line.qty,
                            'debt_amount': 0,
                            'order_id': self.id,
                            'expired': self.x_expired,
                            'money_used': 0,
                            'typex': '2'
                        })
                    elif deposit_total == 0:
                        main_amount = vm_obj.create({
                            'partner_id': self.partner_id.id if not self.x_owner_id else self.x_owner_id.id,
                            'money': line.price_unit * line.qty,
                            'debt_amount': debt_total,
                            'order_id': self.id,
                            'expired': self.x_expired,
                            'money_used': 0,
                            'typex': '1'
                        })
        else:
            for line in self.lines:
                if line.product_id.default_code == 'COIN':
                    if line.price_subtotal_incl == 0:
                        sub_amount = vm_obj.create({
                            'partner_id': self.partner_id.id if not self.x_owner_id else self.x_owner_id.id,
                            'money': line.price_unit * line.qty + deposit_total,
                            'debt_amount': 0,
                            'order_id': self.id,
                            'expired': self.x_expired,
                            'money_used': 0,
                            'typex': '2'
                        })
                    else:
                        main_amount = vm_obj.create({
                            'partner_id': self.partner_id.id if not self.x_owner_id else self.x_owner_id.id ,
                            'money': line.price_unit * line.qty - deposit_total,
                            'debt_amount': debt_total,
                            'order_id': self.id,
                            'expired': self.x_expired,
                            'money_used': 0,
                            'typex': '1'
                        })
        # tiennq hết


        if main_amount:
            if sub_amount:
                main_amount.update({'sub_amount_id': sub_amount.id})
                if main_amount.debt_amount:
                    sub_amount.update({'debt_amount': sub_amount.money})
            # Cập nhật hạn mức ghi nợ của KH = số tiền đã thanh toán cho thẻ tiền
            if not self.x_owner_id:
                self.partner_id.x_balance += main_amount.money - debt_total
            else:
                self.x_owner_id.x_balance += main_amount.money - debt_total


    def action_open_popup_search_card(self):
        return {
            'name': _('Search card'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'pos.order',
            # 'views': [(view.id, 'form')],
            'view_id': self.env.ref('izi_pos_custom_backend.view_pop_up_pos_order_input_card').id,
            'target': 'new',
            'res_id': self.id,
            'context': self.env.context,
        }

    @api.model
    def create(self, vals):
        if self._context.get('izi_sell_vm', False):
            vals['x_type'] = '2'
        return super(PostOrder, self).create(vals)


class PosMakePayment(models.TransientModel):
    _inherit = 'pos.make.payment'

    def check(self):
        self.ensure_one()
        if self.journal_id.code.upper() == 'COIN':
            raise ValidationError("Phương thức thanh toán này không được áp dụng!")
        return super(PosMakePayment, self).check()


class VirtualMoney(models.Model):
    _name = 'pos.virtual.money'
    _order = 'create_date desc'
    _description = u'Tiền ảo'

    partner_id = fields.Many2one('res.partner', 'Customer')
    money = fields.Float('Amount')
    debt_amount = fields.Float('Debt amount')
    order_id = fields.Many2one('pos.order', 'Order ref')
    expired = fields.Date('Expired')
    money_used = fields.Float('Used amount')
    typex = fields.Selection([('1', u'Tài khoản chính'), ('2', u'Tài khoản khuyến mại')], u"Loại tài khoản", default='2')
    sub_amount_id = fields.Many2one('pos.virtual.money', 'Sub amount')
    state = fields.Selection([('ready', "Ready"), ('cancel', "Cancel")], default='ready')
    available_money = fields.Float('Available Amount', compute='get_available_amount')

    @api.multi
    def get_available_amount(self):
        for record in self:
            record.available_money += record.money - record.debt_amount - record.money_used

    def get_available_amount_by_partner(self, partner_id):
        records = self.env['pos.virtual.money'].search([('partner_id', '=', partner_id), ('state', '=', 'ready')])
        res = 0.0
        for r in records:
            res += r.money - r.debt_amount - r.money_used
        return res


class VirtualMoneyHistory(models.Model):
    _name = 'pos.virtual.money.history'
    _order = 'create_date desc'
    _description = u'Virtual money history'

    vm_id = fields.Many2one('pos.virtual.money', 'Virtual money ID')
    order_id = fields.Many2one('pos.order', 'Order ref history', readonly=True)
    partner_id = fields.Many2one('res.partner', 'Partner', related='order_id.partner_id', readonly=True)
    statement_id = fields.Many2one('account.bank.statement.line', 'Statement ref', readonly=True)
    amount = fields.Float('Amount', readonly=True)
    location_id = fields.Many2one('stock.location', 'Location', related='order_id.location_id', readonly=True)


class ResPartner(models.Model):
    _inherit = 'res.partner'

    virtual_money_ids = fields.One2many('pos.virtual.money', 'partner_id', u'Virtual money')
    virtual_money_history_ids = fields.One2many('pos.virtual.money.history', 'partner_id', u'Virtual money history')

