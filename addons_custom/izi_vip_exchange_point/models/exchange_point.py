# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from datetime import datetime
from odoo.exceptions import except_orm, ValidationError, UserError


class ExchangePoint(models.Model):
    _name = 'izi.vip.exchange.point'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    @api.model
    def default_get(self, fields):
        res = super(ExchangePoint, self).default_get(fields)
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

    session_id = fields.Many2one(
        'pos.session', string='Session', required=True, index=True,
        readonly=True, default=_default_session)

    name = fields.Char("Name", default="New", copy=False)
    state = fields.Selection(
        selection=(('draft', 'Draft'), ('to_confirm', 'To Confirm'), ('confirm', 'Confirm'),('rate', 'Rate'),
                   ('done', 'Done'), ('to_refund', 'To refund'), ('refunded', 'Refunded'),
                   ('cancel', 'Cancel')),
        default='draft', track_visibility='onchange')
    note = fields.Text("Note", track_visibility='onchange')
    date_exchange = fields.Datetime("Exchange date", required=True, default=datetime.now())
    partner_id = fields.Many2one('res.partner', string='Customer')
    rank_id = fields.Many2one('crm.vip.rank', string=u'Hạng')
    vip_config_id = fields.Many2one('izi.vip.config', string='Vip config')
    pos_order_id = fields.Many2one('pos.order', 'Order')
    point = fields.Float('Point')
    point_exchange_id = fields.Many2one('izi.vip.config.eviction', string='Point exchange')
    number = fields.Integer('Number',default=1)
    lines = fields.One2many('izi.vip.exchange.point.line', 'exchange_id', string='Lines')
    x_lot_number = fields.Char("Lot number")


    @api.model
    def create(self, vals):
        if vals.get('name', _('New')) == _('New'):
            vals['name'] = self.env['ir.sequence'].next_by_code('izi.vip.exchange.point') or _('New')
        return super(ExchangePoint, self).create(vals)

    @api.multi
    def unlink(self):
        for line in self:
            if line.state != 'draft':
                raise except_orm('Thông báo!', (
                    "Không thể xóa bản ghi ở trạng thái khác bản thảo"))
        return super(ExchangePoint, self).unlink()

    @api.onchange('partner_id')
    def _onchange_rank(self):
        user_id = self.env['res.users'].search([('id', '=', self.env.uid)], limit=1)
        config_id = user_id.x_pos_config_id.id
        if self.partner_id:
            self.rank_id = self.partner_id.x_rank.id
        if self.rank_id:
            vip_config_id = self.env['izi.vip.config'].search(
                [('config_id', '=', config_id), ('to_date', '>=', self.date_exchange),
                 ('from_date', '<=', self.date_exchange), ('type', '=', 'eviction')], limit=1)
            if vip_config_id.id == False:
                raise except_orm('Cảnh báo!', (
                    "Chưa cấu hình quy tắc thu hồi điểm. Xin liên hệ quản trị viên"))
            self.vip_config_id = vip_config_id.id
            point = 0
            for line in self.partner_id.x_point_history_ids:
                if line.date >= self.vip_config_id.from_date and line.date <= self.vip_config_id.to_date:
                    point = point + line.point
            self.point = point
            list=[]
            for eviction in vip_config_id.eviction_ids:
                if eviction.rank_id.id == self.rank_id.id:
                    list.append(eviction.id)
            return {
                'domain': {'point_exchange_id': [('id', 'in', list)]}
            }

    @api.multi
    def action_compute(self):
        for i in self.lines:
            i.unlink()
        if self.point_exchange_id:
            if (self.point_exchange_id.point * self.number) > self.point:
                raise except_orm('Cảnh báo!', (
                    "Điểm đổi không được lớn hơn điểm tích lũy"))
            for line in self.point_exchange_id.lines:
                vals = {
                    'exchange_id':self.id,
                    'product_id': line.product_id.id,
                    'qty': line.qty * self.number,
                    'uom_id': line.product_id.product_tmpl_id.uom_id.id,
                    'price_unit': line.price_unit ,
                    'total': line.qty * line.price_unit * self.number,
                }
                lines = self.env['izi.vip.exchange.point.line'].create(vals)

    @api.multi
    def action_sent(self):
        self.action_compute()
        self.state = 'to_confirm'

    @api.multi
    def action_confirm(self):
        self.state = 'confirm'

    @api.multi
    def action_cancel(self):
        if self.state == 'to_refund':
            self.state = 'done'
        else:
            self.state = 'cancel'

    @api.multi
    def action_done(self):
        if not self.pos_order_id:
            point = self.point_exchange_id.point * self.number
            vals = {
                'partner_id': self.partner_id.id,
                'exchange_id': self.id,
                'date': self.date_exchange,
                'point': -point,
            }
            point_history_id = self.env['izi.vip.point.history'].create(vals)
            self.partner_id.x_point_total = self.partner_id.x_point_total - point
            PosOrder = self.env['pos.order']
            argv = {
                'session_id': self.session_id.id,
                'partner_id': self.partner_id.id,
                'state': 'to_confirm',
                'note': 'Đơn hàng đổi điểm'
            }
            order_id = PosOrder.create(argv)
            i = 0
            for line in self.lines:
                if line.product_id.product_tmpl_id.type == 'service' and line.product_id.default_code != 'COIN':
                    i = i+1
                line = {
                    'product_id': line.product_id.id,
                    'qty': line.qty,
                    'price_unit': line.price_unit,
                    'discount': 100,
                    'order_id': order_id.id,
                }
                PosOrder = self.env['pos.order.line'].create(line)
            self.pos_order_id = order_id.id
            if i != 0:
                view = self.env.ref('izi_vip_exchange_point.lot_number_exchange_point_view')
                return {
                    'name': _('Code card'),
                    'type': 'ir.actions.act_window',
                    'view_type': 'form',
                    'view_mode': 'form',
                    'res_model': 'izi.vip.exchange.point',
                    'views': [(view.id, 'form')],
                    'view_id': view.id,
                    'target': 'new',
                    'res_id': self.id,
                    'context': self.env.context,
                }
            else:
                order_id.action_order_confirm()
                self.state = 'done'
                view = self.env.ref('izi_pos_custom_backend.view_pop_up_signature_customer')
                return {
                    'name': _('Customer Signature?'),
                    'type': 'ir.actions.act_window',
                    'view_type': 'form',
                    'view_mode': 'form',
                    'res_model': 'pos.order',
                    'views': [(view.id, 'form')],
                    'view_id': view.id,
                    'target': 'new',
                    'res_id': order_id.id,
                    'context': self.env.context,
                }
        else:
            i = 0
            for line in self.lines:
                if line.product_id.product_tmpl_id.type == 'service' and line.product_id.default_code != 'COIN':
                    i = i + 1
            if i != 0 and not self.x_lot_number:
                view = self.env.ref('izi_vip_exchange_point.lot_number_exchange_point_view')
                return {
                    'name': _('Code card'),
                    'type': 'ir.actions.act_window',
                    'view_type': 'form',
                    'view_mode': 'form',
                    'res_model': 'izi.vip.exchange.point',
                    'views': [(view.id, 'form')],
                    'view_id': view.id,
                    'target': 'new',
                    'res_id': self.id,
                    'context': self.env.context,
                }
            self.state = 'done'
            view = self.env.ref('izi_pos_custom_backend.view_pop_up_signature_customer')
            return {
                'name': _('Customer Signature?'),
                'type': 'ir.actions.act_window',
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'pos.order',
                'views': [(view.id, 'form')],
                'view_id': view.id,
                'target': 'new',
                'res_id': self.pos_order_id.id,
                'context': self.env.context,
            }

    @api.multi
    def action_exchange_point(self):
        lot = self.x_lot_number.upper().strip()
        lot_obj = self.env['stock.production.lot'].search([('name', '=', lot)])
        if len(lot_obj) == 0:
            raise except_orm('Cảnh báo!', ('Mã "%s" không tồn tại trong hệ thống!' % lot))
        if lot_obj.product_id.product_tmpl_id.x_type_card == 'pmh':
            raise except_orm('Cảnh báo!', ('Mã "%s" không phải là mã thẻ dịch vụ!' % lot))
        self.pos_order_id.x_lot_number = lot
        self.pos_order_id.action_search_lot_number()
        self.pos_order_id.action_order_confirm()
        self.state = 'rate'


    @api.multi
    def action_to_refund(self):
        self.state = 'to_refund'

    @api.multi
    def action_refund(self):
        self.pos_order_id.refund()
        pos_rf = self.env['pos.order'].search([('x_pos_partner_refund_id', '=', self.pos_order_id.id)])
        pos_rf.confirm_refund()
        self.state = 'refunded'

class ExchangePointLine(models.Model):
    _name = 'izi.vip.exchange.point.line'

    exchange_id = fields.Many2one('izi.vip.exchange.point', string='Exchange')
    product_id = fields.Many2one('product.product', string='Product')
    uom_id = fields.Many2one('product.uom', string='Uom')
    qty = fields.Float('Qty')
    price_unit = fields.Float('Price')
    total = fields.Float('Total')

