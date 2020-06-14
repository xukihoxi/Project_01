# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import except_orm, ValidationError, UserError


class PosOrder(models.Model):
    _inherit = 'pos.order'

    x_user_id = fields.Many2many('hr.employee', string='Beneficiary')
    x_allocation_ids = fields.One2many('pos.revenue.allocation.line', 'order_id', string='Allocation')

    @api.onchange('user_id')
    def _onchange_default_emp(self):
        #mặc định lấy nhân viên hưởng doanh thu là người người hưởng doanh thu dự kiến
        context = self._context
        if self.user_id:
            lead_employee_ids = context.get('lead_employee_ids', False)
            if lead_employee_ids:
                self.x_user_id = lead_employee_ids
            else:
                self.x_user_id = False

    # @api.onchange('partner_id')
    # def onchange_employee(self):
    #     ids = []
    #     branch_ids = self.env['res.branch'].search([('brand_id', '=', self.session_id.branch_id.brand_id.id)])
    #     department_ids = self.env['hr.department'].search(
    #         [('x_branch_id', 'in', branch_ids.ids)])
    #     for line in department_ids:
    #         ids_o2m = self.env['hr.employee'].search([('department_id', '=', line.id)])
    #         for id in ids_o2m:
    #             ids.append(id.id)
    #     return {
    #         'domain': {
    #             'x_user_id': [('id', 'in', ids)]
    #         }
    #     }


    @api.multi
    def action_allocation(self):
        allo = self.env['pos.revenue.allocation'].search([('order_id', '=', self.id)], limit=1)
        if allo.id != False:
            view = self.env.ref('pos_revenue_allocation.revenue_allocation_form_view')
            return {
                'name': _('Phân bổ doanh thu'),
                'type': 'ir.actions.act_window',
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'pos.revenue.allocation',
                'views': [(view.id, 'form')],
                'view_id': view.id,
                'res_id': allo.id,
                'target': 'new',
                'context': self.env.context,
            }
        else:
            if self.x_total_order == 0:
                raise except_orm('Cảnh báo!', (
                    "Số tiền KH thanh toán bằng 0. Không có gì để phân bổ"))
            ctx = self.env.context.copy()
            ctx.update({'default_order_id': self.id})
            view = self.env.ref('pos_revenue_allocation.revenue_allocation_form_view')
            return {
                'name': _('Phân bổ doanh thu'),
                'type': 'ir.actions.act_window',
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'pos.revenue.allocation',
                'views': [(view.id, 'form')],
                'view_id': view.id,
                'target': 'new',
                'context': ctx,
            }

    @api.multi
    def process_customer_signature(self):
        order = super(PosOrder, self).process_customer_signature()
        if self.x_user_id:
            self._auto_allocation()
        return order

    def _auto_allocation(self):
        print("_auto_allocation")
        if self.x_total_order >= 0:
            if not self.x_allocation_ids:
                Allocation = self.env['pos.revenue.allocation']
                AllocationLine = self.env['pos.revenue.allocation.line']
                vals = {
                    'order_id': self.id,
                    'partner_name':self.partner_id.name,
                    'partner_id': self.partner_id.id,
                    'partner_code': self.partner_id.x_code,
                    'amount_total': self.x_total_order,
                    'amount_allocated': self.x_total_order,
                    'amount_res': 0,
                    'date': fields.Datetime.now(),
                    # 'style_allocation': 'percent',
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
                    x_total_order = self.x_total_order
                    for line in self.lines:
                        if line.product_id.type == 'product':
                            amount_product_debit = 0
                            if line.price_subtotal_incl > 0 and x_total_order >= 0:
                                if x_total_order >= line.price_subtotal_incl:
                                   amount_product = line.price_subtotal_incl / count
                                elif x_total_order < line.price_subtotal_incl:
                                    amount_product = x_total_order / count
                                elif x_total_order ==0:
                                    amount_product = 0
                                for item in self.x_user_id:
                                    vals_line = {
                                        'employee_id': item.id,
                                        'amount': amount_product,
                                        'amount_total':amount_product,
                                        'percent': 1,
                                        'order_id': self.id,
                                        'product_id':line.product_id.id,
                                        'note': note,
                                        'revenue_allocation_id': revenue_id.id,
                                        'quantity':line.qty
                                    }
                                    AllocationLine.create(vals_line)
                                    amount_product_debit += amount_product
                            x_total_order -= amount_product_debit

                    for line in self.lines:
                        if line.product_id.type == 'service':
                            amount_product_debit = 0
                            if line.price_subtotal_incl > 0 and x_total_order >= 0:
                                if x_total_order >= line.price_subtotal_incl:
                                   amount_product = line.price_subtotal_incl / count
                                elif x_total_order < line.price_subtotal_incl:
                                    amount_product = x_total_order / count
                                elif x_total_order == 0:
                                    amount_product = 0
                                for item in self.x_user_id:
                                    vals_line = {
                                        'employee_id': item.id,
                                        'amount': amount_product,
                                        'amount_total': amount_product,
                                        'percent': 1,
                                        'order_id': self.id,
                                        'product_id':line.product_id.id,
                                        'note': note,
                                        'revenue_allocation_id': revenue_id.id,
                                        'quantity': line.qty
                                    }
                                    AllocationLine.create(vals_line)
                                    amount_product_debit += amount_product
                            x_total_order -= amount_product_debit

                else:
                    x_total_order = self.x_total_order
                    for line in self.lines:
                        if line.product_id.type == 'product':
                            amount_product_debit = 0
                            for item in self.x_user_id:
                                if item.job_id.x_code =='NVTV':
                                    if line.price_subtotal_incl > 0 and x_total_order >= 0:
                                        if x_total_order >= line.price_subtotal_incl:
                                            amount_product = line.price_subtotal_incl / (2 * count_nvtv)
                                        elif x_total_order < line.price_subtotal_incl:
                                            amount_product = x_total_order / (2 * count_nvtv)
                                        elif x_total_order == 0:
                                            amount_product = 0
                                        vals_line = {
                                            'employee_id': item.id,
                                            'amount': amount_product,
                                            'amount_total': amount_product,
                                            'product_id':line.product_id.id,
                                            'percent': 1,
                                            'order_id': self.id,
                                            'note': 'Nhân viên tư vấn',
                                            'revenue_allocation_id': revenue_id.id,
                                            'quantity': line.qty
                                        }
                                        AllocationLine.create(vals_line)
                                        amount_product_debit +=amount_product
                                else:
                                    if line.price_subtotal_incl > 0 and x_total_order >= 0:
                                        if x_total_order >= line.price_subtotal_incl:
                                            amount_product = line.price_subtotal_incl / (2 * (count - count_nvtv))
                                        elif x_total_order < line.price_subtotal_incl:
                                            amount_product = x_total_order / (2 * (count - count_nvtv))
                                        elif x_total_order == 0:
                                            amount_product = 0
                                        vals_line = {
                                            'employee_id': item.id,
                                            'amount': amount_product,
                                            'amount_total': amount_product,
                                            'product_id':line.product_id.id,
                                            'percent': 1,
                                            'order_id': self.id,
                                            'note': 'Nhân viên thừa hưởng',
                                            'revenue_allocation_id': revenue_id.id,
                                            'quantity': line.qty
                                        }
                                        AllocationLine.create(vals_line)
                                        amount_product_debit +=amount_product
                            x_total_order -= amount_product_debit

                    for line in self.lines:
                        if line.product_id.type == 'service':
                            amount_product_debit = 0
                            for item in self.x_user_id:
                                if item.job_id.x_code == 'NVTV':
                                    if line.price_subtotal_incl > 0 and x_total_order >= 0:
                                        if x_total_order >= line.price_subtotal_incl:
                                            amount_product = line.price_subtotal_incl / (2 * count_nvtv)
                                        elif x_total_order < line.price_subtotal_incl:
                                            amount_product = x_total_order / (2 * count_nvtv)
                                        elif x_total_order == 0:
                                            amount_product = 0
                                        vals_line = {
                                            'employee_id': item.id,
                                            'amount': amount_product,
                                            'amount_total': amount_product,
                                            'product_id': line.product_id.id,
                                            'percent': 1,
                                            'order_id': self.id,
                                            'note': 'Nhân viên tư vấn',
                                            'revenue_allocation_id': revenue_id.id,
                                            'quantity': line.qty
                                        }
                                        AllocationLine.create(vals_line)
                                        amount_product_debit += amount_product
                                else:
                                    if line.price_subtotal_incl > 0 and x_total_order >= 0:
                                        if x_total_order >= line.price_subtotal_incl:
                                            amount_product = line.price_subtotal_incl / (2 * (count - count_nvtv))
                                        elif x_total_order < line.price_subtotal_incl:
                                            amount_product = x_total_order / (2 * (count - count_nvtv))
                                        elif x_total_order == 0:
                                            amount_product = 0
                                        vals_line = {
                                            'employee_id': item.id,
                                            'amount': amount_product,
                                            'amount_total': amount_product,
                                            'product_id': line.product_id.id,
                                            'percent': 1,
                                            'order_id': self.id,
                                            'note': 'Nhân viên thừa hưởng',
                                            'revenue_allocation_id': revenue_id.id,
                                            'quantity': line.qty
                                        }
                                        AllocationLine.create(vals_line)
                                        amount_product_debit += amount_product
                            x_total_order -= amount_product_debit
        if self.x_total_order < 0:
            if abs(self.x_total_order) == self.x_pos_partner_refund_id.x_total_order:
                if not self.x_allocation_ids:
                    Allocation = self.env['pos.revenue.allocation']
                    AllocationLine = self.env['pos.revenue.allocation.line']
                    vals = {
                        'order_id': self.id,
                        'partner_name': self.partner_id.name,
                        'partner_id': self.partner_id.id,
                        'partner_code': self.partner_id.x_code,
                        'amount_total': -self.x_total_order,
                        'amount_allocated': 0,
                        'amount_res': -self.x_total_order,
                        'date': fields.Datetime.now(),
                        'state': 'close',
                        'pos_session_id': self.session_id.id,
                    }
                    revenue_id = Allocation.create(vals)
                    for line in self.x_pos_partner_refund_id.x_allocation_ids:
                        vals_line = {
                            'employee_id': line.employee_id.id,
                            'amount': -line.amount,
                            'amount_total': -line.amount_total,
                            'percent': line.percent,
                            'order_id': self.id,
                            'product_id': line.product_id.id,
                            'note': '',
                            'revenue_allocation_id': revenue_id.id,
                            'quantity': line.quantity
                        }
                        AllocationLine.create(vals_line)

            else:
                if not self.x_allocation_ids:
                    Allocation = self.env['pos.revenue.allocation']
                    vals = {
                        'order_id': self.id,
                        'partner_name':self.partner_id.name,
                        'partner_id': self.partner_id.id,
                        'partner_code': self.partner_id.x_code,
                        'amount_total': self.x_total_order,
                        'amount_allocated': 0,
                        'amount_res':self.x_total_order ,
                        'date': fields.Datetime.now(),
                        'state': 'draft',
                        'pos_session_id': self.session_id.id,
                    }
                    revenue_id = Allocation.create(vals)

        return True
