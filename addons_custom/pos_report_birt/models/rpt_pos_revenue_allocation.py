# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from datetime import datetime
from odoo.exceptions import ValidationError


class RptRevenueAllocation(models.TransientModel):
    _name = 'rpt.pos.revenue.allocation'

    from_date = fields.Date("From Date")
    to_date = fields.Date("To Date")
    employee_ids = fields.Many2many('hr.employee', string="Employee")
    config_ids = fields.Many2many('pos.config', string="Pos Config")
    select_all = fields.Boolean('All Pos config')

    @api.onchange('select_all')
    def _onchange_select_all(self):
        user = self.env['res.users'].search([('id', '=', self._uid)], limit=1)
        if self.select_all:
            self.config_ids = self.env['pos.config'].search([('pos_branch_id', 'in', user.branch_ids.ids)])
        else:
            self.config_ids = False

    @api.onchange('config_ids')
    def _onchange_config_ids(self):
        user = self.env['res.users'].search([('id', '=', self._uid)], limit=1)
        return {
            'domain': {
                'config_ids': [('pos_branch_id', 'in', user.branch_ids.ids)]
            }
        }

    @api.multi
    def create_report(self):
        param_obj = self.env['ir.config_parameter']
        url = param_obj.get_param('birt_url')
        if not url:
            raise ValidationError(_(u"Bạn phải cấu hình birt_url"))
        report_name = "rpt_pos_revenue_allocation.rptdesign"
        param_str1 = "&from_date=" + self.from_date + "&to_date=" + self.to_date
        param_str3 = "&config_id="
        param_str4 = "&employee_id="
        employee_id = '0'
        config_id = '0'
        if self.select_all == False:
            list = ''
            list_emp = ''
            if self.config_ids:
                for config in self.config_ids:
                    list += ',' + str(config.id)
                    # user_ids = self.env['res.users'].search([('x_pos_config_id', '=', config.id)])
                    # for user in user_ids:
                    #     employee_ids = self.env['hr.employee'].search(['|', ('user_id', '=', user.id), ('x_user_ids', 'in', [user.id])])
                    #     for emp in employee_ids:
                    department_ids = self.env['hr.department'].search(
                        [('x_branch_id', '=', config.pos_branch_id.id)])
                    for line in department_ids:
                        ids_o2m = self.env['hr.employee'].search([('department_id', '=', line.id)])
                        for emp in ids_o2m:
                            list_emp += ',' + str(emp.id)
                employee_id = (list_emp[1:])
                config_id = (list[1:])
            if self.employee_ids:
                employee = ''
                config = ''
                for emp in self.employee_ids:
                    employee += ',' + str(emp.id)
                #     # config += ',' + str(emp.user_id.x_pos_config_id.id)
                #     for user in emp.x_user_ids:
                #         config += ',' + str(user.x_pos_config_id.id)
                # if config == '':
                #     for config1 in self.config_ids:
                #         list += ',' + str(config1.id)
                # if config == '':
                #     config_id = (list[1:])
                # else:
                #     config_id = (config[1:])
                employee_id = (employee[1:])
                # config_id = (config[1:])
        param_str = param_str1 + param_str4 + employee_id
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
        report_name = "rpt_pos_revenue_allocation.rptdesign"
        param_str1 = "&from_date=" + self.from_date + "&to_date=" + self.to_date
        param_str3 = "&config_id="
        param_str4 = "&employee_id="
        employee_id = '0'
        config_id = '0'
        if self.select_all == False:
            list = ''
            list_emp = ''
            if self.config_ids:
                for config in self.config_ids:
                    list += ',' + str(config.id)
                    # user_ids = self.env['res.users'].search([('x_pos_config_id', '=', config.id)])
                    # for user in user_ids:
                    #     employee_ids = self.env['hr.employee'].search(['|', ('user_id', '=', user.id), ('x_user_ids', 'in', [user.id])])
                    #     for emp in employee_ids:
                    department_ids = self.env['hr.department'].search(
                        [('x_branch_id', '=', config.pos_branch_id.id)])
                    for line in department_ids:
                        ids_o2m = self.env['hr.employee'].search([('department_id', '=', line.id)])
                        for emp in ids_o2m:
                            list_emp += ',' + str(emp.id)
                employee_id = (list_emp[1:])
                # config_id = (list[1:])
            if self.employee_ids:
                employee = ''
                config = ''
                for emp in self.employee_ids:
                    employee += ',' + str(emp.id)
                #     # config += ',' + str(emp.user_id.x_pos_config_id.id)
                #     for user in emp.x_user_ids:
                #         config += ',' + str(user.x_pos_config_id.id)
                # if config == '':
                #     for config1 in self.config_ids:
                #         list += ',' + str(config1.id)
                # if config == '':
                #     config_id = (list[1:])
                # else:
                #     config_id = (config[1:])
                employee_id = (employee[1:])
                # config_id = (config[1:])
        param_str = param_str1 + param_str4 + employee_id
        return {
            'type': 'ir.actions.act_url',
            'url': url + "/report/frameset?__report=report_amia/" + report_name + param_str + '&__format=xlsx',
            'target': 'self',
        }
