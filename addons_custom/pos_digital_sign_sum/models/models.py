# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import except_orm

class PosDigitalSignSum(models.Model):
    _name = 'pos.sum.digital.sign'
    _order = "date desc"

    name = fields.Char("Name")
    partner_id = fields.Many2one('res.partner')
    sign_digital = fields.Binary("Sign Digital")
    # Trường hợp chi tiết thì dùng cái này
    sign_order_line_ids = fields.One2many('pos.order.line', 'x_digital_sign_id', "Order Line")
    sign_use_service_line_ids = fields.One2many('izi.service.card.using.line', 'x_digital_sign_id', "Use Service Line")
    sign_account_bank_statement_lines_ids = fields.One2many('account.bank.statement.line', 'x_digital_sign_id', 'Bank Statement')

    # Trường hợp tổng quan thì dùng cái này
    sign_order_ids = fields.One2many('pos.order', 'x_digital_sign_id', 'Order')
    sign_use_service_ids = fields.One2many('izi.service.card.using', 'x_digital_sign_id', 'Use Service')
    sign_destroy_service_ids = fields.One2many('pos.destroy.service', 'x_digital_sign_id', "Destroy Service")
    sign_exchange_service_ids = fields.One2many('izi.pos.exchange.service', 'x_digital_sign_id', "Exchange Service")
    sign_debit_good_ids = fields.One2many('pos.debit.good', 'x_digital_sign_id', "Debit Good")
    state = fields.Selection([('draft', "Draft"), ('done', "Done")], default='draft')
    date = fields.Date("Date")
    session_id = fields.Many2one('pos.session', "Session")
    customer_comment = fields.Text("Customer Comment")

    @api.model
    def create(self, vals):
        if vals.get('name', _('New')) == _('New'):
            vals['name'] = self.env['ir.sequence'].next_by_code('pos.sum.digital.sign') or _('New')
        return super(PosDigitalSignSum, self).create(vals)

    @api.multi
    def apply_all(self):
        dem = True
        # if not self.sign_digital:
        #     raise except_orm('Cảnh báo!', 'Bạn cần phải ký để áp dụng!')
        for line in self.sign_order_ids:
            line.x_signature_image = self.sign_digital
            if line.state == 'customer_comment':
                ''' #Bỏ qua kiểm tra trạng thái picking để khi đóng phiên thì kiểm tra
                for line_pick in line.picking_id:
                    if line_pick.state != 'done':
                        dem = False
                        break
                if dem == True:
                    # line.x_signature_image = self.sign_digital
                    line.process_customer_signature()
                else:
                    line.x_signature_image = self.sign_digital'''
                line.process_customer_signature()
                line.x_signature_image = self.sign_digital
            if line.x_type == '3':
                line.x_signature_image = self.sign_digital
        for line in self.sign_use_service_ids:
            line.signature_image = self.sign_digital
            line.rate_content = self.customer_comment
            if line.state == 'working':
                line.process_rate_service()
        for line in self.sign_destroy_service_ids:
            line.signature_image = self.sign_digital
            if line.state == 'wait_signature':
                line.process_rate_service()
        for line in self.sign_exchange_service_ids:
            line.signature_image = self.sign_digital
            if line.state == 'customer_comment':
                line.process_rate_service()
        for line in self.sign_debit_good_ids:
            if line.state == 'rate':
                for tmp in line.history_ids:
                    tmp.signature_image = self.sign_digital
                    tmp.action_done()
        self.state = 'done'


#   Tạo chữ ký cho pos_order_line

class SignPosOrderLine(models.Model):
    _inherit = 'pos.order.line'

    x_digital_sign_id = fields.Many2one('pos.sum.digital.sign', "Digital Sign")

class SignUseService(models.Model):
    _inherit = 'izi.service.card.using.line'

    x_digital_sign_id = fields.Many2one('pos.sum.digital.sign', "Digital Sign")

class SignAccountBankStatementLine(models.Model):
    _inherit = 'account.bank.statement.line'

    x_digital_sign_id = fields.Many2one('pos.sum.digital.sign', "Digital Sign")



# Chữ ký đơn hàng
class PosDigitalSignOrder(models.Model):
    _inherit = 'pos.order'

    x_digital_sign_id = fields.Many2one('pos.sum.digital.sign', "Digital Sign")

# Chữ ký sử dụng dịch vụ
class PosDigitalSignUseService(models.Model):
    _inherit = 'izi.service.card.using'

    x_digital_sign_id = fields.Many2one('pos.sum.digital.sign', "Digital Sign")

# Chữ ký hủy dịch vụ
class PosDigitalDestroyService(models.Model):
    _inherit = 'pos.destroy.service'

    x_digital_sign_id = fields.Many2one('pos.sum.digital.sign', "Digital Sign")
    # destroy_service_id = fields.Many2one('pos.destroy.service', "Destroy Service")

# Chữ ký đổi dịch vụ
class PosDigitalExchangeService(models.Model):
    _inherit = 'izi.pos.exchange.service'

    x_digital_sign_id = fields.Many2one('pos.sum.digital.sign', "Digital Sign")
    # exchange_service_id = fields.Many2one('izi.pos.exchange.service', "Exchange Service")

# Chũ ký nợ hàng
class PosDigitalSignDebitGood(models.Model):
    _inherit = 'pos.debit.good'

    x_digital_sign_id = fields.Many2one('pos.sum.digital.sign', "Digital Sign")
    # debit_good_id = fields.Many2one('pos.debit.good', "Debit Good")


