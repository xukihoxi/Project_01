# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import except_orm




class ProductSplitting(models.Model):
    _name = "izi.product.split.detail"
    _order = 'create_date desc'
    name = fields.Char("Name", default="/")
    split_total_id = fields.Many2one('izi.product.split', "The split")
    product_id = fields.Many2one(comodel_name='product.product', string="Product to split", required=True)
    product_uom_id = fields.Many2one(comodel_name='product.uom', string="Product UoM", required=True)
    product_uom_qty = fields.Float(string="Quantity", required=True)
    state = fields.Selection(selection=(('draft', 'Draft'), ('done', 'Done')), string="State", default='draft')
    out_put_product_lines = fields.One2many('izi.product.split.detail.line', 'splitting_id', "Out put products")
    note = fields.Text("Note")
    date = fields.Date("Date", related='split_total_id.split_date')

    @api.onchange('product_id')
    def _onchange_product_uom(self):
        if self.product_id:
            self.product_uom_id = self.product_id.product_tmpl_id.uom_id.id
    @api.multi
    def action_set_state(self):
        self.state = 'done'

    def check_product(self):
        if self.product_id.id != False and self.product_uom_qty <= 0:
            raise except_orm('Cảnh báo!', ('Sản phẩm đem tách phải có số lượng lớn hơn 0.'))
        return True


