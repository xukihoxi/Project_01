# -*- coding: utf-8 -*-

from odoo import models, fields, api

class CodeCard(models.Model):
    _inherit = 'izi.product.release'

    @api.multi
    def action_to_print(self):
        return {
            'type': 'ir.actions.act_url',
            'url': 'report/pdf/izi_product_release.report_template_code_card_view/%s' %(self.id),
            'target': 'new',
            'res_id': self.id,
        }