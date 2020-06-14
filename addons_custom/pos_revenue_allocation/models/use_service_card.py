# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import except_orm, ValidationError, UserError


class UseService(models.Model):
    _inherit = 'izi.service.card.using'

    x_user_id = fields.Many2many('hr.employee')

    @api.onchange('user_id')
    def _onchange_default_emp(self):
        #mặc định lấy nhân viên hưởng doanh thu là người người hưởng doanh thu dự kiến
        context = self._context
        if self.user_id:
            lead_employee_ids = context.get('lead_employee_ids', False)
            if lead_employee_ids:
                self.x_user_id = lead_employee_ids
            else:
                self.x_user_id = False

    @api.multi
    def action_confirm_service(self):
        res = super(UseService,self).action_confirm_service()
        if self.pos_order_id:
            if self.x_user_id:
                self.pos_order_id.x_user_id = self.x_user_id
                self.pos_order_id._auto_allocation()
        return res

    @api.multi
    def action_validate_service(self):
        res = super(UseService, self).action_validate_service()
        if self.pos_order_id:
            if self.x_user_id:
                self.pos_order_id.x_user_id = self.x_user_id
                self.pos_order_id._auto_allocation()
        return res
