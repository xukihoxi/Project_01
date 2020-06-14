# -*- coding: utf-8 -*-

from odoo import api, fields, models, SUPERUSER_ID, _
from datetime import date
from odoo.exceptions import UserError, ValidationError, MissingError, except_orm


class ProductPricelist(models.Model):
    _inherit = 'product.pricelist'

    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=100):
        if 'domain_by_session_id' in self._context:
            ObjSession = self.env['pos.session']
            pricelist_ids = []

            session = ObjSession.search([('id', '=', self._context.get('domain_by_session_id', False))], limit=1)
            if not session:
                raise except_orm('Thông báo', 'Không tìm thấy phiên có mã: %s' % (str(self._context.get('domain_by_session_id', False))))
            if not session.config_id:
                raise except_orm('Thông báo', 'Phiên %s chưa có điểm bán hàng' % (str(session.name)))
            if session.config_id.use_pricelist and session.config_id.available_pricelist_ids:
                for available_pricelist in session.config_id.available_pricelist_ids:
                    pricelist_ids.append(available_pricelist.id)

            res = self.search([('id', 'in', pricelist_ids), ('name', 'ilike', name)], limit=limit)
        else:
            res = self.search([('name', 'ilike', name)], limit=limit)
        return res.name_get()

    def name_get(self):
        result = []
        for record in self:
            name = '%s' % (str(record.name))
            result.append((record.id, name))
        return result

