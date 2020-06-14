# -*- coding: utf-8 -*-

from odoo import models, fields, api,_
from datetime import datetime
from odoo.exceptions import ValidationError


class RptByPayment(models.TransientModel):
    _name = 'rpt.by.payment'

    from_date = fields.Date(string="From Date")
    to_date = fields.Date(string="To Date")
    config_id = fields.Many2one('pos.config', "Pos Config")
    url_report = fields.Text(string="Url report")

    @api.onchange('config_id')
    def _onchange_config_id(self):
        user = self.env['res.users'].search([('id', '=', self._uid)], limit=1)
        return {
            'domain': {
                'config_id': [('pos_branch_id', 'in', user.branch_ids.ids)]
            }
        }

    @api.multi
    def create_report(self):
        param_obj = self.env['ir.config_parameter']
        url = param_obj.get_param('birt_url')
        if not url:
            raise ValidationError(_(u"Bạn phải cấu hình birt_url"))
        report_name = "report_by_payment.rptdesign"
        param_str1 = "&from_date=" + self.from_date + "&to_date=" + self.to_date
        param_str2 = "&config_id=" + str(self.config_id.id)
        param_str = param_str1 + param_str2

        self.url_report = url + "/report/frameset?__report=report_amia/" + report_name + param_str
        # return {
        #     'type': 'ir.actions.act_url',
        #     'url': url + "/report/frameset?__report=report_amia/" + report_name + param_str,
        #     'target': 'new',
        # }
        # param_str = {
        #     'from_date': self.from_date,
        #     'to_date': self.to_date,
        #     'config_id': str(self.config_id.id)
        # }
        #
        # return {
        #     "type": "ir.actions.client",
        #     'name': 'Báo cáo',
        #     'tag': 'BirtViewerAction',
        #     'target': 'current',
        #     'context': {
        #         'birt_link': url + "/report/frameset?__report=report_amia/" + report_name,
        #         'payload_data': param_str
        #     }
        # }

    @api.multi
    def create_report_excel(self):
        param_obj = self.env['ir.config_parameter']
        url = param_obj.get_param('birt_url')
        if not url:
            raise ValidationError(_(u"Bạn phải cấu hình birt_url"))
        report_name = "report_by_payment.rptdesign"
        param_str1 = "&from_date=" + self.from_date + "&to_date=" + self.to_date
        param_str2 = "&config_id=" + str(self.config_id.id)
        param_str = param_str1 + param_str2
        # param_str = "&from_date=" + self.from_date + "&to_date=" + self.to_date + "&config_id=" + self.config_id.id +'&__format=xlsx'
        # param_str = '&__format=xlsx'
        return {
            'type': 'ir.actions.act_url',
            'url': url + "/report/frameset?__report=report_amia/" + report_name + param_str + '&__format=xlsx',
            'target': 'self',
        }