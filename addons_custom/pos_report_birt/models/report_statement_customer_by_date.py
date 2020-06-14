# -*- coding: utf-8 -*-

from odoo import models, fields, api,_
from datetime import datetime
from odoo.exceptions import ValidationError, except_orm


class ReportStatementCustomerByDate(models.TransientModel):
    _name = 'report.statement.customer.date'

    date = fields.Date(string="Date")
    partner_id = fields.Many2one('res.partner', string="Partner")

    @api.multi
    def create_report(self):
        param_obj = self.env['ir.config_parameter']
        url = param_obj.get_param('birt_url')
        if not url:
            raise ValidationError(_(u"Bạn phải cấu hình birt_url"))
        report_name = "statement_customer_by_date.rptdesign"
        param_str1 = "&date=" + self.date
        param_str2 = "&partner_id=" + str(self.partner_id.id)
        param_str3 = "&partner_code=" + str(self.partner_id.x_old_code)
        param_str4 = "&partner_name=" + str(self.partner_id.name)
        param_str = param_str1 + param_str2 + param_str3 + param_str4
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
        report_name = "statement_customer_by_date.rptdesign"
        param_str1 = "&date=" + self.date
        param_str2 = "&partner_id=" + str(self.partner_id.id)
        param_str3 = "&partner_code=" + str(self.partner_id.x_old_code)
        param_str4 = "&partner_name=" + str(self.partner_id.name)
        param_str = param_str1 + param_str2 + param_str3 + param_str4
        return {
            'type': 'ir.actions.act_url',
            'url': url + "/report/frameset?__report=report_amia/" + report_name + param_str + '&__format=xls',
            'target': 'self',
        }