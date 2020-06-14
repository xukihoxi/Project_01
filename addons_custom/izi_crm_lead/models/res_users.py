# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import except_orm


class ResUsers(models.Model):
    _inherit = 'res.users'

    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=100):
        if 'domain_by_team_id' in self._context:
            ObjTeam = self.env['crm.team']
            ObjJob = self.env['hr.job']
            ObjEmployee = self.env['hr.employee']

            user_ids = []
            team = ObjTeam.search([('id', '=', self._context.get('domain_by_team_id', False))], limit=1)
            # job = ObjJob.search([('x_code', '=', 'NVTV')], limit=1)
            # if not job: raise except_orm('Cảnh báo!', _("Chưa cấu hình chức vụ cho nhân viên tư vấn: NVTV"))
            for user in team.x_member_ids:
                # employee = ObjEmployee.search(['|', ('user_id', '=', user.id), ('x_user_ids', 'in', user.id), ('job_id', '=', job.id)], limit=1)
                employee = ObjEmployee.search(['|', ('user_id', '=', user.id), ('x_user_ids', 'in', user.id)], limit=1)
                if employee:
                    user_ids.append(user.id)
                else:
                    continue
            res = self.search([('id', 'in', user_ids), ('name', 'ilike', name)], limit=limit)
        else:
            res = self.search([('name', 'ilike', name)], limit=limit)
        return res.name_get()

    def name_get(self):
        result = []
        for record in self:
            name = '%s' % (str(record.name))
            result.append((record.id, name))
        return result