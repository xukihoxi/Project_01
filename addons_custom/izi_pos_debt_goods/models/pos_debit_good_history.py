# -*- coding: utf-8 -*-
from werkzeug._internal import _log
from odoo import models, fields, api
from odoo.exceptions import ValidationError
from odoo.tools.translate import _
from odoo.exceptions import except_orm, Warning as UserError


class DebitGoodsHis(models.Model):
    _name = "pos.debit.good.history"

    debit_id = fields.Many2one('pos.debit.good')

    date = fields.Date(string='Date')
    picking_id = fields.Many2one('stock.picking',string='Picking')
    signature_image = fields.Binary("Signature Image", default=False, attachment=True, track_visibility='onchange')
    note = fields.Text('Note')

    @api.multi
    def action_done(self):
        if self.debit_id:
            i = 0
            for line in self.debit_id.line_ids:
                if line.qty_debit > 0:
                    i += 1
            if i == 0:
                self.debit_id.state = 'done'
            else:
                self.debit_id.state = 'debit'
            return True


