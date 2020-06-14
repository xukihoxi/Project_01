# -*- coding: utf-8 -*-

from odoo import models, fields, api,_
from datetime import datetime
from odoo.exceptions import ValidationError, except_orm


class RptCongNoKH(models.TransientModel):
    _name = 'rpt.cong.no.kh'

    def _domain_team_id(self):
        UserObj = self.env['res.users']

        user = UserObj.search([('id', '=', self.env.uid)])
        return [('x_branch_id', 'in', user.branch_ids.ids)]

    crm_team_id = fields.Many2one('crm.team', string="CRM",domain=_domain_team_id)
    partner_id = fields.Many2many('res.partner', string='Partner')
    # config_id = fields.Many2one('pos.config', "Pos Config")
    select_all_partner = fields.Boolean('All Partner')

    @api.onchange('select_all_partner')
    def _onchange_select_all_partner(self):
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
        if self.select_all_partner:
            self.partner_id = self.env['res.partner'].search([('x_crm_team_id', 'in', team_ids)])
        else:
            self.partner_id = False

    @api.multi
    def create_report(self):
        param_obj = self.env['ir.config_parameter']
        url = param_obj.get_param('birt_url')
        if not url:
            raise ValidationError(_(u"Bạn phải cấu hình birt_url"))
        report_name = "rpt_cong_no_KH.rptdesign"
        param_str = "&crm_team_id=" + str(self.crm_team_id.id)
        param_str1 = "&partner_id="
        # if (self.select_all_partner == True):
        #     # list_id = ''
        #     # rank = self.env['crm.vip.rank'].search([])
        #     # for rank_id in rank:
        #     #     list_id += ',' + str(rank_id.id)
        #     # param_str += (list_id[1:])
        #     param_str1 += str(0)
        # else:
        list_id = ''
        for loc_id in self.partner_id:
            list_id += ',' + str(loc_id.id)
            param_str1 += (list_id[1:])
        return {
            'type': 'ir.actions.act_url',
            'url': url + "/report/frameset?__report=report_amia/" + report_name + param_str + param_str1,
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
        report_name = "rpt_cong_no_KH.rptdesign"
        param_str = "&crm_team_id=" + str(self.crm_team_id.id)
        param_str1 = "&partner_id="
        # if (self.select_all_partner == True):
        #     # list_id = ''
        #     # rank = self.env['crm.vip.rank'].search([])
        #     # for rank_id in rank:
        #     #     list_id += ',' + str(rank_id.id)
        #     # param_str += (list_id[1:])
        #     param_str1 += str(0)
        # else:
        list_id = ''
        for loc_id in self.partner_id:
            list_id += ',' + str(loc_id.id)
            param_str1 += (list_id[1:])
        return {
            'type': 'ir.actions.act_url',
            'url': url + "/report/frameset?__report=report_amia/" + report_name + param_str + param_str1 + '&__format=xlsx',
            'target': 'self',
        }