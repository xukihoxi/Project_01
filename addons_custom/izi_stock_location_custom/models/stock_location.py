# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, except_orm


class IziStockLocation(models.Model):
    _inherit = 'stock.location'

    x_code = fields.Char(string="Code")
    user_ids = fields.Many2many('res.users', string='Users')

    @api.model
    def create(self, vals):
        if vals.get("x_code") != None:
            if len(self.env['stock.location'].search([('x_code', '=', vals.get("x_code").upper())])) != 0:
                raise  except_orm('Cảnh báo!', ("The code you entered already exists"))
            if ' ' in vals.get('x_code'):
                raise  except_orm('Cảnh báo!', ("No spaces allowed in Code input"))
            vals['x_code'] = vals.get('x_code').upper()
        return super(IziStockLocation,self).create(vals)

    @api.multi
    def write(self, vals):
        if vals.get("x_code") != None:
            if len(self.env['stock.location'].search([('x_code', '=', vals.get("x_code").upper())])) != 0:
                raise except_orm('Cảnh báo!', ("The code you entered already exists"))
            if ' ' in vals.get('x_code'):
                raise except_orm('Cảnh báo!', ("No spaces allowed in Code input"))
            vals['x_code'] = vals.get('x_code').upper()
        return super(IziStockLocation, self).write(vals)



