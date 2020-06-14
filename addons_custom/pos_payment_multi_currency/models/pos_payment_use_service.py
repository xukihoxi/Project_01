# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from datetime import date, datetime
from odoo.exceptions import except_orm, UserError, MissingError, ValidationError

class PosPaymentService(models.Model):
    _inherit = 'pos.payment.service'

    x_currency_id = fields.Many2one('res.currency', "Currency")
    x_currency_rate_id = fields.Many2one('res.currency.rate', "Currency Rate")
    x_rate_vn = fields.Float(string="Rate VN")
    x_money_multi = fields.Float("Money Multi")
    x_show_currency_amount = fields.Boolean('Show Currency Amount', default=False, store=False)

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

    @api.onchange('journal_id')
    def onchange_journal_id(self):
        self.x_show_currency_amount = False
        if self.journal_id.id in self.using_service_id.pos_session_id.config_id.x_journal_currency_ids.ids:
            self.x_show_currency_amount = True
            if self.journal_id.x_pos_multi_currency_id:
                self.x_currency_id = self.journal_id.x_pos_multi_currency_id.id
                self.x_money_multi = 0
                self.x_currency_rate_id = False
                self.x_rate_vn = 0
            else:
                raise except_orm('Cảnh báo', ("Chưa cấu hình đa tiền tệ trên pos cho sổ này. Vui lòng liên hệ quản trị hệ thống"))
        else:
            self.x_money_multi = 0
            self.x_currency_rate_id = ''
            self.x_rate_vn = 0
            self.x_show_currency_amount = False
        super(PosPaymentService, self).onchange_journal_id()

    @api.onchange('x_money_multi', 'x_rate_vn')
    def _onchange_x_money_multi_x_rate_vn(self):
        if self.x_currency_id:
            x_money_multi = self.x_money_multi or 0
            x_rate_vn = self.x_rate_vn or 0
            self.amount = x_rate_vn * x_money_multi

    @api.multi
    def process_payment_service(self):
        pos_session = self.env['pos.session']
        pos_config_id = self.env.user.x_pos_config_id.id
        my_session = pos_session.search([('config_id', '=', pos_config_id), ('state', '=', 'opened')])
        if self.journal_id.id in my_session.config_id.x_journal_currency_ids.ids:
            # if not (self.x_currency_rate_id.rate_vn * self.x_money_multi - 10000 <= self.amount <= self.x_currency_rate_id.rate_vn * self.x_money_multi + 10000):
            if not (self.x_rate_vn * self.x_money_multi - 10000 <= self.amount <= self.x_rate_vn * self.x_money_multi + 10000):
                self.x_money_multi = 0
                self.x_currency_rate_id = ''
                self.x_rate_vn = 0
                self.x_show_currency_amount = False
                self.journal_id = my_session.config_id.journal_ids.ids[0]
                active_id = self.env.context.get('active_id')
                if active_id:
                    order = self.env['izi.service.card.using'].browse(active_id)
                    tmp = 0
                    for line in order.service_card1_ids:
                        tmp += line.amount
                    tmp1 = 0
                    for line in order.pos_payment_service_ids:
                        tmp1 += line.amount
                    self.update({
                        'amount': tmp - tmp1 + self.amount
                    })
                view = self.env.ref('pos_payment_multi_currency.view_pop_up_masseage')
                return {
                    'name': _('Request Material'),
                    'type': 'ir.actions.act_window',
                    'view_type': 'form',
                    'view_mode': 'form',
                    'res_model': 'pos.payment.service',
                    'views': [(view.id, 'form')],
                    'view_id': view.id,
                    'res_id': self.id,
                    'target': 'new',
                    'context': self.env.context,
                }
        return super(PosPaymentService, self).process_payment_service()

