# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models


class ProductTemplate(models.Model):
    _inherit = "product.template"

    bom_service_ids = fields.One2many('service.bom', 'product_tmpl_id', 'Bill of Materials')
    bom_service_count = fields.Integer('# Bill of Material', compute='_compute_bom_service_count')
    x_type_service = fields.Selection([('spa', "Spa"), ('clinic', "Clinic"), ('none', "None")], default='none')
    produce_delay = fields.Float(
        'Manufacturing Lead Time', default=0.0,
        help="Average delay in days to produce this product. In the case of multi-level BOM, the manufacturing lead times of the components will be added.")

    def _compute_bom_service_count(self):
        read_group_res = self.env['service.bom'].read_group([('product_tmpl_id', 'in', self.ids)], ['product_tmpl_id'], ['product_tmpl_id'])
        mapped_data = dict([(data['product_tmpl_id'][0], data['product_tmpl_id_count']) for data in read_group_res])
        for product in self:
            product.bom_service_count = mapped_data.get(product.id, 0)


class ProductProduct(models.Model):
    _inherit = "product.product"

    bom_service_count = fields.Integer('# Bill of Material', compute='_compute_bom_service_count')

    def _compute_bom_service_count(self):
        # read_group_res: BOM where product_id is set
        # read_group_res_tmpl: BOM where product_tmpl_id is set and product_id is not set
        # The total count is the sum of both.
        read_group_res = self.env['service.bom'].read_group([('product_id', 'in', self.ids)], ['product_id'], ['product_id'])
        mapped_data = dict([(data['product_id'][0], data['product_id_count']) for data in read_group_res])
        read_group_res_tmpl = self.env['service.bom'].read_group([
            ('product_tmpl_id', 'in', self.mapped('product_tmpl_id.id')), ('product_id', '=', False)
        ], ['product_tmpl_id'], ['product_tmpl_id'])
        mapped_data_tmpl = dict([(data['product_tmpl_id'][0], data['product_tmpl_id_count']) for data in read_group_res_tmpl])
        for product in self:
            product.bom_service_count = mapped_data.get(product.id, 0) + mapped_data_tmpl.get(product.product_tmpl_id.id, 0)

    @api.multi
    def action_view_bom(self):
        action = self.env.ref('izi_use_service_card.product_open_service_bom').read()[0]
        template_ids = self.mapped('product_tmpl_id').ids
        # bom specific to this variant or global to template
        action['context'] = {
            'default_product_tmpl_id': template_ids[0],
            'default_product_id': self.ids[0],
        }
        action['domain'] = ['|', ('product_id', 'in', self.ids), '&', ('product_id', '=', False), ('product_tmpl_id', 'in', template_ids)]
        return action

