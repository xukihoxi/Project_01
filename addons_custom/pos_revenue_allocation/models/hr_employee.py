# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import except_orm, ValidationError, UserError

class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    x_user_ids = fields.Many2many('res.users', 'res_user_hr_employee_rel', 'employee_id', 'user_id', string="Những người dùng liên quan")

