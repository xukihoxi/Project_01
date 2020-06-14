# -*- coding: utf-8 -*-
from odoo import api, fields, models, SUPERUSER_ID, _
from datetime import date
from odoo.exceptions import UserError, ValidationError, MissingError


class BundleTherapyBarem(models.Model):
    _name = 'bundle.therapy.barem'

    name = fields.Char(string='Bundle Therapy Barem')
    value_bundle_max = fields.Float(string='Value Bundle Max')
    value_bundle_min = fields.Float(string='Value Bundle Min')
    bundle_therapy_barem_line_ids = fields.One2many('bundle.therapy.barem.line', 'bundle_therapy_barem_id', string='Bundle Line')
    product_id = fields.Many2one('product.product', string='Service medicine')
    active = fields.Boolean(default=True)
    pos_order_id = fields.Many2one('pos.order', string='Pos Order')

    @api.constrains('value_bundle_max', 'value_bundle_min')
    def _check_value_bundle(self):
        # result = {}
        if self.value_bundle_min and self.value_bundle_max:
            if self.value_bundle_min >= self.value_bundle_max:
                raise ValidationError(_('Lỗi khoảng giá trị Barem!'))
            for barem in self.env['bundle.therapy.barem'].search([('active', '=', True)]):
                if barem.value_bundle_min < self.value_bundle_min < barem.value_bundle_max or barem.value_bundle_min < self.value_bundle_max < barem.value_bundle_max:
                    raise ValidationError(_('Giá trị Barem nhập vào bị trùng với barem khác!'))
                result_1 = barem.value_bundle_min - self.value_bundle_min
                result_2 = barem.value_bundle_max - self.value_bundle_max
                if result_1 != 0 and result_2 != 0 and (result_2 * result_1) <= 0:
                    raise ValidationError(_('Giá trị Barem nhập vào bị trùng với barem khác!'))

class BundleTherapyBaremLine(models.Model):
    _name = 'bundle.therapy.barem.line'

    name = fields.Char(string='Bundle Therapy Barem Line')
    product_id = fields.Many2one('product.product', string='Product')
    uom_id = fields.Many2one('product.uom', string='Unit of  Measure', required=True)
    qty = fields.Integer(string='Qty')
    note = fields.Char(string='Note')
    bundle_therapy_barem_id = fields.Many2one('bundle.therapy.barem')

    @api.onchange('product_id')
    def _onchange_product_id(self):
        if self.product_id:
            self.uom_id = self.product_id.product_tmpl_id.uom_id.id

