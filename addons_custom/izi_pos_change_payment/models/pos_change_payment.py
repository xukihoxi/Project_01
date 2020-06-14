# -*- coding: utf-8 -*-

from odoo import models, fields, api

class PosChangePaymemnt(models.Model):
    _name = 'pos.change.payment'

    name = fields.Char("Name")
    statement_line_id = fields.Many2one('account.bank.statement.line', "Statement Line")
    journal_id = fields.Many2one('account.journal', 'Journal')
    statement_id = fields.Many2one('account.bank.statement', "Statement")
    amount = fields.Float("Amount")
    amount_currency = fields.Float("Amount Currency")
    currency_id = fields.Many2one('res.currency', "Currency")
    order_id = fields.Many2one('pos.order', "Order")
    stt = fields.Float("Stt")