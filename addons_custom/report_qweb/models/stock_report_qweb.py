# -*- coding: utf-8 -*-

from odoo import models, fields, api


class ReportStockPickingQweb(models.Model):
    _inherit = 'stock.picking'

    @api.multi
    def action_print_picking(self):
        if self.picking_type_id.code == 'incoming':
            return {
                'type': 'ir.actions.act_url',
                'url': 'report/pdf/report_qweb.report_template_stock_picking_incoming_view/%s' % (self.id),
                'target': 'new',
                'res_id': self.id,
            }
        elif self.picking_type_id.code == 'outgoing':
            return {
                'type': 'ir.actions.act_url',
                'url': 'report/pdf/report_qweb.report_template_stock_picking_outgoing_view/%s' % (self.id),
                'target': 'new',
                'res_id': self.id,
            }
        else:
            return {
                'type': 'ir.actions.act_url',
                'url': 'report/pdf/report_qweb.izi_report_template_stock_picking_internal_view/%s' % (self.id),
                'target': 'new',
                'res_id': self.id,
            }


    def _name_qweb(self):
        user_id = self.env['res.users'].search([('id', '=', self.env.uid)], limit=1)
        return user_id.name
