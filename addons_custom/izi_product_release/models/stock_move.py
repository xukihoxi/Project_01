# -*- coding: utf-8 -*-

from odoo import models, fields, api

class IziStockMove(models.Model):
    _inherit = 'stock.move'

    x_release_id = fields.Many2one('izi.product.release',string='Release')

class StockPicking(models.Model):
    _inherit = 'stock.picking'

    @api.multi
    def button_validate(self):
        sp = super(StockPicking,self).button_validate()
        release = self.env['izi.product.release'].search([('name','=', self.origin)],limit=1)
        if release.id != 0:
            release.state = 'done'
        return sp

    @api.multi
    def action_cancel(self):
        sp = super(StockPicking, self).action_cancel()
        release = self.env['izi.product.release'].search([('name', '=', self.origin)], limit=1)
        if release.id != 0:
            release.state = 'done'
        return sp