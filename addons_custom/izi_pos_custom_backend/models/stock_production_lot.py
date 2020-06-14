# -*- coding: utf-8 -*-

from odoo import models, fields, api
from datetime import datetime
from odoo.exceptions import UserError, MissingError, ValidationError
from datetime import date, datetime
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT


class StockProductionLot(models.Model):
    _inherit = 'stock.production.lot'

    @api.multi
    def _invalidate_vc_code(self, partner_id, statement_id=None):
        self.ensure_one()
        if self.product_id.x_type_card != 'pmh':
            raise MissingError("Mã phiếu mua hàng không tồn tại!")
        else:
            if statement_id:
                count_used = self.env['account.bank.statement.line'].search_count(
                    [('x_vc_id', '=', self.id), ('id', '!=', statement_id),
                     ('pos_statement_id.state', 'in', ('draft', 'to_confirm', 'to_approve'))])
            else:
                count_used = self.env['account.bank.statement.line'].search_count([('x_vc_id', '=', self.id), (
                'pos_statement_id.state', 'in', ('draft', 'to_confirm', 'to_approve'))])
            if count_used > 0:
                raise UserError("Phiếu mua hàng %s đã được sử dụng!" % self.name)
        if self.x_status == 'new':
            raise UserError("Phiếu mua hàng %s chưa được kích hoạt!" % self.name)
        elif self.x_status == 'actived':
            raise UserError("Phiếu mua hàng %s chưa được bán!" % self.name)
        elif self.x_status == 'used':
            raise UserError("Phiếu mua hàng %s đã được sử dụng!" % self.name)
        elif self.x_status == 'destroy':
            raise UserError("Phiếu mua hàng %s đã bị huỷ!" % self.name)
        elif self.life_date and datetime.strptime(self.life_date, DEFAULT_SERVER_DATETIME_FORMAT).date() < date.today():
            raise UserError("Phiếu mua hàng %s đã quá hạn sử dụng!" % self.name)
        elif self.x_release_id.use_type == '0' and self.x_customer_id.id != partner_id:
            raise UserError("Phiếu mua hàng %s thuộc khách hàng khác và chỉ sử dụng đúng định danh!" % self.name)
