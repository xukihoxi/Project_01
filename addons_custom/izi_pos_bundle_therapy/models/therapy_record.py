# -*- coding: utf-8 -*-
from odoo import api, fields, models, SUPERUSER_ID, _
from datetime import date, datetime
from odoo.exceptions import UserError, ValidationError, MissingError


class TherapyRecord(models.Model):
    _inherit = 'therapy.record'

    bundle_therapy_ids = fields.One2many('bundle.therapy', 'therapy_record_id', 'Bundle Therapy')  # gói trị liệu

    def create_order(self):
        self.ensure_one()
        ctx = self.env.context.copy()
        ctx.update({
            'default_partner_id': self.partner_id.id,
            'default_x_therapy_record_id': self.id,
            'default_categ_id': self.categ_id.id,
        })
        view = self.env.ref('point_of_sale.view_pos_pos_form')
        return {
            'name': _('Pos Order'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'pos.order',
            'views': [(view.id, 'form')],
            'view_id': view.id,
            'target': '',
            'context': ctx,
        }