# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from datetime import date, datetime
from odoo.exceptions import except_orm, UserError, MissingError, ValidationError

class UseServiceCard(models.Model):
    _inherit = 'izi.service.card.using'


    @api.multi
    def action_confirm_service(self):
        res = super(UseServiceCard, self).action_confirm_service()
        order_id = self.pos_order_id
        for line in order_id.statement_ids:
            if line.journal_id.id in self.pos_session_id.config_id.x_journal_currency_ids.ids:
                for i in self.pos_payment_service_ids:
                    if line.journal_id.id == i.journal_id.id and i.amount == line.amount:
                        line.update({
                            'x_amount_currency': i.x_money_multi,
                            'x_currency_id': i.x_currency_id.id,
                            'x_currency_rate_id':i.x_currency_rate_id.id,
                        })
        return res