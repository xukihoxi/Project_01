# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import UserError, MissingError, ValidationError, except_orm
from datetime import date, datetime
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT


class PosMakePayment(models.TransientModel):
    _inherit = 'pos.make.payment'

    # @api.multi
    # def check(self):
    #     self.ensure_one()
    #     order = self.env['pos.order'].browse(self.env.context.get('active_id', False))
    #
    #     return super(PosMakePayment, self.with_context(context)).check()

    def allowed_products_two_lines(self):
        context = self.env.context
        order = self.env['pos.order'].browse(context.get('active_id', False))
        if order.x_therapy_record_id:
            check = False
        else:
            check = True
        return check