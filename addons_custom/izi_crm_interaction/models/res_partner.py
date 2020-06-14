# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import ValidationError, except_orm
from datetime import datetime


class Partner(models.Model):
    _inherit = 'res.partner'

    x_interaction_ids = fields.One2many('partner.interaction', 'partner_id', string='Interaction')

    x_interaction_count = fields.Integer(string='Count interaction', compute='_compute_interaction_count')

    @api.multi
    def action_view_interaction(self):
        type_remarketing = self.env['partner.interaction.type'].search([('name', '=', 'Remarketing')])
        if not type_remarketing: raise except_orm('Thông báo', 'Chưa cấu hình loại tương tác khách hàng là: Remarketing')

        # action = self.env.ref('izi_crm_interaction.partner_interaction_action_window').read()[0]
        # interactions = self.mapped('x_interaction_ids')
        # if len(interactions) > 1:
        #     action['domain'] = [('id', 'in', interactions.ids)]
        # elif interactions:
        #     # action['views'] = [(self.env.ref('izi_crm_interaction.partner_interaction_form_view').id, 'form')]
        #     action['res_id'] = interactions.id
        # else:
        #     action['domain'] = [('id', '=', 0)]
        # return action

    @api.depends('x_interaction_ids')
    def _compute_interaction_count(self):
        for s in self:
            s.x_interaction_count = len(s.x_interaction_ids)