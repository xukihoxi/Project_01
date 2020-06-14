# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class StockBackorder(models.TransientModel):
    _inherit = 'stock.backorder.confirmation'

    @api.one
    def _process(self, cancel_backorder=False):
        self.pick_ids.action_done()
        backorder_id = self.env['stock.picking'].search([('backorder_id', '=', self.pick_ids.id)])
        for pick_id in self.pick_ids:
            backorder_pick = self.env['stock.picking'].search([('backorder_id', '=', pick_id.id)])
            pos = self.env['pos.order'].search([('name', '=', backorder_pick.origin)])
            if pos:
                pos.write({'picking_id': [(4, backorder_pick.id)]})
        if cancel_backorder:
            for pick_id in self.pick_ids:
                backorder_pick = self.env['stock.picking'].search([('backorder_id', '=', pick_id.id)])
                backorder_pick.action_cancel()
                pick_id.message_post(body=_("Back order <em>%s</em> <b>cancelled</b>.") % (backorder_pick.name))
        return backorder_id.id

    def process(self):
        obj = self._process()
        view = self.env.ref('stock.view_picking_form')
        return {
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'stock.picking',
            'views': [(view.id, 'form')],
            'view_id': view.id,
            'res_id': obj[0],
            'target': '',
        }
