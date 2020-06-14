# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from datetime import datetime
from odoo.exceptions import UserError, MissingError, ValidationError
from datetime import date, datetime
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT


class DebitInvoice(models.TransientModel):
    _name = 'invoice.customer.transient'

    x_search_id = fields.Many2one('izi.product.search.card')
    order_id = fields.Many2one('pos.order','Order')
    number = fields.Char('Number')
    amount_total = fields.Float('Tổng')
    residual = fields.Float('Residual')
    date_invoice = fields.Datetime('Date invoice')
    date_due = fields.Datetime('Date due')
    invoice_id = fields.Many2one('account.invoice', "Invoice")
    state = fields.Selection(
        [('draft', 'Draft'),
         ('open', 'Open'),
         ('paid', 'Paid'),
         ('cancel', 'Cancelled'), ],
        'Status')

    @api.multi
    def action_preview_invoice(self):
        view = self.sudo().env.ref('izi_product_search_card.invoice_supplier_form_view_transient')
        return {
            'name': _('Account Invoice?'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'account.invoice',
            'views': [(view.id, 'form')],
            'view_id': view.id,
            'target': 'new',
            'res_id': self.invoice_id.id,
            'context': { 'create': False,
                        'delete': False,
                        'edit': False
                                         }
        }