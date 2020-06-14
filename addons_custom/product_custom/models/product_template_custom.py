# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, except_orm
from . import utils


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    x_net_weight = fields.Float('Net Weight',
        help="The weight of the contents in Kg, not including any packaging, etc.")
    default_code = fields.Char('Internal Reference', compute='_compute_default_code',
        inverse='_set_default_code', store=True, )
    x_guarantee = fields.Boolean('Guarantee', default=False)
    x_counted_work = fields.Boolean("Count Work", default=True)
    x_use_doctor = fields.Boolean(string="Use doctor")

    # @api.model
    # def create(self, vals):
    #     if vals.get('type') == 'service':
    #         code = utils.get_sequence(self._cr, 1, 'DV',3)
    #         while len(self.env['product.template'].search([('default_code', '=', code)])) != 0:
    #             code = utils.get_sequence(self._cr, 1,  'DV',3)
    #         vals['default_code'] = code
        # else:
        #     category_id = self.env['product.category'].search([('id', '=', vals.get('categ_id'))])
        #     if category_id.x_category_code == '120':
        #         code = utils.get_sequence(self._cr, 1, 'SP', 5)
        #         while len(self.env['product.template'].search([('default_code', '=', code)])) != 0:
        #             code = utils.get_sequence(self._cr, 1, 'SP', 5)
        #         vals['default_code'] = code
        #     if category_id.x_category_code == '121' or category_id.x_category_code == '122':
        #         code = utils.get_sequence(self._cr, 1, 'SPDC', 3)
        #         while len(self.env['product.template'].search([('default_code', '=', code)])) != 0:
        #             code = utils.get_sequence(self._cr, 1, 'SPDC', 3)
        #         vals['default_code'] = code
        # return super(ProductTemplate, self).create(vals)




