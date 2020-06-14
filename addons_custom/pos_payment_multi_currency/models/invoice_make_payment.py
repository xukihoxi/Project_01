# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from datetime import date
from odoo.exceptions import UserError, ValidationError, MissingError
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT
from odoo.exceptions import except_orm, Warning as UserError


class InvoiceMakePayment(models.TransientModel):
    _inherit = 'invoice.make.payment'

    x_currency_id = fields.Many2one('res.currency', "Currency")
    x_currency_rate_id = fields.Many2one('res.currency.rate', "Currency Rate")
    x_rate_vn = fields.Float(default=0, string="Rate VN")
    x_money_multi = fields.Float("Money Multi")
    x_show_currency_amount = fields.Boolean('Show Currency Amount', default=False, store=False)

    @api.onchange('journal_id')
    def _onchange_journal_id(self):
        self.x_show_currency_amount = False
        if self.journal_id.id in self.session_id.config_id.x_journal_currency_ids.ids:
            self.x_show_currency_amount = True
            if self.journal_id.x_pos_multi_currency_id:
                self.x_currency_id = self.journal_id.x_pos_multi_currency_id.id
                self.x_money_multi = 0
                self.x_currency_rate_id = False
                self.x_rate_vn = 0
            else:
                raise except_orm('Cảnh báo', ("Chưa cấu hình đa tiền tệ trên pos cho sổ này. Vui lòng liên hệ quản trị hệ thống"))
        super(InvoiceMakePayment, self)._onchange_journal_id()

    @api.onchange('x_money_multi', 'x_rate_vn')
    def _onchange_x_money_multi_x_rate_vn(self):
        if self.x_currency_id:
            x_money_multi = self.x_money_multi or 0
            x_rate_vn = self.x_rate_vn or 0
            self.amount = x_rate_vn * x_money_multi

    # @api.onchange('x_currency_rate_id')
    # def onchange_currency_rate(self):
    #     ids = []
    #     currency_rate_ids = self.env['res.currency.rate'].search([('currency_id', '=', self.x_currency_id.id)])
    #     for line in currency_rate_ids:
    #         ids.append(line.id)
    #     return {
    #         'domain': {
    #             'x_currency_rate_id': [('id', 'in', ids)]
    #         }
    #     }


    def process_payment(self):
        res = super(InvoiceMakePayment, self).process_payment()
        if self.journal_id.id in self.session_id.config_id.x_journal_currency_ids.ids:
            res.update({
                'x_amount_currency': self.x_money_multi,
                'x_currency_id': self.x_currency_id.id,
                # 'x_rate_vn': self.x_rate_vn,
                # 'x_currency_rate_id': self.x_currency_rate_id.id,
            })
            # if not (self.x_currency_rate_id.rate_vn * self.x_money_multi - 10000 <= self.amount <= self.x_currency_rate_id.rate_vn * self.x_money_multi+ 10000):
            if not (self.x_rate_vn * self.x_money_multi - 10000 <= self.amount <= self.x_rate_vn * self.x_money_multi+ 10000):
                raise except_orm('Cảnh báo!', ("Số tiền điều chỉnh không thể lớn hơn 10.000 VNĐ"))
        return res