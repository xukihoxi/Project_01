# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import except_orm, ValidationError, UserError

class InheritCashManagement(models.Model):
    _inherit = 'account.cash'

    x_user_id = fields.Many2many('hr.employee', string='Beneficiary')
    revenue_id = fields.Many2one('pos.revenue.allocation', string='Allocation revenue')

    @api.multi
    def action_carrying(self):
        res = super(InheritCashManagement, self).action_carrying()
        if self.x_user_id:
            if self.type == 'in':
                revenue_id =  self._auto_allocation(self.amount_total)
            else:
                revenue_id = self._auto_allocation(-self.amount_total)
            self.revenue_id = revenue_id.id
        return res

    def _auto_allocation(self, amount):
        partner_id = False
        for line in self.lines:
            partner_id = line.partner_id
            break
        if amount != 0:
            Allocation = self.env['pos.revenue.allocation']
            AllocationLine = self.env['pos.revenue.allocation.line']
            vals = {
                'cash_management_id': self.id,
                # 'partner_name':self.partner_id.name,
                'partner_id': partner_id.id,
                'partner_code': self.partner_id.x_code,
                'amount_total': amount,
                'amount_allocated': amount,
                'amount_res': 0,
                'date': fields.Datetime.now(),
                'style_allocation': 'percent',
                'state': 'close',
                'pos_session_id': self.session_id.id,
            }
            revenue_id = Allocation.create(vals)
            count_nvtv = 0
            for item in self.x_user_id:
                if item.job_id.x_code == 'NVTV':
                    count_nvtv += 1
            count = len(self.x_user_id)
            if count == count_nvtv or count_nvtv == 0:
                if count_nvtv == 0:
                    note = 'Nhân viên thừa hưởng'
                else:
                    note = 'Nhân viên tư vấn'
                for item in self.x_user_id:
                    vals_line = {
                        'employee_id': item.id,
                        'amount': amount / count,
                        'amount_total': amount / count,
                        'percent': 100 / count,
                        'cash_management_id': self.id,
                        'note': note,
                        'revenue_allocation_id': revenue_id.id,
                    }
                    AllocationLine.create(vals_line)
            else:
                for item in self.x_user_id:
                    if item.job_id.x_code == 'NVTV':
                        vals_line = {
                            'employee_id': item.id,
                            'amount': amount / (2 * count_nvtv),
                            'amount_total': amount / (2 * count_nvtv),
                            'percent': 50 / count_nvtv,
                            'cash_management_id': self.id,
                            'note': 'Nhân viên tư vấn',
                            'revenue_allocation_id': revenue_id.id,
                        }
                        AllocationLine.create(vals_line)
                    else:
                        vals_line = {
                            'employee_id': item.id,
                            'amount': amount / (2 * (count - count_nvtv)),
                            'amount_total': amount / (2 * (count - count_nvtv)),
                            'percent': 50 / (count - count_nvtv),
                            'cash_management_id': self.id,
                            'note': 'Nhân viên thừa hưởng',
                            'revenue_allocation_id': revenue_id.id,
                        }
                        AllocationLine.create(vals_line)
        return revenue_id