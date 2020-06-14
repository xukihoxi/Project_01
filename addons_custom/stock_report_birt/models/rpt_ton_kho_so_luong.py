# -*- coding: utf-8 -*-

from odoo import fields, models, api
from datetime import datetime
from odoo.exceptions import ValidationError

class ReportInventoryValue(models.TransientModel):
    _name = "report.stock.inventory.quant"

    # @api.multi
    # def _get_login_id(self):
    #     if self._uid != 1:
    #         return True
    #
    # # @api.multi
    # # def _get_location(self):
    # #     print self._uid
    # #     if self._uid != 1:
    # #         user_obj = self.env['res.users'].search([('id', '=', self._uid)])
    # #         if user_obj.pos_config:
    # #             if user_obj.pos_config.stock_location_id:
    # #                 print user_obj.pos_config.stock_location_id.id
    # #                 return [user_obj.pos_config.stock_location_id.id, ]
    #
    # inv = fields.Boolean('Invisible state')
    location_id = fields.Many2many('stock.location', string='Loaction')
    select_all = fields.Boolean('All Location')

    # _defaults = {
    #     'inv': _get_login_id,
    #     #'location_id': _get_location
    # }

    # @api.onchange('location_id')
    # def onchange_location(self):
    #     if self._uid != 1:
    #         list = []
    #         user_obj = self.env['res.users'].search([('id', '=', self._uid)])
    #         locations = self.env['stock.location'].search(
    #             [('branch_id', '=', user_obj.branch_id.id), ('usage', '=', 'internal')])
    #         for location_id in locations:
    #             list.append(location_id.id)
    #         return {
    #             'domain': {'location_id': [('id', 'in', list)]}
    #         }

    # @api.onchange('location_id')
    # def _onchange_wh(self):
    #     list = []
    #     if self.warehouse_id:
    #         locations = self.env['stock.location'].search(
    #             [('location_id', '=', self.warehouse_id.view_location_id.id), ('usage', '=', 'internal')])
    #         for location_id in locations:
    #             list.append(location_id.id)
    #     return {
    #         'domain': {'location_id': [('id', 'in', list)]}
    #     }

    @api.multi
    def create_report(self):
        param_obj = self.env['ir.config_parameter']
        url = param_obj.get_param('birt_url')
        if not url:
            raise ValidationError("You must config birt_url")
        report_name = "rpt_ton_kho.rptdesign"
        param_str = "&location_id="
        if (self.select_all == True):
            param_str += '0'
        else:
            list_id = ''
            for loc_id in self.location_id:
                list_id += ',' + str(loc_id.id)
            param_str += (list_id[1:])

        return {
            'type': 'ir.actions.act_url',
            'url': url + "/report/frameset?__report=report_amia/" + report_name + param_str,
            'target': 'new',
        }

    @api.multi
    def create_report_ex(self):
        param_obj = self.env['ir.config_parameter']
        url = param_obj.get_param('birt_url')
        if not url:
            raise ValidationError("You must config birt_url")
        report_name = "rpt_ton_kho.rptdesign"
        param_str = "&location_id="
        if (self.select_all == True):
            param_str += '0'
        else:
            list_id = ''
            for loc_id in self.location_id:
                list_id += ',' + str(loc_id.id)
            param_str += (list_id[1:])

        return {
            'type': 'ir.actions.act_url',
            'url': url + "/report/frameset?__report=report_amia/" + report_name + param_str+'&__format=xlsx',
            'target': 'self',
        }


