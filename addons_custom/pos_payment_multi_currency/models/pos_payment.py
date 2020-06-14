# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import except_orm


class PosMakePayment(models.TransientModel):
    _inherit = 'pos.make.payment'

    x_currency_id = fields.Many2one('res.currency', "Currency")
    x_currency_rate_id = fields.Many2one('res.currency.rate', "Currency Rate")
    x_rate_vn = fields.Float(string="Rate vn")
    x_money_multi = fields.Float("Money Multi")
    x_show_currency_amount = fields.Boolean('Show Currency Amount', default=False, store=False)

    # @api.onchange('x_currency_rate_id')
    # def onchange_currency_rate(self):
    #     ids = []
    #     currency_rate_ids = self.env['res.currency.rate'].search([('currency_id', '=', self.x_currency_id.id)])
    #     for line in currency_rate_ids:
    #             ids.append(line.id)
    #     return {
    #         'domain': {
    #             'x_currency_rate_id': [('id', 'in', ids)]
    #         }
    #     }

    @api.multi
    def read(self, fields=None, load='_classic_read'):
        result = super(PosMakePayment, self).read(fields, load=load)
        for record in result:
            record['x_show_currency_amount'] = False
            if isinstance(record['journal_id'], tuple):
                journal_id = self.env['account.journal'].browse(record['journal_id'][0])
            else:
                journal_id = self.env['account.journal'].browse(record['journal_id'])

            if journal_id.id in self.session_id.config_id.x_journal_currency_ids.ids:
                record['x_show_currency_amount'] = True
        return result

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
        else:
            self.x_currency_id = False
            self.x_money_multi = 0
            self.x_currency_rate_id = False
            self.x_rate_vn = 0
        super(PosMakePayment, self)._onchange_journal_id()

    @api.onchange('x_money_multi', 'x_rate_vn')
    def _onchange_x_money_multi_x_rate_vn(self):
        if self.x_currency_id:
            x_money_multi = self.x_money_multi or 0
            x_rate_vn = self.x_rate_vn or 0
            self.amount = x_rate_vn * x_money_multi

    @api.multi
    def check(self):
        self.ensure_one()
        order = self.env['pos.order'].browse(self.env.context.get('active_id', False))
        order_amount = order.amount_total - order.amount_paid
        context = dict(self._context or {})
        context['izi_currency_id'] = False
        context['izi_currency_rate_id'] = False
        context['izi_money_multi'] = 0
        if self.journal_id.id in self.session_id.config_id.x_journal_currency_ids.ids:
            # if self.x_currency_rate_id:
            if self.x_rate_vn:
                context['izi_currency_id'] = self.x_currency_id.id
                context['izi_money_multi'] = self.x_money_multi
                # context['izi_currency_rate_id'] = self.x_currency_rate_id.id
            # if not (self.x_currency_rate_id.rate_vn * self.x_money_multi- 10000 <= self.amount <= self.x_currency_rate_id.rate_vn * self.x_money_multi+ 10000):
            if not (self.x_rate_vn * self.x_money_multi- 10000 <= self.amount <= self.x_rate_vn * self.x_money_multi+ 10000):
                raise except_orm('Cảnh báo!', ("Số tiền điều chỉnh không thể lớn hơn 10.000 VNĐ"))
        return super(PosMakePayment, self.with_context(context)).check()
