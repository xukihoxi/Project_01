# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from datetime import datetime
from odoo.exceptions import except_orm
from datetime import datetime, timedelta, date as my_date
from dateutil.relativedelta import relativedelta


class GuaranteeLine(models.Model):
    _name = 'guarantee.line'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    @api.model
    def default_get(self, fields):
        res = super(GuaranteeLine, self).default_get(fields)
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
    name = fields.Char("Name", default="New", copy=False, track_visibility='onchange')
    service_id = fields.Many2one('product.product', "Service")
    partner_id = fields.Many2one('res.partner', "Customer")
    date = fields.Datetime(string='Date', default=fields.Datetime.now)
    qty = fields.Integer('Quantity', default=1)
    life_date = fields.Datetime("Life Date", track_visibility='onchange')
    number = fields.Char('Number', required=1)
    lot_id = fields.Many2one('stock.production.lot', "Serial")
    state = fields.Selection(
        [('draft', "Draft"), ('wait_confirm', "Wait Confirm"), ('done', "Done"), ('cancel', "Cancel")], default='draft',
        track_visibility='onchange')

    @api.model
    def create(self, vals):
        if vals.get('name', _('New')) == _('New'):
            vals['name'] = self.env['ir.sequence'].next_by_code('guarantee.line') or _('New')
        return super(GuaranteeLine, self).create(vals)

    @api.multi
    def action_search_lot_number(self):
        str_lot = self.number.upper().strip()
        lot_obj = self.env['stock.production.lot'].search([('name', '=', str_lot)])
        if len(lot_obj) == 0:
            raise except_orm('Cảnh báo!', ('Mã "%s" không tồn tại trong hệ thống!' % str_lot))
        if lot_obj.product_id.product_tmpl_id.x_type_card != 'tbh':
            raise except_orm('Cảnh báo!', ('Thẻ có mã "%s" không phải là thẻ bảo hành. Vui lòng kiểm tra lại!!' % str_lot))
        if lot_obj.x_status == 'new':
            raise except_orm('Cảnh báo!', ('Mã "%s" chưa được kích hoạt!' % str_lot))
        elif lot_obj.x_status == 'using':
            raise except_orm('Cảnh báo!', ('Mã "%s" đã bán và đang được sử dụng!' % str_lot))
        elif lot_obj.x_status == 'used':
            raise except_orm('Cảnh báo!', ('Mã "%s" đã sử dụng xong!' % str_lot))
        elif lot_obj.x_status == 'destroy':
            raise except_orm('Cảnh báo!', ('Mã "%s" đã bị hủy!' % str_lot))
        else:
            if lot_obj.life_date and datetime.strptime(lot_obj.life_date, '%Y-%m-%d %H:%M:%S') + timedelta(
                    days=1) <= datetime.strptime(self.date, '%Y-%m-%d %H:%M:%S'):
                raise except_orm('Cảnh báo!', (('Mã "%s" hết hạn vào ngày: ' + datetime.strptime(lot_obj.life_date,
                                                                                                 "%Y-%m-%d %H:%M:%S").strftime(
                    "%d-%m-%Y")) % str_lot))
        guarantee = self.env['guarantee.line'].search([('lot_id', '=', lot_obj.id),('state','!=','cancel')])
        if len(guarantee) != 0:
            raise except_orm('Cảnh báo!', ('Thẻ có mã "%s" đang được gắn ở đơn bảo hành khác!' % str_lot))
        self.lot_id = lot_obj.id
        if self.env.context.get('using_id', False):
            view = self.env.ref('guarantee_service.view_card_guarantee_form1')
            return {
                'name': _('Thẻ bảo hành'),
                'type': 'ir.actions.act_window',
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'guarantee.line',
                'views': [(view.id, 'form')],
                'view_id': view.id,
                'target': 'new',
                'res_id': self.id,
                'context': self.env.context,
            }

    @api.multi
    def action_send(self):
        if self.life_date:
            if self.life_date <= self.date:
                raise except_orm('Cảnh báo!', ('Ngày hết hạn phải lớn hơn ngày tạo!'))
        if not self.lot_id:
            raise except_orm('Cảnh báo!', ('Bạn chưa thêm thẻ bảo hành cho dịch vụ này!'))
        if self.service_id.x_guarantee != True:
            raise except_orm('Cảnh báo!', ('Dịch vụ bạn chọn không phải dịch vụ được bảo hành. Vui lòng xem lại cấu hình dịch vụ!'))
        self.state = 'wait_confirm'
        if self.env.context.get('using_id', False):
            view = self.env.ref('guarantee_service.view_card_guarantee_form1')
            return {
                'name': _('Thẻ bảo hành'),
                'type': 'ir.actions.act_window',
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'guarantee.line',
                'views': [(view.id, 'form')],
                'view_id': view.id,
                'target': 'new',
                'res_id': self.id,
                'context': self.env.context,
            }

    @api.multi
    def action_cancel(self):
        using = self.env['izi.service.card.using.line'].search([('guarantee_id','=',self.id)],limit=1)
        if using.id != False:
            using.guarantee_id = False
        self.state = 'cancel'

    @api.multi
    def action_confirm(self):
        if self.life_date:
            if self.life_date <= self.date:
                raise except_orm('Cảnh báo!', ('Ngày hết hạn phải lớn hơn ngày tạo!'))
        if self.state != 'wait_confirm':
            return True
        if self.lot_id:
            if self.life_date:
                if self.lot_id.life_date:
                    if self.lot_id.life_date > self.life_date:
                        self.lot_id.life_date = self.life_date
                else:
                    self.lot_id.life_date = self.life_date
            else:
                if not self.lot_id.life_date:
                    life_date = datetime.strptime(self.date, "%Y-%m-%d %H:%M:%S") + relativedelta(
                        months=self.lot_id.x_release_id.validity)
                    self.lot_id.life_date = life_date
                    self.life_date = life_date
        self.lot_id.x_customer_id = self.partner_id.id
        self.lot_id.x_status = 'using'
        self.lot_id.x_user_id = self.partner_id.id
        self.lot_id.x_payment_amount = 0
        lines_lot = []
        argvs = {
            'lot_id': self.lot_id.id,
            'product_id': self.service_id.id,
            'total_qty': self.qty,
            'qty_hand': self.qty,
            'qty_use': 0,
            'price_unit': 0,
            'remain_amount': 0,
            'amount_total': 0,
        }
        lines_lot.append(argvs)
        self.lot_id.x_card_detail_ids = lines_lot
        self.state = 'done'

    @api.multi
    def unlink(self):
        for line in self:
            if line.state != 'draft':
                raise except_orm('Thông báo!', (
                    "Không thể xóa bản ghi ở trạng thái khác bản thảo"))
        return super(GuaranteeLine, self).unlink()
