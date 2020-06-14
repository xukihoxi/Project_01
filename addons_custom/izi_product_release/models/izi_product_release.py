# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from datetime import datetime
import logging
from odoo.exceptions import except_orm, ValidationError, RedirectWarning

_logger = logging.getLogger(__name__)


class IziProductRelease(models.Model):
    _name = 'izi.product.release'
    _order = 'date ASC'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    def _default_card_product(self):
        product_id = self.env['product.product'].search([('default_code','=','PHOI')],limit=1)
        if product_id.id != False:
            return product_id.id
    # def _default_location(self):
    #     param_obj = self.env['ir.config_parameter']
    #     code = param_obj.get_param('release_stock_location')
    #     if code == False:
    #         return False
    #     location_id = self.env['stock.location'].search([('x_code','=',code)],limit=1)
    #     if location_id.id != False:
    #         return location_id.id

    EXPIRE_TYPE = [('0', 'Fixed'), ('1', 'Flexible')]
    USED_TYPE = [('0', 'Real name'), ('1', 'Flexible')]

    name = fields.Char('Name', track_visibility='always', default='/')
    campaign_id = fields.Many2one('utm.campaign', string='Campaign', required=True)
    product_id = fields.Many2one('product.product', string='Product', required=True)
    card_blank_id = fields.Many2one('product.product', string='Card Blank',default=_default_card_product)
    quantity = fields.Integer('Quantity', required=True)
    use_type = fields.Selection(string='Use type', selection=USED_TYPE, default='0')
    location_id = fields.Many2one('stock.location', string='Picking to',
                                  required=False)
    release_location_id = fields.Many2one('stock.location', string='Delivery to', required=True)
    date = fields.Date('Created date', required=True, default=fields.Datetime.now)
    expired_type = fields.Selection(string='Expire type', selection=EXPIRE_TYPE, default='0')
    expired_date = fields.Date('Expired date')
    validity = fields.Integer('Num of active days (month)')

    state = fields.Selection(selection=(('draft', 'Draft'),
                                        ('created', 'Created'),
                                        ('actived', "Actived"),
                                        ('transfering','Transfering'),
                                        ('done', 'Done'),
                                        ('cancel', "Cancel"),), default='draft', string='State')
    production_lot_ids = fields.One2many('stock.production.lot', 'x_release_id', string='Product detail', auto_join=True)
    note = fields.Text('Note')

    picking_id = fields.Many2one('stock.picking',string='Picking')
    move_ids = fields.One2many('stock.move','x_release_id',string='Move')

    # @api.onchange('release_location_id')
    # def _onchange_code_release(self):
    #     if not self.release_location_id:
    #         param_obj = self.env['ir.config_parameter']
    #         code = param_obj.get_param('release_stock_location')
    #         if code == False:
    #             raise ValidationError(_(u"Bạn chưa cấu hình thông số hệ thống cho địa điểm tổng. Xin hãy liên hệ với người quản trị."))
    #         location_id = self.env['stock.location'].search([('x_code', '=', code)], limit=1)
    #         if location_id.id == False:
    #             raise ValidationError(_(u"Bạn chưa cấu hình mã kho tổng "))


    @api.model
    def create(self, vals):
        if vals.get('name', _('New')) == _('New'):
            vals['name'] = self.env['ir.sequence'].next_by_code('izi.product.release') or _('New')
        if vals.get('card_blank_id') == '' or vals.get('card_blank_id') == False or not vals.get('card_blank_id'):
            raise ValidationError(_(u"Bạn chưa cấu hình sản phẩm cho phôi."))
        return super(IziProductRelease, self).create(vals)

    @api.onchange('expired_type','expired_date','validity')
    def _onchange_check(self):
        if self.expired_type == '1':
            self.expired_date =  False
        else:
            self.validity = 0

    @api.constrains('validity', 'expired_type')
    def _check_validity(self):
        if self.expired_type == '1' and self.validity == 0:
            raise ValidationError(_(u"Số tháng hết hạn phải lớn hơn 0 !!!"))

    @api.constrains('expired_type','expired_date','date')
    def _check_expired_date(self):
        if self.expired_type == '0' and self.date >= self.expired_date:
            raise ValidationError(_(u"Ngày hết hạn phải lớn hơn ngày phát hành !!!"))

    @api.constrains('product_id', 'use_type')
    def _check_use_type(self):
        if self.product_id.product_tmpl_id.x_type_card == 'tbh' and self.use_type == '1':
            raise ValidationError(_(u"Thẻ bảo hành chỉ được sử dụng đích danh. Vui lòng kiểm tra lại!!!"))

    def _get_inventory(self, product_id, location_id):
        total_availability = self.env['stock.quant']._get_available_quantity(product_id, location_id)
        return total_availability

    def _get_code_index(self,qty):
        list_code = []
        if self.product_id.product_tmpl_id.x_type_card == 'tdv':
            prefix = 'TDV'
        elif self.product_id.product_tmpl_id.x_type_card == 'tdt':
            prefix = 'TDT'
        elif self.product_id.product_tmpl_id.x_type_card == 'tbh':
            prefix = 'TBH'
        elif self.product_id.product_tmpl_id.x_type_card == 'pmh':
            prefix = 'PMH'
        code = prefix + self.date[2:4] + self.date[5:7]
        query = """SELECT l.name as code FROM stock_production_lot l
                    WHERE l.name like %s
                    ORDER BY l.id desc LIMIT 1"""
        self._cr.execute(query, (str(code+'%'),))
        new_code = self._cr.fetchall()
        for i in range(0, qty):
            stt = i + 1
            if len(new_code) == 0:
                len_stt = len(str(stt))
                auto = '0' * (4 - len_stt) + str(stt)
            else:
                code_max = new_code[0][0][7:]
                int_new = int(code_max) + stt
                str_new = len(str(int_new))
                auto = '0' * (4 - str_new) + str(int_new)
            list_code.append(code + auto)
        return list_code

    @api.multi
    def generate_serial(self):
        # try:
        if (self.quantity == 0):
            raise except_orm('Error !!!',
                             'Số lượng phát hành phải lớn hơn 0 !!!')
        list_production = []
        self.production_lot_ids = False
        if self.expired_type == '0':
            life_date = self.expired_date
        else:
            life_date = False
        # TODO: Thực hiện query 1 lần và lấy về list các mã
        list_code = self._get_code_index(self.quantity)
        for i in range(0, self.quantity):
            code = list_code[i]
            vals = {
                'name': code,
                'x_release_id': self.id,
                'product_id': self.product_id.id,
                'product_uom_id': self.product_id.product_tmpl_id.uom_id.id,
                'x_discount': self.product_id.product_tmpl_id.x_discount,
                'x_amount': self.product_id.product_tmpl_id.x_amount,
                'life_date': life_date,
                'x_customer_id': False,
                'x_user_id': False,
            }
            list_production.append(vals)
        self.production_lot_ids = list_production
        self.write({'state': 'created'})


    @api.multi
    def action_active(self):
        self.do_transfer_loss()
        for serial in self.production_lot_ids:
            serial.write({'x_status': 'actived',
                          'x_amount': self.product_id.product_tmpl_id.x_amount,
                          'x_discount': self.product_id.product_tmpl_id.x_discount})
        if self.release_location_id.id == self.location_id.id:
            self.write({'state': 'done'})
        else:
            self.write({'state': 'actived'})

    @api.multi
    def do_transfer_loss(self):
        product_vals = self._get_inventory_loss(self.card_blank_id)
        property_stock_inventory = product_vals.get('property_stock_inventory')
        product_vals_in = self._get_inventory_loss(self.product_id)
        property_stock_production_in = product_vals.get('property_stock_inventory')

        release_stock = self.release_location_id
        cost_price_out = product_vals.get('cost_price', 0.0)
        cost_price_in = product_vals_in.get('cost_price', 0.0)
        move_obj = self.env['stock.move']
        move_line_obj = self.env['stock.move.line']

        # TODO: Thực hiện xuất phôi từ kho phát hành về kho ảo tồn kho
        stock_move_out_vals = {
            'product_id': self.card_blank_id.id,
            'origin': self.name,
            'product_uom': self.card_blank_id.product_tmpl_id.uom_id.id,
            'product_uom_qty': self.quantity,
            'price_unit': cost_price_out,
            'location_id': release_stock.id,
            'location_dest_id': property_stock_inventory,
            'name': self.card_blank_id.product_tmpl_id.name,
            'state': 'done',
            'x_release_id': self.id
        }
        move_out = move_obj.create(stock_move_out_vals)
        stock_move_out_line_vals = {
            'product_id': self.card_blank_id.id,
            'origin': self.name,
            'product_uom_id': self.card_blank_id.product_tmpl_id.uom_id.id,
            'qty_done': self.quantity,
            'price_unit': cost_price_out,
            'location_id': release_stock.id,
            'location_dest_id': property_stock_inventory,
            'name': self.card_blank_id.product_tmpl_id.name,
            'move_id': move_out.id,
            'state': 'done'
        }
        move_line_obj.create(stock_move_out_line_vals)

        # TODO: Thực hiện nhập thẻ từ kho ảo sản xuất vào kho phát hành
        stock_move_in_vals = {
            'product_id': self.product_id.id,
            'origin': self.name,
            'product_uom': self.product_id.product_tmpl_id.uom_id.id,
            'product_uom_qty': self.quantity,
            'price_unit': cost_price_in,
            'location_id': property_stock_production_in,
            'location_dest_id': release_stock.id,
            'name': self.product_id.product_tmpl_id.name,
            'state': 'done',
            'x_release_id': self.id
        }
        move_in = move_obj.create(stock_move_in_vals)
        for ob in self.production_lot_ids:
            stock_move_in_line_vals = {
                'product_id': self.product_id.id,
                'origin': self.name,
                'product_uom_id': self.product_id.product_tmpl_id.uom_id.id,
                'qty_done': 1,
                'price_unit': cost_price_in,
                'location_id': property_stock_production_in,
                'location_dest_id': release_stock.id,
                'name': self.product_id.product_tmpl_id.name,
                'lot_id': ob.id,
                'lot_name': ob.name,
                'move_id': move_in.id,
                'state': 'done'
            }
            move_line_obj.create(stock_move_in_line_vals)
        return True


    def _get_inventory_loss(self, product_id):
        if not product_id.property_stock_inventory:
            raise except_orm('Error!', 'Bạn phải cấu hình tài khoản kế toán cho sản phẩm')
        property_stock_inventory = product_id.property_stock_inventory.id
        cost_price = product_id.standard_price
        dict = {
            'property_stock_inventory': property_stock_inventory,
            'cost_price': cost_price
        }
        return dict

    @api.multi
    def action_transfer(self):
        if self.release_location_id.id == self.location_id.id :
            self.write({'state': 'done'})
        else:
            picking_obj = self.env['stock.picking']
            picking_type_id = self.env['stock.picking.type'].search(
                [('code', '=', 'internal'), ('default_location_src_id', '=', self.release_location_id.id),
                 ('default_location_dest_id', '=', self.location_id.id)], limit=1)
            if picking_type_id.id == False:
                raise except_orm('Cảnh báo!', (
                    "Xin hãy cấu hình loại điều chuyển kho"))
            picking_vals = {
                'picking_type_id': picking_type_id.id,
                'date': datetime.now(),
                'origin': self.name,
                'location_id': self.release_location_id.id,
                'location_dest_id': self.location_id.id,
                'state':'assigned',
            }
            picking_id = picking_obj.create(picking_vals)
            move_line_obj = self.env['stock.move.line']
            move_obj = self.env['stock.move']
            stock_move_in_vals = {
                'product_id': self.product_id.id,
                'origin': self.name,
                'product_uom': self.product_id.product_tmpl_id.uom_id.id,
                'product_uom_qty': self.quantity,
                'location_id': self.release_location_id.id,
                'location_dest_id': self.location_id.id,
                'name': self.product_id.product_tmpl_id.name,
                'picking_id': picking_id.id,
            }
            move = move_obj.create(stock_move_in_vals)
            for ob in self.production_lot_ids:
                stock_move_line_vals = {
                    'product_id': self.product_id.id,
                    'origin': self.name,
                    'product_uom_id': self.product_id.product_tmpl_id.uom_id.id,
                    'qty_done': 1,
                    'location_id': self.release_location_id.id,
                    'location_dest_id': self.location_id.id,
                    'name': self.product_id.product_tmpl_id.name,
                    'lot_id': ob.id,
                    'lot_name': ob.name,
                    'picking_id': picking_id.id,
                    'move_id':move.id,
                }
                move_line_obj.create(stock_move_line_vals)
            picking_id.action_confirm()
            picking_id.action_assign()
            self.write({'state': 'transfering','picking_id': picking_id.id})

    @api.multi
    def action_cancel_release(self):
        if self.state == 'actived' and self.card_blank_id:
            self.do_transfer()
        for ob in self.production_lot_ids:
            ob.unlink()
        self.write({'state': 'cancel'})

    @api.multi
    def do_transfer(self):
        product_vals = self._get_inventory_loss(self.card_blank_id)
        property_stock_inventory = product_vals.get('property_stock_inventory')
        product_vals_in = self._get_inventory_loss(self.product_id)
        property_stock_production_in = product_vals.get('property_stock_production')

        release_stock = self.release_location_id
        cost_price_out = product_vals.get('cost_price', 0.0)
        cost_price_in = product_vals_in.get('cost_price', 0.0)
        move_obj = self.env['stock.move']
        move_line_obj = self.env['stock.move.line']

        # TODO: Thực hiện trả phôi từ kho ảo tồn kho về kho nguồn
        stock_move_out_vals = {
            'product_id': self.card_blank_id.id,
            'origin': self.name,
            'product_uom': self.card_blank_id.product_tmpl_id.uom_id.id,
            'product_uom_qty': self.quantity,
            'price_unit': cost_price_out,
            'location_dest_id': release_stock.id,
            'location_id': property_stock_inventory,
            'name': self.card_blank_id.product_tmpl_id.name,
            'state': 'done',
            'x_release_id': self.id
        }
        move_out = move_obj.create(stock_move_out_vals)
        stock_move_out_line_vals = {
            'product_id': self.card_blank_id.id,
            'origin': self.name,
            'product_uom_id': self.card_blank_id.product_tmpl_id.uom_id.id,
            'qty_done': self.quantity,
            'price_unit': cost_price_out,
            'location_dest_id': release_stock.id,
            'location_id': property_stock_inventory,
            'name': self.card_blank_id.product_tmpl_id.name,
            'move_id': move_out.id,
            'state': 'done'
        }
        move_line_obj.create(stock_move_out_line_vals)

        # TODO: Thực hiện trả thẻ từ kho phát hành về kho ảo sản xuất
        stock_move_in_vals = {
            'product_id': self.product_id.id,
            'origin': self.name,
            'product_uom': self.product_id.product_tmpl_id.uom_id.id,
            'product_uom_qty': self.quantity,
            'price_unit': cost_price_in,
            'location_dest_id': property_stock_production_in,
            'location_id': release_stock.id,
            'name': self.product_id.product_tmpl_id.name,
            'state': 'done',
            'x_release_id': self.id
        }
        move_in = move_obj.create(stock_move_in_vals)
        for ob in self.production_lot_ids:
            stock_move_in_line_vals = {
                'product_id': self.product_id.id,
                'origin': self.name,
                'product_uom_id': self.product_id.product_tmpl_id.uom_id.id,
                'qty_done': 1,
                'price_unit': cost_price_in,
                'location_dest_id': property_stock_production_in,
                'location_id': release_stock.id,
                'name': self.product_id.product_tmpl_id.name,
                'lot_id': ob.id,
                'lot_name': ob.name,
                'move_id': move_in.id,
                'state': 'done'
            }
            move_line_obj.create(stock_move_in_line_vals)
        return True

    @api.multi
    def unlink(self):
        for line in self:
            if line.state != 'draft':
                raise except_orm('Thông báo!', (
                    "Không thể xóa bản ghi ở trạng thái khác bản thảo"))
        return super(IziProductRelease, self).unlink()

    @api.multi
    def write(self, vals):
        if len(vals) > 0:
            self.create_log(vals)
        return super(IziProductRelease, self).write(vals)

    @api.multi
    def create_log(self, vals):
        mail_message_obj = self.env['mail.message']
        id = self.id
        user = self.env['res.users'].browse([self._uid])
        partner_id = user.partner_id
        subtype_id = 2
        subtype = self.env['mail.message.subtype'].browse([subtype_id])
        if len(subtype) == 0:
            subtype = self.env['mail.message.subtype'].search([('name', '=', 'Note')])
            if len(subtype) > 0:
                subtype_id = subtype[0].id
            else:
                subtype_id = 0
        body = ""
        for val in vals:
            if val == 'state':
                bd = "<p>Chuyển trạng thái " + self.state + " -> " + vals.get('state') + "</p>"
                body = body + bd
        if len(body) > 0:
            bd = "<p>Thời gian " + str(fields.Datetime.now()) + " </p>"
            body = body + bd
            vals_mail_message = {
                'model': 'izi.product.release',
                'email_from': partner_id.name or '' + ' <' + partner_id.email or '' + '>',
                'reply_to': partner_id.name or '' + ' <' + partner_id.email or '' + '>',
                'message_type': 'notification',
                'date': fields.Datetime.now(),
                'res_id': id,
                'subtype_id': subtype_id,
                'record_name': self.name or 'no_message',
                'author_id': partner_id.id,
                'body': body
            }
            parent = mail_message_obj.search(
                [('model', '=', 'izi.product.release'), ('res_id', '=', self.id), ('parent_id', '=', False)],
                limit=1)
            if len(parent) > 0:
                vals_mail_message['parent_id'] = parent[0].id
            mail_id = mail_message_obj.create(vals_mail_message)

