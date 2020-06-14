# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import except_orm
from datetime import timedelta, datetime
from datetime import date, datetime

class StockExtendCard(models.Model):
    _name = 'stock.extend.card'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = "id desc"

    name = fields.Char('Name', default="/", track_visibility='onchange')
    user_id = fields.Many2one('res.users', "User", default=lambda self: self.env.uid)
    date = fields.Date('Date', default=fields.Datetime.now, track_visibility='onchange')
    config_id = fields.Many2one('pos.config', "Config", dèault=lambda  self: self.env.user.x_pos_config_id.id)
    partner_id = fields.Many2one('res.partner', "Partner", track_visibility='onchange')
    serial = fields.Char("Serial", track_visibility='onchange')
    state = fields.Selection([('draft', "Draft"), ('wait_confirm', "Wait Confirm"), ('done', "Done"), ('cancel', "Cancel")], default='draft', track_visibility='onchange')
    extend_card_ids = fields.One2many('stock.extend.card.line', 'extend_card_id', "Extend Card")

    @api.model
    def create(self, vals):
        if vals.get('name', _('New')) == _('New'):
            vals['name'] = self.env['ir.sequence'].next_by_code('stock.extend.card') or _('New')
        return super(StockExtendCard, self).create(vals)

    @api.multi
    def action_search_serial(self):
        self.extend_card_ids.unlink()
        serial = self.serial
        if serial and len(serial) > 0:
            serial = str(self.serial).strip()
        else:
            raise except_orm(_('Thông báo'), _('Vui lòng nhập mã thẻ !'))

        extend_card_obj = self.env['stock.extend.card.line']
        lot_obj = self.env['stock.production.lot'].search([('name', '=', serial)], limit=1)
        if lot_obj:
            if lot_obj.x_status != 'using':
                raise except_orm('Cảnh báo!', "Thẻ không dùng được")
            if lot_obj.x_status != 'using' and lot_obj.x_status != 'used':
                raise except_orm('Cảnh báo!', ('Thẻ không hợp lệ'))
            argvs = {
                'lot_id': lot_obj.id,
                'life_date': lot_obj.life_date,
                'extend_card_id': self.id,
            }
            extend_card_obj.create(argvs)
            self.partner_id = lot_obj.x_customer_id.id
        else:
            raise except_orm('Cảnh báo!', ('Không tìm thấy mã thẻ'))
        self.serial_code = ''
        self.partner_search_id = ''


    @api.multi
    def action_send(self):
        if self.state != 'draft':
            raise except_orm('Cảnh báo!', ("Trạng thái đơn đã thay đổi. Vui lòng F5 hoặc load lại trang"))
        self.state = 'wait_confirm'
        if not self.partner_id:
            raise except_orm("Cảnh báo!", ("Bạn cần điền đầy đủ thông tin trước khi gửi!"))
        for line in self.extend_card_ids:
            if line.extend_date == False:
                raise except_orm('Cảnh báo!', ('Bạn cần chọn ngày gia hạn'))
            if line.extend_date <= line.life_date:
                raise except_orm('Cảnh báo!', ("Ngày gia hạn không thể nhỏ hơn ngày hết hạn trước"))

    @api.multi
    def action_confirm(self):
        if self.state != 'wait_confirm':
            raise except_orm('Cảnh báo!', ("Trạng thái đơn đã thay đổi. Vui lòng F5 hoặc load lại trang"))
        self.state = 'done'
        for line in self.extend_card_ids:
            line.lot_id.x_before_life_date = line.lot_id.life_date
            line.lot_id.life_date = line.extend_date



    @api.multi
    def action_cancel(self):
        if self.state != 'wait_confirm':
            raise except_orm('Cảnh báo!', ("Trạng thái đơn đã thay đổi. Vui lòng F5 hoặc load lại trang"))
        self.state = 'cancel'





class StockExtendCardLine(models.Model):
    _name = 'stock.extend.card.line'

    lot_id = fields.Many2one('stock.production.lot', "Lot")
    life_date = fields.Date("Life Date")
    extend_date = fields.Date("Extend date")
    extend_card_id = fields.Many2one('stock.extend.card', "Extend Card")



class StockProductionLot(models.Model):
    _inherit = 'stock.production.lot'

    x_before_life_date = fields.Datetime('Before Life Date')
