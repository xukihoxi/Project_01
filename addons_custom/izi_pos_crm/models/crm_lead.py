# -*- coding: utf-8 -*-#

from odoo import models, fields, api
from odoo.exceptions import except_orm, ValidationError


class CrmLead(models.Model):
    _inherit = 'crm.lead'

    @api.multi
    def action_assign_lead(self):
        ctx = self.env.context.copy()
        print(ctx)
        view = self.env.ref('izi_pos_crm.crm_lead_form_inherit')
        return {
            'name': 'Giao lead',
            'type': 'ir.actions.act_window',
            'res_model': 'crm.lead',
            'view_mode': 'form',
            'view_type': 'form',
            'views': [(view.id, 'form')],
            'view_id': view.id,
            'target': 'new',
            'res_id': self.id,
            'context': ctx
        }

    @api.multi
    def action_confirm_assign_lead(self):
        ctx = self.env.context.copy()
        if 'reception_customer_id' in ctx and ctx['reception_customer_id']:
            reception_customer = self.env['reception.customer'].search([('id', '=', ctx['reception_customer_id'])])
            if not reception_customer: raise except_orm("Thông báo", "Không tìm thấy \"Tiếp đón khách hàng\" có id: %s" % (str(ctx['reception_customer_id'])))

            reception_customer.write({
                'lead_ids': [(6, 0, [self.id])],
                'state': 'done',
            })

            if self.service_booking_ids:
                for service_booking in self.service_booking_ids:
                    if service_booking.state == 'ready':
                        service_booking.write({'state': 'met'})
            self.write({
                'x_state': 'to_shop'
            })