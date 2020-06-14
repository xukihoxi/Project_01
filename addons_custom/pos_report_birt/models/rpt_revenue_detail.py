# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from datetime import datetime
from odoo.exceptions import ValidationError, except_orm


class RptRevenueAllocationDetail(models.TransientModel):
    _name = 'rpt.revenue.allocation.detail'

    from_date = fields.Date("From Date")
    to_date = fields.Date("To Date")
    employee_ids = fields.Many2many('hr.employee', string="Employee")
    crm_team_ids = fields.Many2many('crm.team', string="Teams")
    select_all = fields.Boolean('All Team')
    select_all_employee = fields.Boolean('Select all employee')

    @api.onchange('select_all')
    def _onchange_select_all(self):
        if not self.select_all:
            self.crm_team_ids = False
        else:
            UserObj = self.env['res.users']
            TeamObj = self.env['crm.team']

            user = UserObj.search([('id', '=', self._uid)], limit=1)
            if not user.branch_ids: raise except_orm('Thông báo', 'Người dùng %s chưa chọn chi nhánh cho phép. Vui lòng liên hệ quản trị để được giải quyết' % (
                                                                   str(user.name)))
            for branch in user.branch_ids:
                if not branch: raise except_orm('Thông báo', 'Chi nhánh %s chưa chọn thương hiệu. Vui lòng liên hệ quản trị để được giải quyết' % (
                                                                        str(branch.name)))
            branch_ids = [user.branch_id and user.branch_id.id or 0]
            for branch in user.branch_ids:
                branch_ids.append(branch.id)
            team_ids = TeamObj.get_team_ids_by_branches(branch_ids)

            self.crm_team_ids = TeamObj.search([('id', 'in', team_ids)])

    @api.onchange('select_all_employee')
    def _onchange_select_all_employee(self):
        UserObj = self.env['res.users']
        TeamObj = self.env['crm.team']
        EmployeeObj = self.env['hr.employee']

        if not self.select_all_employee:
            self.employee_ids = False
        else:
            employee_ids = []

            group_consultant = UserObj.has_group('izi_res_permissions.group_consultant')
            group_therapist = UserObj.has_group('izi_res_permissions.group_therapist')

            group_business_manager = UserObj.has_group('izi_res_permissions.group_business_manager')
            group_revenue_accountant = UserObj.has_group('izi_res_permissions.group_revenue_accountant')
            group_cost_accountant = UserObj.has_group('izi_res_permissions.group_cost_accountant')
            group_revenue_control = UserObj.has_group('izi_res_permissions.group_revenue_control')
            group_leader_shop = UserObj.has_group('izi_res_permissions.group_leader_shop')
            group_cashier = UserObj.has_group('izi_res_permissions.group_cashier')

            if group_business_manager or group_revenue_accountant or group_cost_accountant or group_revenue_control or group_leader_shop or group_cashier:
                if self.crm_team_ids:
                    for team in self.crm_team_ids:
                        for use in team.x_member_ids:
                            employee = self.env['hr.employee'].search([('user_id', '=', use.id)])
                            if employee: employee_ids.append(employee.id)
                return {
                    'value': {
                        'employee_ids': employee_ids
                    }
                }
            if group_consultant or group_therapist:
                employee = EmployeeObj.search(['|', ('user_id', '=', self._uid), ('x_user_ids', 'in', [self._uid])])
                if not employee: raise except_orm('Thông báo', 'Tài khoản của bạn chưa liên kết với nhân viên nào, liên hệ quản trị viên để được giải quyết!')
                if len(employee) > 1: raise except_orm('Thông báo', 'Có nhiều hơn một nhân viên đang liên kết với tài khoản của bạn: %s' % (str(employee.ids)))
                return {
                    'value': {
                        'employee_ids': employee and [employee.id] or []
                    }
                }

    @api.onchange('crm_team_ids')
    def _onchange_crm_team_ids(self):
        UserObj = self.env['res.users']
        TeamObj = self.env['crm.team']
        EmployeeObj = self.env['hr.employee']

        group_consultant = UserObj.has_group('izi_res_permissions.group_consultant')
        group_therapist = UserObj.has_group('izi_res_permissions.group_therapist')
        group_business_manager = UserObj.has_group('izi_res_permissions.group_business_manager')
        group_revenue_accountant = UserObj.has_group('izi_res_permissions.group_revenue_accountant')
        group_cost_accountant = UserObj.has_group('izi_res_permissions.group_cost_accountant')
        group_revenue_control = UserObj.has_group('izi_res_permissions.group_revenue_control')
        group_leader_shop = UserObj.has_group('izi_res_permissions.group_leader_shop')
        group_cashier = UserObj.has_group('izi_res_permissions.group_cashier')

        user = UserObj.search([('id', '=', self._uid)], limit=1)

        if not user.branch_ids: raise except_orm('Thông báo', 'Người dùng %s chưa chọn chi nhánh cho phép. Vui lòng liên hệ quản trị để được giải quyết' % (
                                                               str(user.name)))
        for branch in user.branch_ids:
            if not branch: raise except_orm('Thông báo', 'Chi nhánh %s chưa chọn thương hiệu. Vui lòng liên hệ quản trị để được giải quyết' % (
                                                                    str(branch.name)))
        branch_ids = [user.branch_id and user.branch_id.id or 0]
        for branch in user.branch_ids:
            branch_ids.append(branch.id)
        team_ids = TeamObj.get_team_ids_by_branches(branch_ids)

        if group_business_manager or group_revenue_accountant or group_cost_accountant or group_revenue_control or group_leader_shop or group_cashier:
            return {
                'domain': {
                    'crm_team_ids': [('id', 'in', team_ids)],
                    'employee_ids': ['|', ('department_id.x_branch_id', 'in', user.branch_ids.ids), ('job_id.x_code', '=', 'BS')]
                }
            }
        if group_consultant or group_therapist:
            employee = EmployeeObj.search(['|', ('user_id', '=', self._uid), ('x_user_ids', 'in', [self._uid])])
            if not employee: raise except_orm('Thông báo', 'Tài khoản của bạn chưa liên kết với nhân viên nào, liên hệ quản trị viên để được giải quyết!')
            if len(employee) > 1: raise except_orm('Thông báo', 'Có nhiều hơn một nhân viên đang liên kết với tài khoản của bạn: %s' % (str(employee.ids)))

            return {
                'domain': {
                    'crm_team_ids': [('id', 'in', team_ids)],
                    'employee_ids': [('id', '=', employee.id)]
                }
            }
        return {
            'domain': {
                'crm_team_ids': [('id', 'in', team_ids)],
                'employee_ids': ['|', ('department_id.x_branch_id', 'in', user.branch_ids.ids), ('job_id.x_code', '=', 'BS')]
            }
        }

    @api.multi
    def create_report(self):
        param_obj = self.env['ir.config_parameter']
        UserObj = self.env['res.users']
        EmployeeObj = self.env['hr.employee']
        url = param_obj.get_param('birt_url')
        group_consultant = UserObj.has_group('izi_res_permissions.group_consultant')
        group_therapist = UserObj.has_group('izi_res_permissions.group_therapist')

        group_business_manager = UserObj.has_group('izi_res_permissions.group_business_manager')
        group_revenue_accountant = UserObj.has_group('izi_res_permissions.group_revenue_accountant')
        group_cost_accountant = UserObj.has_group('izi_res_permissions.group_cost_accountant')
        group_revenue_control = UserObj.has_group('izi_res_permissions.group_revenue_control')
        group_leader_shop = UserObj.has_group('izi_res_permissions.group_leader_shop')
        group_cashier = UserObj.has_group('izi_res_permissions.group_cashier')
        if not url:
            raise ValidationError(_(u"Bạn phải cấu hình birt_url"))
        report_name = "rpt_revenue_emplooyee.rptdesign"
        param_str1 = "&from_date=" + self.from_date + "&to_date=" + self.to_date
        param_str4 = "&employee_id="
        employee_id = '0'
        if group_business_manager or group_revenue_accountant or group_cost_accountant or group_revenue_control or group_leader_shop or group_cashier:
            list_emp = ''
            if self.crm_team_ids:
                for team in self.crm_team_ids:
                    for user in team.x_member_ids:
                        employee_ids = EmployeeObj.search(['|', ('user_id', '=', user.id), ('x_user_ids', 'in', [user.id])])
                        for emp in employee_ids:
                            list_emp += ',' + str(emp.id)
                employee_id = (list_emp[1:])
            if self.employee_ids:
                employee = ''
                for emp in self.employee_ids:
                    employee += ',' + str(emp.id)
                employee_id = (employee[1:])
        elif group_consultant or group_therapist:
            employee = EmployeeObj.search(['|', ('user_id', '=', self._uid), ('x_user_ids', 'in', [self._uid])])
            if not employee: raise except_orm('Thông báo', 'Tài khoản của bạn chưa liên kết với nhân viên nào, liên hệ quản trị viên để được giải quyết!')
            if len(employee) > 1: raise except_orm('Thông báo', 'Có nhiều hơn một nhân viên đang liên kết với tài khoản của bạn: %s' % (str(employee.ids)))
            employee_id += ',' + str(employee.id)
        else:
            raise except_orm('Thông báo', 'Tài khoản của bạn không có quyền xem báo cáo này')

        param_str = param_str1 + param_str4 + employee_id
        return {
            'type': 'ir.actions.act_url',
            'url': url + "/report/frameset?__report=report_amia/" + report_name + param_str,
            'target': 'new',
        }

    @api.multi
    def create_report_excel(self):
        param_obj = self.env['ir.config_parameter']
        UserObj = self.env['res.users']
        EmployeeObj = self.env['hr.employee']
        url = param_obj.get_param('birt_url')
        group_consultant = UserObj.has_group('izi_res_permissions.group_consultant')
        group_therapist = UserObj.has_group('izi_res_permissions.group_therapist')

        group_business_manager = UserObj.has_group('izi_res_permissions.group_business_manager')
        group_revenue_accountant = UserObj.has_group('izi_res_permissions.group_revenue_accountant')
        group_cost_accountant = UserObj.has_group('izi_res_permissions.group_cost_accountant')
        group_revenue_control = UserObj.has_group('izi_res_permissions.group_revenue_control')
        group_leader_shop = UserObj.has_group('izi_res_permissions.group_leader_shop')
        group_cashier = UserObj.has_group('izi_res_permissions.group_cashier')
        if not url:
            raise ValidationError(_(u"Bạn phải cấu hình birt_url"))
        report_name = "rpt_revenue_emplooyee.rptdesign"
        param_str1 = "&from_date=" + self.from_date + "&to_date=" + self.to_date
        param_str4 = "&employee_id="
        employee_id = '0'

        if group_business_manager or group_revenue_accountant or group_cost_accountant or group_revenue_control or group_leader_shop or group_cashier:
            list_emp = ''
            if self.crm_team_ids:
                for team in self.crm_team_ids:
                    for user in team.x_member_ids:
                        employee_ids = self.env['hr.employee'].search(
                            ['|', ('user_id', '=', user.id), ('x_user_ids', 'in', [user.id])])
                        for emp in employee_ids:
                            list_emp += ',' + str(emp.id)
                employee_id = (list_emp[1:])
            if self.employee_ids:
                employee = ''
                for emp in self.employee_ids:
                    employee += ',' + str(emp.id)
                employee_id = (employee[1:])
        elif group_consultant or group_therapist:
            employee = EmployeeObj.search(['|', ('user_id', '=', self._uid), ('x_user_ids', 'in', [self._uid])])
            if not employee: raise except_orm('Thông báo', 'Tài khoản của bạn chưa liên kết với nhân viên nào, liên hệ quản trị viên để được giải quyết!')
            if len(employee) > 1: raise except_orm('Thông báo', 'Có nhiều hơn một nhân viên đang liên kết với tài khoản của bạn: %s' % (str(employee.ids)))

            employee_id += ',' + str(employee.id)
        else:
            raise except_orm('Thông báo', 'Tài khoản của bạn không có quyền xem báo cáo này')

        param_str = param_str1 + param_str4 + employee_id
        return {
            'type': 'ir.actions.act_url',
            'url': url + "/report/frameset?__report=report_amia/" + report_name + param_str + '&__format=xlsx',
            'target': 'self',
        }
