# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from datetime import datetime
from odoo.exceptions import ValidationError


class RptUseService(models.TransientModel):
    _name = 'rpt.use.service'

    from_date = fields.Date(string="From Date")
    to_date = fields.Date(string="To Date")
    config_ids = fields.Many2many('pos.config', string="Pos Config")
    service_ids = fields.Many2many('product.product', string="Service")
    select_all_config = fields.Boolean("Select All Config")
    select_all_service = fields.Boolean("Select All Service")

    @api.onchange('select_all_config')
    def _onchange_select_all_config(self):
        user = self.env['res.users'].search([('id', '=', self._uid)], limit=1)
        if self.select_all_config:
            self.config_ids = self.env['pos.config'].search([('pos_branch_id', 'in', user.branch_ids.ids)])
        else:
            self.config_ids = False

    @api.onchange('config_ids')
    def _onchange_config_ids(self):
        user = self.env['res.users'].search([('id', '=', self._uid)], limit=1)
        pos_categ_ids = []
        if self.config_ids:
            for config in self.config_ids:
                for pos_category in config.x_category_ids:
                    pos_categ_ids.append(pos_category.id)
        # return {
        #     'domain': {
        #         'service_ids': [('type', '=', 'service'), ('x_type_card', '=', 'none'), ('available_in_pos', '=', True)
        #                                                               , ('pos_categ_id', 'in', pos_categ_ids)]
        #     }
        # }
        return {
            'domain': {
                'config_ids': [('pos_branch_id', 'in', user.branch_ids.ids)],
                'service_ids': [('type', '=', 'service'), ('x_type_card', '=', 'none'), ('available_in_pos', '=', True)
                                                                      , ('pos_categ_id', 'in', pos_categ_ids)]
            }
        }

    @api.onchange('select_all_service')
    def _onchange_select_all_service(self):
        if self.select_all_service and self.config_ids:
            pos_categ_ids = []
            for config in self.config_ids:
                for pos_category in config.x_category_ids:
                    pos_categ_ids.append(pos_category.id)
            print("len(pos_categ_ids): %s" % (str(len(pos_categ_ids))))
            self.service_ids = self.env['product.product'].search([('type', '=', 'service')
                                                                      , ('x_type_card', '=', 'none')
                                                                      , ('available_in_pos', '=', True)
                                                                      , ('pos_categ_id', 'in', pos_categ_ids)])
        else:
            self.service_ids = False

    @api.multi
    def create_report(self):
        param_obj = self.env['ir.config_parameter']
        url = param_obj.get_param('birt_url')
        if not url:
            raise ValidationError(_(u"Bạn phải cấu hình birt_url"))
        report_name = "use_service.rptdesign"
        param_str1 = "&from_date=" + self.from_date + "&to_date=" + self.to_date
        # param_str2 = "&config_id1=" + str(self.config_id.id)
        param_str2 = "&config_id1="
        list_id = ''
        for loc_id in self.config_ids:
            list_id += ',' + str(loc_id.id)
        param_str2 += (list_id[1:])
        param_str3 = "&service_id="
        list_id = ''
        for loc_id in self.service_ids:
            list_id += ',' + str(loc_id.id)
        param_str3 += (list_id[1:])
        param_str = param_str1 + param_str2 + param_str3
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
        report_name = "use_service.rptdesign"
        param_str1 = "&from_date=" + self.from_date + "&to_date=" + self.to_date
        # param_str2 = "&config_id1=" + str(self.config_id.id)
        param_str2 = "&config_id1="
        list_id = ''
        for loc_id in self.config_ids:
            list_id += ',' + str(loc_id.id)
        param_str2 += (list_id[1:])
        param_str3 = "&service_id="
        list_id = ''
        for loc_id in self.service_ids:
            list_id += ',' + str(loc_id.id)
        param_str3 += (list_id[1:])
        param_str = param_str1 + param_str2 + param_str3
        # param_str = "&from_date=" + self.from_date + "&to_date=" + self.to_date + "&config_id=" + self.config_id.id +'&__format=xlsx'
        # param_str = '&__format=xlsx'
        return {
            'type': 'ir.actions.act_url',
            'url': url + "/report/frameset?__report=report_amia/" + report_name + param_str + '&__format=xlsx',
            'target': 'self',
        }
