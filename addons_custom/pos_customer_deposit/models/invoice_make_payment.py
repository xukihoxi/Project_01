# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from datetime import date
from odoo.exceptions import UserError, ValidationError, MissingError
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT
from odoo.exceptions import except_orm, Warning as UserError


class InvoiceMakePayment(models.TransientModel):
    _inherit = 'invoice.make.payment'

    def _show_deposit_amount_residual(self):
        deposit_lines = self.env['pos.customer.deposit'].search([('partner_id', '=', self.invoice_id.partner_id.id)])
        total = 0.0
        for line in deposit_lines:
            total += line.residual
        self.deposit_amount_residual = total
        self.show_deposit_amount = True
        self.amount = min(self.deposit_amount_residual, self.amount)

    deposit_amount_residual = fields.Float("Số tiền đặt cọc", compute=_show_deposit_amount_residual, store=False)
    show_deposit_amount = fields.Boolean('Hiện đặt cọc', default=False, store=False)

    @api.onchange('journal_id')
    def _onchange_journal_id(self):
        self.show_deposit_amount = False
        self.amount = self.invoice_id.residual
        super(InvoiceMakePayment, self)._onchange_journal_id()
        if self.journal_id.id == self.session_id.config_id.journal_deposit_id.id:
            self._show_deposit_amount_residual()

    def add_more_payment(self):
        if self.journal_id.id == self.session_id.config_id.journal_deposit_id.id:
            deposit_lines = self.env['pos.customer.deposit'].search([('partner_id', '=', self.invoice_id.partner_id.id)])
            total = 0.0
            for line in deposit_lines:
                total += line.residual
            if self.amount > total:
                raise UserError("Số tiền thanh toán nhiều hơn số tiền đặt cọc của khách hàng.")
            elif self.amount <= 0:
                raise ValidationError("Số tiền thanh toán không hợp lệ.")
            elif self.amount > self.invoice_id.residual:
                raise UserError("Số tiền thanh toán nhiều hơn số nợ của khách hàng.")
            order_id = self.env['pos.order'].search([('name', '=', self.invoice_id.reference)], limit=1)
            # Trừ tiền đặt cọc
            self.env['pos.customer.deposit.line'].create({
                'journal_id': self.journal_id.id,
                'date': date.today(),
                'amount': self.amount,
                'order_id': order_id.id if order_id else None,
                'deposit_id': deposit_lines[0].id,
                'type': 'payment',
                'partner_id': self.invoice_id.partner_id.id,
                'state': 'done'
            })
            # deposit_lines[0].residual -= self.amount
