# -*- coding: utf-8 -*-

from odoo import models, fields, api,_
from datetime import datetime
from odoo.exceptions import ValidationError


class RptServiceWithEmployeDefaultUse(models.TransientModel):
    _name = 'rpt.service.with.employee.default.use'

    def _default_employee(self):
        employee = self.env['hr.employee'].search([('user_id', '=', self.env.uid)], limit=1)
        return employee.id

    from_date = fields.Date("From Date")
    to_date = fields.Date("To Date")
    employee_id = fields.Many2one('hr.employee', string="Employee", default=_default_employee)

    @api.multi
    def create_report(self):
        param_obj = self.env['ir.config_parameter']
        url = param_obj.get_param('birt_url')
        if not url:
            raise ValidationError(_(u"Bạn phải cấu hình birt_url"))
        report_name = "rpt_sevice_with_employee.rptdesign"
        str_from_date = datetime.strptime(self.from_date, "%Y-%m-%d").strftime("%d/%m/%Y")
        str_to_date = datetime.strptime(self.to_date, "%Y-%m-%d").strftime("%d/%m/%Y")
        param_str1 = "&from_date=" + str_from_date + "&to_date=" + str_to_date
        param_str3 = "&employee_id=" + str(self.employee_id.id)

        param_str = param_str1 + param_str3
        return {
            'type': 'ir.actions.act_url',
            'url': url + "/report/frameset?__report=report_amia/" + report_name + param_str,
            'target': 'new',
        }


    @api.multi
    def create_report_excel(self):
        param_obj = self.env['ir.config_parameter']
        url = param_obj.get_param('birt_url')
        if not url:
            raise ValidationError(_(u"Bạn phải cấu hình birt_url"))
        report_name = "rpt_sevice_with_employee.rptdesign"
        str_from_date = datetime.strptime(self.from_date, "%Y-%m-%d").strftime("%d/%m/%Y")
        str_to_date = datetime.strptime(self.to_date, "%Y-%m-%d").strftime("%d/%m/%Y")
        param_str1 = "&from_date=" + str_from_date + "&to_date=" + str_to_date
        param_str3 = "&employee_id=" + str(self.employee_id.id)
        param_str = param_str1 + param_str3
        return {
            'type': 'ir.actions.act_url',
            'url': url + "/report/frameset?__report=report_amia/" + report_name + param_str + '&__format=xlsx',
            'target': 'self',
        }