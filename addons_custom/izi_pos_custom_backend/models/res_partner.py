# -*- coding: utf-8 -*-

from odoo import models, fields, api
from datetime import datetime
from odoo.exceptions import UserError, except_orm


class ResPartner(models.Model):
    _inherit = 'res.partner'

    @api.multi
    def _calc_due_amount(self):
        fmt = '%Y-%m-%d'
        today = (datetime.today()).strftime(fmt)
        cr = self._cr
        for record in self:
            total = 0.0
            query = "SELECT SUM(residual) residual FROM account_invoice WHERE partner_id = %s and state='open' and date_due < %s"
            cr.execute(query, (record.id, today))
            res = cr.dictfetchone()
            if res:
                total = res['residual']
            record.x_total_overdue = total

    @api.multi
    def _compute_id(self):
        cr = self._cr
        for record in self:
            record.conpute_id = record.id

    x_pmh_ids = fields.One2many('stock.production.lot', 'x_customer_id', domain=[('product_id.product_tmpl_id.x_type_card', '=', 'pmh')])
    x_card_ids = fields.One2many('stock.production.lot', 'x_customer_id', domain=[('product_id.product_tmpl_id.x_type_card', '=', 'tdv')])
    x_crm_his_ids = fields.One2many('crm.vip.customer.history', 'partner_id')
    x_account_invoices = fields.One2many('account.invoice', 'partner_id', string="Invoices", domain=[('state', '=', 'open')], auto_join=True)
    x_account_invoices_all = fields.One2many('account.invoice', 'partner_id', string="Invoices", domain=[('state', 'in',('open','paid'))], auto_join=True)
    x_payment_ids = fields.One2many('account.payment', 'partner_id', string='Payments', domain=[('payment_type', '=', 'inbound'),('x_payment_debit', '=', True),('state', '=','posted')])
    x_total_overdue = fields.Float(compute='_calc_due_amount', string="Total overdue")
    x_loyal_total = fields.Float('Loyal total', readonly=True)
    x_point_total = fields.Float("Point total", readonly=True)
    x_total_revenue = fields.Float("Total Revenue", compute='_compute_total_revenue')
    x_balance = fields.Float('Balance')
    conpute_id = fields.Float(compute='_compute_id', string="Compute View")
    #tiennq them nagy 17/08 tong tien ao
    x_virtual_total = fields.Float("Total Revenue", compute='_compute_total_virtual')

    @api.depends('x_payment_ids.x_payment_debit', 'x_payment_ids.state', 'x_payment_ids.payment_type')
    def _compute_payment_debit(self):
        for partner in self:
            partner.x_payment_ids = self.env['account.payment'].search([
                ('x_payment_debit', '=', True), ('partner_id', '=', partner.id)
                ('state', '=', 'posted'),
                ('payment_type', '=', 'inbound')
            ])

    @api.depends('x_revenue_ids')
    def _compute_total_revenue(self):
        for line in self:
            for tmp in line.x_revenue_ids:
                line.x_total_revenue += tmp.amount

    @api.depends('virtual_money_ids')
    def _compute_total_virtual(self):
        for res in self:
            total = 0
            for line in res.virtual_money_ids:
                if line.state == 'ready':
                    total += line.money - line.debt_amount - line.money_used

    @api.model
    def get_pos_order_line_detail_customer(self, partner_id):
        # print(1)
        order_line_details = []
        if partner_id:
            order = self.env['pos.order'].sudo().search([('partner_id', '=', partner_id)], order='id desc')
            for order_id in order:
                for line in order_id.lines:
                    if line.lot_name == False and order_id.state in ('invoiced', 'done', 'cancel', 'paid'):
                        vals7 = {
                            'product_name': line.product_id.name,
                            # 'lot_name': line.lot_name if line.lot_name else '',
                            'qty': line.qty,
                            'price_unit': line.price_unit,
                            'discount': line.discount,
                            'x_discount': line.x_discount,
                            'price_subtotal_incl': line.price_subtotal_incl,
                            'order_name': order_id.name,
                            'date_order': datetime.strptime(order_id.date_order, '%Y-%m-%d %H:%M:%S') + timedelta(
                                hours=7),
                            'user_name': order_id.user_id.name,
                            'state': order_id.state,
                            'x_type': order_id.x_type,
                        }
                        order_line_details.append(vals7)
        return order_line_details