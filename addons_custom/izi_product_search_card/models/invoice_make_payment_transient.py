from odoo import models, fields, api
from datetime import datetime
from odoo.exceptions import UserError, MissingError, ValidationError
from datetime import date, datetime
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT


class InvoiceMakePaymentHistory(models.TransientModel):
    _name = 'invoice.make.payment.transient'
    _description = u'Lịch sử thanh toán công nợ'
    _order = 'create_date desc'

    x_search_id = fields.Many2one('izi.product.search.card')
    invoice_ids = fields.Many2many('account.invoice', string='Account Invoice')
    journal_id = fields.Many2one('account.journal',string ='Account Jouranl')
    amount = fields.Float(digits=(16, 2))
    payment_id = fields.Many2one('account.payment', string='Account Payment')
    payment_date = fields.Datetime(string='Payment Date')
