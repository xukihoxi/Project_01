# -*- coding: utf-8 -*-

from odoo import models, fields, api,_
from odoo.tools.float_utils import float_compare, float_is_zero, float_round
from odoo.exceptions import UserError, AccessError

class IziStockTransfer(models.Model):
    _inherit = 'izi.stock.transfer'

    @api.multi
    def action_receive(self):
        transfer = super(IziStockTransfer, self).action_receive()
        request_id = self.env['izi.stock.request'].search([('name', '=', self.origin)])
        if request_id.id != False:
            request_id.state = 'done'
        return transfer