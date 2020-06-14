# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from datetime import datetime
from odoo.exceptions import except_orm, ValidationError
from datetime import datetime, timedelta, date as my_date
from dateutil.relativedelta import relativedelta


class ServiceCardUsingLine(models.Model):
    _name = 'izi.service.card.using.line'
    # _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(related='service_id.name', string="Code")
    service_id = fields.Many2one('product.product', "Service")
    max_use_count = fields.Float("Max Use Count")
    paid_count = fields.Float("Paid Count")
    used_count = fields.Float("Used Count")
    quantity = fields.Float("Quantity")
    uom_id = fields.Many2one('product.uom')
    employee_ids = fields.Many2many('hr.employee','hr_employee_izi_service_card_using_line_rel', 'izi_service_card_using_line_id', 'hr_employee_id', string="Employee")
    using_id = fields.Many2one('izi.service.card.using', "Using", ondelete='cascade')
    serial_id = fields.Many2one('stock.production.lot', "Serial")
    detail_serial_id = fields.Many2one('izi.service.card.detail', "Detail Serial")
    price_unit = fields.Float("Price Unit")
    discount = fields.Float("Discount(%)")
    amount = fields.Float("Amount Total", compute="_compute_amount_total", store=True)
    customer_rate = fields.Selection([(0, 'Normal'), (1, 'Good'), (2, "Excellent"), (3, "No rate")], default=3)
    customer_comment = fields.Text("Customer Comment")
    is_gift = fields.Boolean("Gift", default=False)
    work_type = fields.Selection([('book', "Book"), ('tour', "Tour")], default='book')
    doctor_ids = fields.Many2many('hr.employee', 'hr_employee_tour_izi_service_card_using_line_rels', 'izi_service_card_using_line_id', 'hr_employee_id', string="Doctor")
    branch_id = fields.Many2one('res.branch', related="using_id.pos_session_id.branch_id", string="Branch", store=True)
    # tiennq them nut bao hanh 06/08
    show_button = fields.Boolean('Visible', compute='_compute_show_button')
    guarantee_id = fields.Many2one('guarantee.line', "Guarantee")
    note = fields.Char("Note")
    edit_price = fields.Boolean(string="Edit price", compute='_compute_edit_price', copy=False)

    @api.depends('service_id')
    def _compute_edit_price(self):
        for s in self:
            for product_edit_price in s.using_id.pos_session_id.config_id.product_edit_price_ids:
                print(product_edit_price)
                print(s.service_id.id)
                if s.service_id.id == product_edit_price.id:
                    s.edit_price = True
                    break

    @api.depends('service_id')
    def _compute_show_button(self):
        for s in self:
            if s.service_id.x_guarantee == True:
                s.show_button = True
            else:
                s.show_button = False

    # @api.constrains('service_id')
    # def _check_service_id(self):
    #     for s in self:
    #         if s.service_id.x_type_service == 'spa' and s.service_id.type == 'service' and s.service_id.bom_service_count == 0:
    #             raise ValidationError('Dịch vụ [%s]%s có loại dịch vụ là %s bắt buộc phải cấu hình nguyên vật liệu!' % (str(s.service_id.default_code), str(s.service_id.name), str(s.service_id.x_type_service)))

    # @api.constrains('quantity')
    # def _check_quantity(self):
    #     for s in self:
    #         if s.quantity <= 0:
    #             raise ValidationError('Số lượng dịch vụ [%s]%s phải lớn hơn 0!' % (str(s.service_id.default_code), str(s.service_id.name)))

    @api.multi
    def action_guarantee(self):
        if not self.guarantee_id:
            vals = {
                'partner_id': self.using_id.customer_id.id,
                'service_id': self.service_id.id,
                'number':'',
            }
            guar = self.env['guarantee.line'].create(vals)
            self.guarantee_id = guar.id
            ctx = self.env.context.copy()
            ctx.update({'using_id': self.id})
            view = self.env.ref('guarantee_service.view_card_guarantee_form')
            return {
                'name': _('Thẻ bảo hành'),
                'type': 'ir.actions.act_window',
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'guarantee.line',
                'views': [(view.id, 'form')],
                'view_id': view.id,
                'res_id': guar.id,
                'target': 'new',
                'context': ctx,
            }
        else:
            view = self.env.ref('guarantee_service.view_card_guarantee_form')
            return {
                'name': _('Thẻ bảo hành'),
                'type': 'ir.actions.act_window',
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'guarantee.line',
                'views': [(view.id, 'form')],
                'view_id': view.id,
                'res_id': self.guarantee_id.id,
                'target': 'new',
                'context': self.env.context,
            }

    @api.onchange('employee_ids', 'service_id', 'quantity')
    def onchange_employee(self):
        ids = []
        # branch_ids = self.env['res.branch'].search([('brand_id', '=', self.using_id.pos_session_id.config_id.pos_branch_id.id)])
        department_ids = self.env['hr.department'].search(
            [('x_branch_id', '=', self.using_id.pos_session_id.config_id.pos_branch_id.id)])
        for line in department_ids:
            ids_o2m = self.env['hr.employee'].search([('department_id', '=', line.id), ('x_work_service', '=', True)])
            for id in ids_o2m:
                ids.append(id.id)
        return {
            'domain': {
                'employee_ids': [('id', 'in', ids)]
            }
        }

    @api.onchange('service_id', 'quantity')
    def onchange_service(self):
        price = 0
        if self.service_id:
            if self.using_id.type == 'service':
                if self.using_id.pricelist_id:
                    price = self.using_id.pricelist_id.get_product_price(self.service_id, self.quantity or 1.0, self.using_id.customer_id)
        self.price_unit = price

    @api.onchange('service_id')
    def onchange_service_quantity(self):
        self.quantity = 1

    @api.onchange('quantity', 'price_unit')
    def onchange_quantity_price(self):
        self.amount = self.quantity * self.price_unit
        if self.quantity < 0:
            raise except_orm('Cảnh báo!', ("Số lượng phải lớn hơn không. Vui lòng kiểm tra lại"))
        if self.using_id.type == 'card':
            if self.paid_count - self.used_count < self.quantity:
                raise except_orm('Cảnh báo!', ("Bạn không thể sử dụng nhiều hơn số lần còn lại"))

    @api.depends('quantity', 'price_unit','discount')
    def _compute_amount_total(self):
        for line in self:
            line.amount = line.quantity * line.price_unit * (1 -(line.discount/100))

    '''
    Dự án Amia không sử dụng chức năng bán dưới giá 29/11/2019
    @api.onchange('price_unit')
    def _onchange_price_unit(self):
        if self.using_id.type == 'service':
            if self.service_id:
                if self.using_id.pricelist_id:
                    price = self.using_id.pricelist_id.get_product_price(self.service_id, self.quantity or 1.0,
                                                                         self.using_id.customer_id)
                    if self.price_unit < price:
                        warning = {
                            'title': 'Cảnh báo!',
                            'message': _('Dịch vụ "' + str(
                                self.service_id.product_tmpl_id.name) + ',Giá niêm yết ' + str(
                                price)) + ', Giá bán.'+ str(self.price_unit * (100 - self.discount)/ 100) + ' Dưới mức giá bán tối thiểu cần phê duyêt. !'
                        }
                        return {'warning': warning}
    '''

    @api.onchange('service_id')
    def _onchange_izi_pos_product_id(self):
        list = []
        for item in self.using_id.pos_session_id.config_id.x_category_ids:
            product_ids = self.env['product.product'].search(
                [('pos_categ_id', '=', item.id), ('active', '=', True), ('product_tmpl_id.type', '=', 'service')])
            for product_id in product_ids:
                list.append(product_id.id)
        return {
            'domain': {'service_id': [('id', 'in', list)]}
        }