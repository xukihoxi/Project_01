# -*- coding: utf-8 -*-

from odoo import models, fields, api,_
from datetime import datetime
from odoo.exceptions import ValidationError


class RptServiceWithEmploye(models.TransientModel):
    _name = 'rpt.service.with.employee'

    from_date = fields.Date("From Date")
    to_date = fields.Date("To Date")
    employee_ids = fields.Many2many('hr.employee', string="Employee")
    select_all = fields.Boolean('All Employee')

    @api.onchange('select_all')
    def _onchange_select_all(self):
        #Lấy hết các bác sĩ
        #lấy hết các nhân viên trong các phòng ban liên kết với các chi nhánh mà user đang quản lý
        EmployeeObj = self.env['hr.employee']
        UserObj = self.env['res.users']
        user = UserObj.search([('id', '=', self._uid)], limit=1)
        if self.select_all:
            self.employee_ids = EmployeeObj.search(['|', ('department_id.x_branch_id', 'in', user.branch_ids.ids), ('job_id.x_code', '=', 'BS')])
        else:
            self.employee_ids = False

    @api.onchange('employee_ids')
    def _onchange_employee_ids(self):
        user = self.env['res.users'].search([('id', '=', self._uid)], limit=1)
        return {
            'domain': {
                'employee_ids': ['|', ('department_id.x_branch_id', 'in', user.branch_ids.ids), ('job_id.x_code', '=', 'BS')]
            }
        }

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
        param_str3 = "&employee_id="
        # if (self.select_all == True):
        #     list_id = ''
        #     employee = self.env['hr.employee'].search([])
        #     for employee_id in employee:
        #         list_id += ',' + str(employee_id.id)
        #     param_str3 += (list_id[1:])
        # else:
        list_id = ''
        for loc_id in self.employee_ids:
            list_id += ',' + str(loc_id.id)
        param_str3 += (list_id[1:])
        param_str = param_str1 + param_str3
        return {
            'type': 'ir.actions.act_url',
            'url': url + "/report/frameset?__report=report_amia/" + report_name + param_str,
            'target': 'new',
        }
        # return {
        #     "type": "ir.actions.client",
        #     'name': 'Báo cáo',
        #     'tag': 'BirtViewerAction',
        #     'target': 'new',
        #     'context': {'birt_link': url + "/report/frameset?__report=report_amia/" + report_name + param_str}
        # }

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
        param_str3 = "&employee_id="
        # if (self.select_all == True):
        #     list_id = ''
        #     employee = self.env['hr.employee'].search([])
        #     for employee_id in employee:
        #         list_id += ',' + str(employee_id.id)
        #     param_str3 += (list_id[1:])
        # else:
        list_id = ''
        for loc_id in self.employee_ids:
            list_id += ',' + str(loc_id.id)
        param_str3 += (list_id[1:])
        param_str = param_str1 + param_str3
        return {
            'type': 'ir.actions.act_url',
            'url': url + "/report/frameset?__report=report_amia/" + report_name + param_str + '&__format=xlsx',
            'target': 'self',
        }