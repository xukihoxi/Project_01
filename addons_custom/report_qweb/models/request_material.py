# -*- coding: utf-8 -*-

from odoo import models, fields, api

class RequestMaterialQweb(models.Model):
    _inherit = 'izi.service.card.using'

    @api.multi
    def action_print(self):
        return {
            'type': 'ir.actions.act_url',
            'url': 'report/pdf/report_qweb.report_template_request_material_view/%s' %(self.id),
            'target': 'new',
            'res_id': self.id,
        }

    def _name_qweb(self):
        user_id = self.env['res.users'].search([('id', '=', self.env.uid)], limit=1)
        return user_id.name

    def _get_name_employee(self,line_id):
        line = self.env['izi.service.card.using.line'].search([('id','=',line_id)])
        name = ''
        for emp in line.employee_ids:
            name = name + ',' + emp.name
        return name[1:]

