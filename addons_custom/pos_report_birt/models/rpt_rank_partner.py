# -*- coding: utf-8 -*-

from odoo import models, fields, api,_
from datetime import datetime
from odoo.exceptions import ValidationError


class RptRankPartner(models.TransientModel):
    _name = 'rpt.rank.partner'

    rank_id = fields.Many2many('crm.vip.rank', string="Rank")
    # config_id = fields.Many2one('pos.config', "Pos Config")
    select_all = fields.Boolean('All Session')

    # @api.onchange('config_id')
    # def onchange_pos_session(self):
    #     ids = []
    #     ids_o2m = self.env['pos.session'].search([])
    #     for id in ids_o2m:
    #         if id.id == 1 or id.id == 2 or id.id == 3:
    #             continue
    #         ids.append(id.id)
    #     return {
    #         'domain': {
    #             'session_id': [('id', 'in', ids)]
    #         }
    #     }

    @api.multi
    def create_report(self):
        param_obj = self.env['ir.config_parameter']
        url = param_obj.get_param('birt_url')
        if not url:
            raise ValidationError(_(u"Bạn phải cấu hình birt_url"))
        report_name = "rank_partner.rptdesign"
        param_str = "&rank_id="
        if (self.select_all == True):
            list_id = ''
            rank = self.env['crm.vip.rank'].search([])
            for rank_id in rank:
                list_id += ',' + str(rank_id.id)
            param_str += (list_id[1:])
        else:
            list_id = ''
            for loc_id in self.rank_id:
                list_id += ',' + str(loc_id.id)
            param_str += (list_id[1:])
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
        report_name = "rank_partner.rptdesign"
        param_str = "&rank_id="
        if (self.select_all == True):
            list_id = ''
            rank = self.env['crm.vip.rank'].search([])
            for rank_id in rank:
                list_id += ',' + str(rank_id.id)
            param_str += (list_id[1:])
        else:
            list_id = ''
            for loc_id in self.rank_id:
                list_id += ',' + str(loc_id.id)
            param_str += (list_id[1:])
        return {
            'type': 'ir.actions.act_url',
            'url': url + "/report/frameset?__report=report_amia/" + report_name + param_str + '&__format=xlsx',
            'target': 'self',
        }