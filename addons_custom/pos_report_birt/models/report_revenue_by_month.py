# -*- coding: utf-8 -*-

from odoo import models, fields, api,_
from datetime import datetime
from odoo.exceptions import ValidationError, except_orm


class ReportRevenueByMonth(models.TransientModel):
    _name = 'report.revenue.by.month'

    from_date = fields.Date(string="From Date")
    to_date = fields.Date(string="To Date")
    branch_ids = fields.Many2many('res.branch', string="Branches")
    select_all = fields.Boolean(string="Select all")
    url_report = fields.Text(string="Url report")

    @api.onchange('select_all')
    def _onchange_select_all(self):
        user = self.env['res.users'].search([('id', '=', self._uid)], limit=1)
        if self.select_all:
            self.branch_ids = self.env['res.branch'].search([('id', 'in', user.branch_ids.ids)])
        else:
            self.branch_ids = False

    @api.onchange('branch_ids')
    def _onchange_branch_ids(self):
        user = self.env['res.users'].search([('id', '=', self._uid)], limit=1)
        return {
            'domain': {
                'branch_ids': [('id', 'in', user.branch_ids.ids)]
            }
        }

    @api.multi
    def create_report(self):
        param_obj = self.env['ir.config_parameter']
        url = param_obj.get_param('birt_url')
        if not url:
            raise ValidationError(_(u"Bạn phải cấu hình birt_url"))
        branch_ids = '0'
        branches_name = ''
        if not self.branch_ids: raise except_orm('Thông báo', 'Chưa chọn chi nhánh!')
        for branch in self.branch_ids:
            branch_ids += ',%s' % (str(branch.id), )
            branches_name += '%s,' % (str(branch.name), )
        report_name = "report_revenue_by_month.rptdesign"
        param_str1 = "&from_date=" + self.from_date + "&to_date=" + self.to_date
        param_str2 = "&branch_ids=" + str(branch_ids)
        param_str3 = "&branches_name=" + str(branches_name)
        param_str = param_str1 + param_str2 + param_str3

        self.url_report = url + "/report/frameset?__report=report_amia/" + report_name + param_str
        # return {
        #     'type': 'ir.actions.act_url',
        #     'url': url + "/report/frameset?__report=report_amia/" + report_name + param_str,
        #     'target': 'new',
        # }
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
        branch_ids = '0'
        branches_name = ''
        if not self.branch_ids: raise except_orm('Thông báo', 'Chưa chọn chi nhánh!')
        for branch in self.branch_ids:
            branch_ids += ',%s' % (str(branch.id), )
            branches_name += '%s,' % (str(branch.name), )
        report_name = "report_revenue_by_month.rptdesign"
        param_str1 = "&from_date=" + self.from_date + "&to_date=" + self.to_date
        param_str2 = "&branch_ids=" + str(branch_ids)
        param_str3 = "&branches_name=" + str(branches_name)
        param_str = param_str1 + param_str2 + param_str3
        # param_str = "&from_date=" + self.from_date + "&to_date=" + self.to_date + "&config_id=" + self.config_id.id +'&__format=xlsx'
        # param_str = '&__format=xlsx'
        return {
            'type': 'ir.actions.act_url',
            'url': url + "/report/frameset?__report=report_amia/" + report_name + param_str + '&__format=xls',
            'target': 'self',
        }