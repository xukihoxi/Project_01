# -*- coding: utf-8 -*-

from odoo import models, fields, api,_
from datetime import datetime
from odoo.exceptions import ValidationError


class RptDinhLuongMaterail(models.TransientModel):
    _name = 'rpt.material'

    from_date = fields.Date(string="From Date")
    to_date = fields.Date(string="To Date")
    config_id = fields.Many2one('pos.config', "Pos Config")

    @api.multi
    def create_report(self):
        param_obj = self.env['ir.config_parameter']
        url = param_obj.get_param('birt_url')
        if not url:
            raise ValidationError(_(u"Bạn phải cấu hình birt_url"))
        report_name = "rpt_dinh_luong_nguyen_vat_lieu.rptdesign"
        str_from_date = datetime.strptime(self.from_date, "%Y-%m-%d").strftime("%d/%m/%Y")
        str_to_date = datetime.strptime(self.to_date, "%Y-%m-%d").strftime("%d/%m/%Y")
        param_str1 = "&from_date=" + self.from_date + "&to_date=" + self.to_date
        param_str2 = "&config_id=" + str(self.config_id.id)
        param_str = param_str1 + param_str2
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
        report_name = "rpt_dinh_luong_nguyen_vat_lieu.rptdesign"
        str_from_date = datetime.strptime(self.from_date, "%Y-%m-%d").strftime("%d/%m/%Y")
        str_to_date = datetime.strptime(self.to_date, "%Y-%m-%d").strftime("%d/%m/%Y")
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