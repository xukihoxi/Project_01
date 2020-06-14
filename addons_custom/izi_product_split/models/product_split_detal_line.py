# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import except_orm



class ProductSplittingLine(models.Model):
    _name = "izi.product.split.detail.line"

    product_id = fields.Many2one(comodel_name='product.product', string="Split to product", required=True)
    product_uom_id = fields.Many2one(comodel_name='product.uom', string="Product UoM", required=True)
    product_uom_qty = fields.Float(string="Quantity", required=True)
    splitting_id = fields.Many2one('izi.product.split.detail', "Belong to Splitting", required=True)

    def check_product(self):
        if self.product_id and self.product_uom_qty <= 0:
            raise except_orm('Cảnh báo!', ('Thành phẩm sau khi tách phải có số lượng lớn hơn 0.'))
        if self.product_id:
            if self.product_id == self.splitting_id.product_id:
                raise except_orm('Cảnh báo!', ('Thành phẩm sau khi tách không được trùng với sản phẩm tách.'))
        return True

    @api.onchange('product_id')
    def _onchange_product_uom(self):
        if self.product_id:
            self.product_uom_id = self.product_id.product_tmpl_id.uom_id.id
