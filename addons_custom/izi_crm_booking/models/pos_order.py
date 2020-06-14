# -*- coding: utf-8 -*-


from odoo import api,models, fields


class PosOrder(models.Model):
    _inherit = 'pos.order'

    origin_service_booking = fields.Char(string='Origin')

    @api.model
    def create(self, vals):
        res = super(PosOrder, self).create(vals)

        if res.origin_service_booking:
            service_booking = self.env['service.booking'].search([('name', '=', res.origin_service_booking)])
            if len(service_booking) == 1:
                service_booking.ref_order_id = res.id

        return res
