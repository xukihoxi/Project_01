# -*- coding: utf-8 -*-

from odoo import models, fields, api,_
from datetime import datetime
from odoo.exceptions import ValidationError


class RptPosMoneySession(models.TransientModel):
    _name = 'rpt.pos.money.sesion'

    session_id = fields.Many2many('pos.session', string="Pos Session")
    select_all = fields.Boolean('All Session')

    @api.onchange('select_all')
    def _onchange_select_all(self):
        user = self.env['res.users'].search([('id', '=', self._uid)], limit=1)
        if self.select_all:
            self.session_id = self.env['pos.session'].search([('branch_id', 'in', user.branch_ids.ids)])
        else:
            self.session_id = False

    @api.onchange('session_id')
    def onchange_session_id(self):
        user = self.env['res.users'].search([('id', '=', self._uid)], limit=1)
        session_ids = []
        sessions = self.env['pos.session'].search([('branch_id', 'in', user.branch_ids.ids)])
        for session in sessions:
            session_ids.append(session.id)
        return {
            'domain': {
                'session_id': [('id', 'in', session_ids)]
            }
        }

    @api.multi
    def create_report(self):
        param_obj = self.env['ir.config_parameter']
        url = param_obj.get_param('birt_url')
        if not url:
            raise ValidationError(_(u"Bạn phải cấu hình birt_url"))
        report_name = "rpt_pos_money_session.rptdesign"
        param_str = "&session_id="
        list_id = ''
        for loc_id in self.session_id:
            list_id += ',' + str(loc_id.id)
        param_str += (list_id[1:])
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
        report_name = "rpt_pos_money_session.rptdesign"
        param_str = "&session_id="
        list_id = ''
        for loc_id in self.session_id:
            list_id += ',' + str(loc_id.id)
        param_str += (list_id[1:])
        return {
            'type': 'ir.actions.act_url',
            'url': url + "/report/frameset?__report=report_amia/" + report_name + param_str + '&__format=xlsx',
            'target': 'self',
        }