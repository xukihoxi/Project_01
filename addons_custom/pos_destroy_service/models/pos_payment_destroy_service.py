# -*- coding: utf-8 -*-

from odoo import models, fields, api

class PosPaymentDestroyServiceLine(models.Model):
    _name = 'pos.payment.destroy.service'

    journal_id = fields.Many2one('account.journal', "Journal")
    amount = fields.Float("Amount")
    destroy_service_id = fields.Many2one('pos.destroy.service', "Destroy Service")
    date = fields.Date("Date")


