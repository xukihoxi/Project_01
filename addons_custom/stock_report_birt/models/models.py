# -*- coding: utf-8 -*-

from odoo import fields, models, api, _
from datetime import datetime
from odoo.exceptions import ValidationError



class Reportimportandexportinventory(models.TransientModel):
    _name = "report.import.and.export.inventory"

    from_date = fields.Date(string="From Date")
    to_date = fields.Date(string="To Date")
    rpt_location_id = fields.Many2one('stock.location', string='Location')

    @api.onchange('rpt_location_id')
    def onchange_location(self):
        if self._uid != 1:
            list = []
            user_obj = self.env['res.users'].search([('id', '=', self._uid)])
            locations = self.env['stock.location'].search(
                [('branch_id', 'in', user_obj.branch_ids.ids), ('usage', '=', 'internal')])
            for location_id in locations:
                list.append(location_id.id)
            return {
                'domain': {'rpt_location_id': [('id', 'in', list)]}
            }

    @api.multi
    def create_report_import_and_export_inventory(self):
        param_obj = self.env['ir.config_parameter']
        url = param_obj.get_param('birt_url')
        if not url:
            raise ValidationError(_(u"Bạn phải cấu hình birt_url"))
        report_name = "bao_cao_xuat_nhap_ton.rptdesign"
        from_date = datetime.strptime(self.from_date, "%Y-%m-%d")
        to_date = datetime.strptime(self.to_date, "%Y-%m-%d")
        location_id = self.rpt_location_id

        param_str = "&from_date=" + str(from_date) + "&to_date=" + str(to_date) + "&location_id=" + str(location_id.id)
        return {
            'type': 'ir.actions.act_url',
            'url': url + "/report/frameset?__report=report_amia/" + report_name + param_str,
            'target': 'new',
        }

    @api.multi
    def create_report_import_and_export_inventory_ex(self):
        param_obj = self.env['ir.config_parameter']
        url = param_obj.get_param('birt_url')
        if not url:
            raise ValidationError(_(u"Bạn phải cấu hình birt_url"))
        report_name = "bao_cao_xuat_nhap_ton.rptdesign"
        from_date = datetime.strptime(self.from_date, "%Y-%m-%d")
        to_date = datetime.strptime(self.to_date, "%Y-%m-%d")
        location_id = self.rpt_location_id

        param_str = "&from_date=" + str(from_date) + "&to_date=" + str(to_date) + "&location_id=" + str(location_id.id)
        return {
            'type': 'ir.actions.act_url',
            'url': url + "/report/frameset?__report=report_amia/" + report_name + param_str + '&__format=xlsx',
            'target': 'self',
        }
