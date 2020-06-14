# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import except_orm


class InheritPartner(models.Model):
    _inherit = 'res.partner'


    @api.multi
    def action_search(self):
        search_card_obj = self.env['izi.product.search.card'].create({
            'brand_id': self.x_brand_id.id,
            'serial': self.phone,
        })
        search_card_obj.action_check_card()
        ctx = self.env.context.copy()
        # ctx.update(
        #     {'default_serial': self.partner_id.phone})
        view = self.env.ref('izi_product_search_card.izi_product_search_card_form')
        return {
            'name': _('Search partner'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'izi.product.search.card',
            'views': [(view.id, 'form')],
            'view_id': view.id,
            'target': '',
            'context': ctx,
            'res_id': search_card_obj.id,
        }
