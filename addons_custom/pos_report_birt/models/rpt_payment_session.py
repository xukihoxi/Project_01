# -*- coding: utf-8 -*-

from odoo import models, fields, api,_
from datetime import datetime
from odoo.exceptions import ValidationError


class RptByPaymentSession(models.TransientModel):
    _name = 'rpt.by.payment.session'

    session_id = fields.Many2one('pos.session', "Pos Session")
    config_id = fields.Many2one('pos.config', "Pos Config")

    @api.onchange('config_id')
    def _onchange_config_id(self):
        user = self.env['res.users'].search([('id', '=', self._uid)], limit=1)
        session_ids = []
        if self.config_id:
            sessions = self.env['pos.session'].search([('config_id', '=', self.config_id.id)])
            for session in sessions:
                session_ids.append(session.id)
        return {
            'domain': {
                'config_id': [('pos_branch_id', 'in', user.branch_ids.ids)],
                'session_id': [('id', 'in', session_ids)]
            }
        }

    @api.multi
    def create_report(self):
        param_obj = self.env['ir.config_parameter']
        url = param_obj.get_param('birt_url')
        if not url:
            raise ValidationError(_(u"Bạn phải cấu hình birt_url"))
        report_name = "report_by_payment_session.rptdesign"
        param_str1 = "&sesstion_id=" + str(self.session_id.id)
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
        report_name = "report_by_payment_session.rptdesign"
        param_str1 = "&sesstion_id=" + str(self.session_id.id)
        param_str2 = "&config_id=" + str(self.config_id.id)
        param_str = param_str1 + param_str2
        # param_str = "&from_date=" + self.from_date + "&to_date=" + self.to_date + "&config_id=" + self.config_id.id +'&__format=xlsx'
        # param_str = '&__format=xlsx'
        return {
            'type': 'ir.actions.act_url',
            'url': url + "/report/frameset?__report=report_amia/" + report_name + param_str + '&__format=xlsx',
            'target': 'self',
        }