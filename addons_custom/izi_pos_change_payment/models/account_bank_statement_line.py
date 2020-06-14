# # -*- coding: utf-8 -*-
#
# from odoo import models, fields, api
# from odoo.exceptions import except_orm
# from datetime import datetime
#
# class PosChangePayment(models.Model):
#     _inherit = 'account.bank.statement.line'
#
#     @api.multi
#     def unlink(self):
#         if self.pos_statement_id.x_status == 'change':
#             # cập nhật lại phiếu mua hàng
#             count = 0
#             if self.x_vc_id:
#                 self.x_vc_id.x_status = 'using'
#                 self.x_vc_id.x_user_id = False
#             # Nếu là hình thức là ghi nhận doanh thu
#             #  => Xóa doanh thu ghi nhận và xóa điểm được cộng khi thanh toán công nợ
#             # Xóa phân bổ doanh thu
#             for x in self.statement_id.pos_session_id.config_id:
#                 journal_loyal_ids = x.journal_loyal_ids.ids if x.journal_loyal_ids else False
#                 if journal_loyal_ids:
#                     if self.journal_id.id in journal_loyal_ids:
#                         revenue = self.env['crm.vip.customer.revenue'].search(
#                             [('partner_id', '=', self.partner_id.id), ('order_id', '=', self.pos_statement_id.id),
#                              ('journal_id', '=', self.journal_id.id),
#                              ('amount', '=', self.amount), ('date', '=', self.pos_statement_id.date_order)],
#                             limit=1)
#                         if revenue:
#                             self.partner_id.update({'x_loyal_total': self.partner_id.x_loyal_total - revenue.amount})
#                             revenue.unlink()
#                         else:
#                             raise except_orm("2", ("2"))
#                 # Nếu hình thức là tiền đặt cọc thị xóa dong dùng đặt cọc để thanh toán đi để cộng lại tiền cho khách hàng
#                 journal_deposit_id = x.journal_deposit_id.id if x.journal_deposit_id else False
#                 if journal_deposit_id:
#                     if self.journal_id.id == journal_deposit_id:
#                         customer_deposit = self.env['pos.customer.deposit.line'].search(
#                             [('partner_id', '=', self.partner_id.id),
#                              ('date', '=', self.pos_statement_id.date_order),
#                              ('journal_id', '=', self.journal_id.id),
#                              ('amount', '=', self.amount), ('x_type', '=', 'deposit'),
#                              ('type', '=', 'payment')], limit=1)
#                         if customer_deposit:
#                             customer_deposit.state = 'draft'
#                             customer_deposit.unlink()
#                         else:
#                             raise except_orm("5", ("5"))
#                 # Nếu là thẻ tiền thì trả tiền cho khách hàng sau đó xóa lịch sủ sử dụng thẻ tiền
#                 journal_vm_id = x.journal_vm_id.id if x.journal_vm_id else False
#                 if journal_vm_id:
#                     if self.journal_id.id == journal_vm_id:
#                         vm_arg_history = []
#                         self.env.cr.execute("""
#                                                     SELECT id
#                                                     FROM pos_virtual_money_history
#                                                     WHERE (create_date + INTERVAL '7' HOUR)::date = %s ORDER BY id desc
#                                                     """, (self.pos_statement_id.date_order,))
#                         res = self.env.cr.fetchall()
#                         columns = []
#                         for data in res:
#                             columns.append(data[0])
#                         print(res)
#                         print(columns)
#                         if columns:
#                             count = 1
#                             amount_vm = 0
#                             date = datetime.today().date()
#                             for x in columns:
#                                 print(x)
#                                 y = self.env['pos.virtual.money.history'].search([('id', '=', str(x))])
#                                 if count == 1:
#                                     amount_vm = 0
#                                     date = y.create_date
#                                     count += 1
#                                 if date == y.create_date:
#                                     amount_vm += y.amount
#                                     vm_arg_history.append(y)
#                                 else:
#                                     count = 1
#                                     vm_arg_history = []
#                                 if amount_vm == self.amount:
#                                     break
#                             for line in vm_arg_history:
#                                 line.vm_id.money_used -= line.amount
#                                 line.unlink()
#                         else:
#                             raise except_orm("3", ("3"))