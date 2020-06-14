# -*- coding: utf-8 -*-

from odoo import models, fields, api, _

class UseServiceCardUsing(models.Model):
    _inherit = 'izi.service.card.using'

    pos_work_service_lines = fields.One2many('pos.work.service.allocation.line', 'use_service_id', "Pos Work Service")


    @api.multi
    def action_done(self):
        res =  super(UseServiceCardUsing,self).action_done()
        if len(self.pos_work_service_lines) > 0:
            for line in self.pos_work_service_lines:
                line.unlink()
        if self.type == 'card':
            for line in self.service_card_ids:
                count_nv = 0
                count_bs = 0
                employee = ''
                for x in line.employee_ids:
                    employee = employee  + ', ' + str(x.name)
                    count_nv += 1
                for y in line.doctor_ids:
                    employee = employee + ', ' + str(y.name)
                    count_bs += 1
                pos_work_service_id = self.env['pos.work.service.allocation'].create({
                    'date': self.redeem_date,
                    'use_service_id' : self.id,
                    'pos_session_id': self.pos_session_id.id,
                    'partner_id': self.customer_id.id,
                    'service_id' : line.service_id.id,
                    'employee': employee,
                    'state': 'done',
                })
                for i in line.employee_ids:
                    # work_lt = 0
                    # if line.service_id.product_tmpl_id.x_counted_work == False:
                    #     work_lt = 0
                    # else:
                    #     if i.job_id.x_code == 'BSN':
                    #         work_lt = 1 * line.quantity
                    #     else:
                    #         work_lt = line.quantity*(1/(count_nv - count_bs))
                    pos_work_service_line_id = self.env['pos.work.service.allocation.line'].create({
                        'pos_session_id': self.pos_session_id.id,
                        'service_id': line.service_id.id,
                        'partner_id': self.customer_id.id,
                        'employee_id': i.id,
                        'work_lt' : line.quantity *(1/count_nv) if count_nv >0 else 0,
                        'work_change': line.quantity *(1/count_nv) if count_nv >0 else 0,
                        'date': self.redeem_date,
                        'work_nv': 'employee',
                        'pos_work_service_id': pos_work_service_id.id,
                        'use_service_id': self.id,
                        'use_service_line_id': line.id,
                    })
                for i in line.doctor_ids:
                    # work_lt = 0
                    # if line.service_id.product_tmpl_id.x_counted_work == False:
                    #     work_lt = 0
                    # else:
                    #     if i.job_id.x_code == 'BSN':
                    #         work_lt = 1 * line.quantity
                    #     else:
                    #         work_lt = line.quantity*(1/(count_nv - count_bs))
                    pos_work_service_line_id = self.env['pos.work.service.allocation.line'].create({
                        'pos_session_id': self.pos_session_id.id,
                        'service_id': line.service_id.id,
                        'partner_id': self.customer_id.id,
                        'employee_id': i.id,
                        'work_lt' : line.quantity *(1/count_bs) if count_bs >0 else 0,
                        'work_change': line.quantity *(1/count_bs) if count_bs >0 else 0,
                        'date': self.redeem_date,
                        'work_nv': 'doctor',
                        'pos_work_service_id': pos_work_service_id.id,
                        'use_service_id': self.id,
                        'use_service_line_id': line.id,
                    })
        else:
            for line in self.service_card1_ids:
                count_nv = 0
                count_bs = 0
                employee = ''
                for x in line.employee_ids:
                    employee = employee  + ', ' + str(x.name)
                    count_nv += 1
                for y in line.doctor_ids:
                    employee = employee + ', ' + str(y.name)
                    count_bs += 1
                pos_work_service_id = self.env['pos.work.service.allocation'].create({
                    'date': self.redeem_date,
                    'use_service_id' : self.id,
                    'pos_session_id': self.pos_session_id.id,
                    'partner_id': self.customer_id.id,
                    'service_id' : line.service_id.id,
                    'employee': employee,
                    'state': 'done',
                })
                for i in line.employee_ids:
                    pos_work_service_line_id = self.env['pos.work.service.allocation.line'].create({
                        'pos_session_id': self.pos_session_id.id,
                        'service_id': line.service_id.id,
                        'partner_id': self.customer_id.id,
                        'employee_id': i.id,
                        'work_lt' : line.quantity *(1/count_nv) if count_nv >0 else 0,
                        'work_change': line.quantity *(1/count_nv) if count_nv >0 else 0,
                        'date': self.redeem_date,
                        'work_nv': 'employee',
                        'pos_work_service_id': pos_work_service_id.id,
                        'use_service_id': self.id,
                        'use_service_line_id': line.id,
                    })
                for i in line.doctor_ids:
                    pos_work_service_line_id = self.env['pos.work.service.allocation.line'].create({
                        'pos_session_id': self.pos_session_id.id,
                        'service_id': line.service_id.id,
                        'partner_id': self.customer_id.id,
                        'employee_id': i.id,
                        'work_lt' : line.quantity *(1/count_bs) if count_bs >0 else 0,
                        'work_change': line.quantity *(1/count_bs) if count_bs >0 else 0,
                        'date': self.redeem_date,
                        'work_nv': 'doctor',
                        'pos_work_service_id': pos_work_service_id.id,
                        'use_service_id': self.id,
                        'use_service_line_id': line.id,
                    })

    @api.multi
    def action_confirm_refund(self):
        super(UseServiceCardUsing, self).action_confirm_refund()
        if self.option_refund == 'cancel':
            pos_work_service_allocation_obj = self.env['pos.work.service.allocation'].search(
                [('use_service_id', '=', self.id)])
            for line in pos_work_service_allocation_obj:
                line.unlink()
            pos_work_service_allocation_line_obj = self.env['pos.work.service.allocation.line'].search([('use_service_id', '=', self.id)])
            for i in pos_work_service_allocation_line_obj:
                i.unlink()

    @api.multi
    def action_apply_change_employee(self):
        pos_work_service_allocation_obj = self.env['pos.work.service.allocation'].search(
            [('use_service_id', '=', self.id)])
        for line in pos_work_service_allocation_obj:
            line.unlink()
        pos_work_service_allocation_line_obj = self.env['pos.work.service.allocation.line'].search(
            [('use_service_id', '=', self.id)])
        for i in pos_work_service_allocation_line_obj:
            i.unlink()
        if self.type == 'card':
            for line in self.service_card_ids:
                count_nv = 0
                count_bs = 0
                employee = ''
                for x in line.employee_ids:
                    employee = employee  + ', ' + str(x.name)
                    count_nv += 1
                for y in line.doctor_ids:
                    employee = employee + ', ' + str(y.name)
                    count_bs += 1
                pos_work_service_id = self.env['pos.work.service.allocation'].create({
                    'date': self.redeem_date,
                    'use_service_id' : self.id,
                    'pos_session_id': self.pos_session_id.id,
                    'partner_id': self.customer_id.id,
                    'service_id' : line.service_id.id,
                    'employee': employee,
                    'state': 'done',
                })
                for i in line.employee_ids:
                    pos_work_service_line_id = self.env['pos.work.service.allocation.line'].create({
                        'pos_session_id': self.pos_session_id.id,
                        'service_id': line.service_id.id,
                        'partner_id': self.customer_id.id,
                        'employee_id': i.id,
                        'work_lt' : line.quantity *(1/count_nv) if count_nv >0 else 0,
                        'work_change': line.quantity *(1/count_nv) if count_nv >0 else 0,
                        'date': self.redeem_date,
                        'work_nv': 'employee',
                        'pos_work_service_id': pos_work_service_id.id,
                        'use_service_id': self.id,
                        'use_service_line_id': line.id
                    })
                for i in line.doctor_ids:
                    pos_work_service_line_id = self.env['pos.work.service.allocation.line'].create({
                        'pos_session_id': self.pos_session_id.id,
                        'service_id': line.service_id.id,
                        'partner_id': self.customer_id.id,
                        'employee_id': i.id,
                        'work_lt' : line.quantity *(1/count_bs) if count_bs >0 else 0,
                        'work_change': line.quantity *(1/count_bs) if count_bs >0 else 0,
                        'date': self.redeem_date,
                        'work_nv': 'doctor',
                        'pos_work_service_id': pos_work_service_id.id,
                        'use_service_id': self.id,
                        'use_service_line_id': line.id
                    })
        else:
            for line in self.service_card1_ids:
                count_nv = 0
                count_bs = 0
                employee = ''
                for x in line.employee_ids:
                    employee = employee  + ', ' + str(x.name)
                    count_nv += 1
                for y in line.doctor_ids:
                    employee = employee + ', ' + str(y.name)
                    count_bs += 1
                pos_work_service_id = self.env['pos.work.service.allocation'].create({
                    'date': self.redeem_date,
                    'use_service_id' : self.id,
                    'pos_session_id': self.pos_session_id.id,
                    'partner_id': self.customer_id.id,
                    'service_id' : line.service_id.id,
                    'employee': employee,
                    'state': 'done',
                })
                for i in line.employee_ids:
                    pos_work_service_line_id = self.env['pos.work.service.allocation.line'].create({
                        'pos_session_id': self.pos_session_id.id,
                        'service_id': line.service_id.id,
                        'partner_id': self.customer_id.id,
                        'employee_id': i.id,
                        'work_lt' : line.quantity *(1/count_nv) if count_nv >0 else 0,
                        'work_change': line.quantity *(1/count_nv) if count_nv >0 else 0,
                        'date': self.redeem_date,
                        'work_nv': 'employee',
                        'pos_work_service_id': pos_work_service_id.id,
                        'use_service_id': self.id,
                        'use_service_line_id': line.id,
                    })
                for i in line.doctor_ids:
                    pos_work_service_line_id = self.env['pos.work.service.allocation.line'].create({
                        'pos_session_id': self.pos_session_id.id,
                        'service_id': line.service_id.id,
                        'partner_id': self.customer_id.id,
                        'employee_id': i.id,
                        'work_lt' : line.quantity *(1/count_bs) if count_bs >0 else 0,
                        'work_change': line.quantity *(1/count_bs) if count_bs >0 else 0,
                        'date': self.redeem_date,
                        'work_nv': 'doctor',
                        'pos_work_service_id': pos_work_service_id.id,
                        'use_service_id': self.id,
                        'use_service_line_id': line.id,
                    })
        super(UseServiceCardUsing, self).action_apply_change_employee()


    @api.multi
    def action_all_work_one(self):
        service_id = self.env['izi.service.card.using'].search([('id', '=', '1140')])
        service_id810 = self.env['izi.service.card.using'].search([('id', '=', '810')])
        service_id810.signature_image = service_id.signature_image
        # pos_work = self.env['pos.work.service.allocation'].search([])
        # for i in pos_work:
        #     i.unlink()
        # pos_work_line = self.env['pos.work.service.allocation.line'].search([])
        # for x in pos_work_line:
        #     x.unlink()
        # use_service = self.env['izi.service.card.using'].search([('id', '>=', '1'), ('id', '<=','500')])
        # for tmp in use_service:
        #     if (tmp.state == 'cancel' and tmp.option_refund == 'cancel') or (tmp.state == 'cancel' and (not tmp.option_refund)):
        #         continue
        #     if tmp.type == 'card':
        #         for line in tmp.service_card_ids:
        #             count_nv = 0
        #             count_bs = 0
        #             employee = ''
        #             for x in line.employee_ids:
        #                 employee = employee  + ', ' + str(x.name)
        #                 count_nv += 1
        #                 if x.job_id.x_code == 'BSN':
        #                     count_bs += 1
        #             for y in line.doctor_ids:
        #                 employee = employee + ', ' + str(y.name)
        #                 count_nv += 1
        #                 if y.job_id.x_code == 'BSN':
        #                     count_bs += 1
        #             pos_work_service_id = self.env['pos.work.service.allocation'].create({
        #                 'date': tmp.redeem_date,
        #                 'use_service_id' : tmp.id,
        #                 'pos_session_id': tmp.pos_session_id.id,
        #                 'partner_id': tmp.customer_id.id,
        #                 'service_id' : line.service_id.id,
        #                 'employee': employee,
        #                 'state': 'done',
        #             })
        #             for i in line.employee_ids:
        #                 work_lt = 0
        #                 if line.service_id.product_tmpl_id.x_counted_work == False:
        #                     work_lt = 0
        #                 else:
        #                     if i.job_id.x_code == 'BSN':
        #                         work_lt = 1 * line.quantity
        #                     else:
        #                         work_lt = line.quantity*(1/(count_nv - count_bs))
        #                 pos_work_service_line_id = self.env['pos.work.service.allocation.line'].create({
        #                     'pos_session_id': tmp.pos_session_id.id,
        #                     'service_id': line.service_id.id,
        #                     'partner_id': tmp.customer_id.id,
        #                     'employee_id': i.id,
        #                     'work_lt' : work_lt,
        #                     'work_change': work_lt,
        #                     'date': tmp.redeem_date,
        #                     'work_type': 'book',
        #                     'pos_work_service_id': pos_work_service_id.id,
        #                     'use_service_id': tmp.id,
        #                     'use_service_line_id': line.id,
        #                 })
        #             for i in line.doctor_ids:
        #                 work_lt = 0
        #                 if line.service_id.product_tmpl_id.x_counted_work == False:
        #                     work_lt = 0
        #                 else:
        #                     if i.job_id.x_code == 'BSN':
        #                         work_lt = 1 * line.quantity
        #                     else:
        #                         work_lt = line.quantity*(1/(count_nv - count_bs))
        #                 pos_work_service_line_id = self.env['pos.work.service.allocation.line'].create({
        #                     'pos_session_id': tmp.pos_session_id.id,
        #                     'service_id': line.service_id.id,
        #                     'partner_id': tmp.customer_id.id,
        #                     'employee_id': i.id,
        #                     'work_lt' : work_lt,
        #                     'work_change': work_lt,
        #                     'date': tmp.redeem_date,
        #                     'work_type': 'tour',
        #                     'pos_work_service_id': pos_work_service_id.id,
        #                     'use_service_id': tmp.id,
        #                     'use_service_line_id': line.id,
        #                 })
        #     else:
        #         for line in tmp.service_card1_ids:
        #             count_nv = 0
        #             count_bs = 0
        #             employee = ''
        #             for x in line.employee_ids:
        #                 employee = employee  + ', ' + str(x.name)
        #                 count_nv += 1
        #                 if x.job_id.x_code == 'BSN':
        #                     count_bs += 1
        #             for y in line.doctor_ids:
        #                 employee = employee + ', ' + str(y.name)
        #                 count_nv += 1
        #                 if y.job_id.x_code == 'BSN':
        #                     count_bs += 1
        #             pos_work_service_id = self.env['pos.work.service.allocation'].create({
        #                 'date': tmp.redeem_date,
        #                 'use_service_id' : tmp.id,
        #                 'pos_session_id': tmp.pos_session_id.id,
        #                 'partner_id': tmp.customer_id.id,
        #                 'service_id' : line.service_id.id,
        #                 'employee': employee,
        #                 'state': 'done',
        #             })
        #             for i in line.employee_ids:
        #                 work_lt = 0
        #                 if line.service_id.product_tmpl_id.x_counted_work == False:
        #                     work_lt = 0
        #                 else:
        #                     if i.job_id.x_code == 'BSN':
        #                         work_lt = 1 * line.quantity
        #                     else:
        #                         work_lt = line.quantity*(1/(count_nv - count_bs))
        #                 pos_work_service_line_id = self.env['pos.work.service.allocation.line'].create({
        #                     'pos_session_id': tmp.pos_session_id.id,
        #                     'service_id': line.service_id.id,
        #                     'partner_id': tmp.customer_id.id,
        #                     'employee_id': i.id,
        #                     'work_lt' : work_lt,
        #                     'work_change': work_lt,
        #                     'date': tmp.redeem_date,
        #                     'work_type': 'book',
        #                     'pos_work_service_id': pos_work_service_id.id,
        #                     'use_service_id': tmp.id,
        #                     'use_service_line_id': line.id,
        #                 })
        #             for i in line.doctor_ids:
        #                 work_lt = 0
        #                 if line.service_id.product_tmpl_id.x_counted_work == False:
        #                     work_lt = 0
        #                 else:
        #                     if i.job_id.x_code == 'BSN':
        #                         work_lt = 1 * line.quantity
        #                     else:
        #                         work_lt = line.quantity*(1/(count_nv - count_bs))
        #                 pos_work_service_line_id = self.env['pos.work.service.allocation.line'].create({
        #                     'pos_session_id': tmp.pos_session_id.id,
        #                     'service_id': line.service_id.id,
        #                     'partner_id': tmp.customer_id.id,
        #                     'employee_id': i.id,
        #                     'work_lt' : work_lt,
        #                     'work_change': work_lt,
        #                     'date': tmp.redeem_date,
        #                     'work_type': 'tour',
        #                     'pos_work_service_id': pos_work_service_id.id,
        #                     'use_service_id': tmp.id,
        #                     'use_service_line_id': line.id,
        #                 })