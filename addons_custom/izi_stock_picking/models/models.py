# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import except_orm, ValidationError, RedirectWarning


class izi_stock_picking(models.Model):
    _inherit= 'stock.picking'

    @api.multi
    def unlink(self):
        for line in self:
            if line.state != 'draft':
                raise except_orm('Thông báo!', (
                    "Không thể xóa bản ghi ở trạng thái khác bản thảo"))
        return super(izi_stock_picking, self).unlink()


