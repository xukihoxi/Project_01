# -*- coding: utf-8 -*-


from odoo import fields, models, api, _
from odoo.exceptions import except_orm


class UsingStockMoveLine(models.Model):
    _name = 'izi.using.stock.move.line'
    # _inherit = ['mail.thread', 'mail.activity.mixin']

    def _get_inventory(self, product_id, location_id):
        total_availability = self.env['stock.quant']._get_available_quantity(product_id, location_id)
        return total_availability


    name = fields.Char("Name")
    material_id = fields.Many2one('product.product', "Material",domain=[('type', '!=', 'service')])
    quantity = fields.Float("Quantity")
    quantity_used = fields.Float("Quantity Use")
    uom_id = fields.Many2one('product.uom', 'Product Uom')
    # using_id = fields.Many2one('izi.service.card.using', "Using")
    use_material_id = fields.Many2one('pos.user.material', 'Use Material')
    replace_material_id = fields.Many2one('product.product', "Replace Material", domain=[('type', '!=', 'service')])
    quantity_replace = fields.Float("Quantity Replace")
    uom_replace_id = fields.Many2one('product.uom', 'Product Uom Replace')
    quantity_remain_stock = fields.Float('Quantity Remain Stock')
    quantity_remain_stock_replace = fields.Float("Quantity Remain Stock Replace")
    state = fields.Selection([('ready', "Ready"), ('replace', "Replace"), ('stock_out', "Stock Out")])
    use = fields.Boolean("Use", default=True)


    @api.onchange('replace_material_id')
    def onchange_uom_replace(self):
        self.uom_replace_id = self.replace_material_id.product_tmpl_id.uom_id.id
        for line in self.use_material_id.use_move_line_ids:
            if self.material_id.id == False and self.replace_material_id.id == False:
                break
            if self.material_id.id == False and self.replace_material_id.id != False:
                raise except_orm('Cảnh báo!', ("Bạn không thể chọn sản phẩm thay thế"))
            if line.material_id.id == self.replace_material_id.id:
                self.replace_material_id = False
                raise except_orm('Cảnh báo!', ('Bạn không thể chọn 1 sản phẩm thay thế đã có trong sản phẩm lý thuyết'))

    @api.onchange('material_id')
    def onchange_material_id(self):
        self.uom_id = self.material_id.product_tmpl_id.uom_id.id
        i = 1
        for line in self.use_material_id.use_move_line_ids:
            i += 1
            if i == len(self.use_material_id.use_move_line_ids):
                break
            if self.material_id.id == False:
                break
            if line.material_id.id == self.material_id.id:
                self.material_id = False
                raise except_orm('Cảnh báo!', ('Bạn không thể chọn 1 sản phẩm thay thế đã có trong sản phẩm lý thuyết'))

    @api.onchange('quantity_used')
    def onchange_quantity_use(self):
        if self.quantity_used > 0 and (self.replace_material_id or self.quantity_replace >0):
            self.quantity_used = 0
            warning = {
                'title': 'Cảnh báo!',
                'message': 'Bạn đã nhập nguyên vật liệu thay thế, Không thể sử dụng nguyên vật liệu này'
                }
            return {'warning': warning}
        # if self.quantity_used > self.quantity_remain_stock:
        #     self.quantity_used = 0
        #     warning = {
        #         'title': 'Cảnh báo!',
        #         'message': 'Bạn không thể xuất nguyên vật liệu nhiều hơn số tồn trong kho'
        #     }
        #     return {'warning': warning}

    @api.onchange('replace_material_id', 'quantity_replace')
    def onchange_replace_material(self):
        if self.quantity_used > 0 and (self.replace_material_id or self.quantity_replace >0):
            self.replace_material_id = False
            self.quantity_replace = 0
            warning = {
                'title': 'Cảnh báo!',
                'message': 'Bạn đã nhập số lượng sử dụng, không thể thay thế nguyên liệu'
            }
            return {'warning': warning}
        # if self.quantity_replace > self.quantity_remain_stock:
        #     self.quantity_replace = 0
        #     warning = {
        #         'title': 'Cảnh báo!',
        #         'message': 'Bạn không thể xuất nguyên vật liệu nhiều hơn số tồn trong kho'
        #     }
        #     return {'warning': warning}
        if self.replace_material_id.id == False and self.quantity_replace >0:
            self.quantity_replace = 0
            warning = {
                'title': 'Cảnh báo!',
                'message': 'Bạn không thể xuất nguyên vật liệu nhiều hơn số tồn trong kho'
            }
            return {'warning': warning}

