# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, except_orm


class IziProductCategory(models.Model):
    _inherit = 'product.category'

    x_category_code = fields.Char(string="Category code")

    # @api.model
    # def create(self, vals):
    #     if len(self.env['product.category'].search([('x_category_code', '=', vals.get("x_category_code").upper())])) != 0:
    #         raise  except_orm('Cảnh báo!', ("The code you entered already exists"))
    #     if ' ' in vals.get('x_category_code'):
    #         raise  except_orm('Cảnh báo!', ("No spaces allowed in Code input"))
    #     vals['x_category_code'] = vals.get('x_category_code').upper()
    #     return super(IziProductCategory,self).create(vals)
    #
    # @api.multi
    # def write(self, vals):
    #     if vals.get("x_category_code"):
    #         if len(self.env['product.category'].search(
    #                 [('x_category_code', '=', vals.get("x_category_code").upper())])) != 0:
    #             raise except_orm('Cảnh báo!', ("The code you entered already exists"))
    #         if ' ' in vals.get('x_category_code'):
    #             raise except_orm('Cảnh báo!', ("No spaces allowed in Code input"))
    #         vals['x_category_code'] = vals.get('x_category_code').upper()
    #     return super(IziProductCategory, self).write(vals)
