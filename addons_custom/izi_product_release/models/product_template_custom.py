# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import except_orm


class IziProductTemplateCustom(models.Model):
    _inherit = 'product.template'

    x_type_card = fields.Selection([('none', 'None'),('tbh', 'Thẻ bào hành'), ('tdt', 'Thẻ đổ tồn'),
        ('tdv', 'Thẻ dịch vụ'),('pmh', 'Phiếu mua hàng')], string="Type Card", default='none')
    x_amount = fields.Float('Amount')
    x_discount = fields.Float('Discount')

    @api.model
    def create(self, vals):
        if vals.get("x_type_card") == 'pmh':
            if vals.get("x_amount") == 0.0 and vals.get("x_discount") == 0.0:
                raise except_orm('Cảnh báo!', _("Loại thẻ là phiếu mua hàng, bạn cần thêm tổng tiền hoặc phần trăm giảm giá cho phiếu này!"))
            if vals.get("x_amount") < 0.0 or vals.get("x_discount") < 0.0 :
                raise except_orm('Cảnh báo!', _("Loại thẻ là phiếu mua hàng, tổng tiền hoặc phần trăm giảm giá của phiếu này phải lớn hơn 0!"))
        return super(IziProductTemplateCustom,self).create(vals)