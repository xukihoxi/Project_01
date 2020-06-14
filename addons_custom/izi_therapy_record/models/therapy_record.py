# -*- coding: utf-8 -*-
from odoo import api, fields, models, SUPERUSER_ID, _
from datetime import date, datetime
from odoo.exceptions import UserError, ValidationError, MissingError


class TherapyRecord(models.Model):
    _name = 'therapy.record'

    name = fields.Char(string='Therapy Record')
    # target_therapy = fields.Char('Target Therapy') # mục tiêu trị liệu
    partner_id = fields.Many2one('res.partner', string='Partner')
    code = fields.Char(string='Code', related='partner_id.x_code', readonly=True)
    birthday = fields.Date(string='Birthday', related='partner_id.x_birthday', readonly=True)
    level_age_id = fields.Many2one('level.age', string='Level Age', readonly=True)
    street = fields.Char(string='Street', related='partner_id.street', readonly=True)
    state_id = fields.Many2one('res.country.state', string='State', related='partner_id.state_id', readonly=True)
    country_id = fields.Many2one('res.country', string='Country', related='partner_id.country_id', readonly=True)
    phone = fields.Char(string='Phone', related='partner_id.phone', readonly=True)
    crm_lead_tag_ids = fields.Many2many('crm.lead.tag', string='Tag', related='partner_id.x_crm_lead_tag_ids', readonly=True)
    create_date = fields.Datetime('Create Date', default=fields.Datetime.now)
    employee_id = fields.Many2one('hr.employee', 'Staff create')
    categ_id = fields.Many2one('product.category', string='Category')
    note = fields.Text('Warning Information')  # thông tin lưu ý
    body_index_ids = fields.One2many('body.index', 'therapy_record_id', 'Body Index')
    prescription_task_ids = fields.One2many('prescription.task', 'therapy_record_id',
                                            'Prescription Task')  # phiếu chỉ định

    product_therapy_ids = fields.One2many('product.therapy', 'therapy_record_id',
                                          'Product Therapy')  # tổng sản phẩm, dịch vụ tồn

    @api.model
    def default_get(self, fields):
        res = super(TherapyRecord, self).default_get(fields)
        user_id = self._context.get('uid')
        user = self.env['res.users'].browse(user_id)
        res['employee_id'] = user.id
        return res

    @api.onchange('partner_id')
    def _onchange_partner_id(self):
        if self.partner_id:
            if self.partner_id.x_birthday:
                year_birth = int(self.partner_id.x_birthday.split('-')[0])
                year_now = datetime.now().year
                age = year_now - year_birth
                return {
                    'value': {
                        'level_age_id': self.env['level.age'].search([('age_start', '<=', age), ('age_end', '>=', age)], limit=1).id
                    }
                }


# Chỉ số cơ thể
class BodyIndex(models.Model):
    _name = 'body.index'

    name = fields.Char(string='Name')
    upper_waist = fields.Float(string='Upper of Waist')  # eo trên
    lower_waist = fields.Float(string='Lower of Waist')  # eo dưới
    middle_waist = fields.Float(string='Middle Waist')  # eo giữa
    arm = fields.Float(string='Arm')  # bắp tay
    right_upper_thighs = fields.Float(string='Right Upper Thigh')  # bắp đùi phải trên
    left_upper_thighs = fields.Float(string='Left Upper Thigh')  # bắp đùi trái trên
    right_lower_thighs = fields.Float(string='Right lower Thigh')  # bắp đùi phải dưới
    left_lower_thighs = fields.Float(string='Left lower Thigh')  # bắp đùi trái dưới
    flank = fields.Float(string='Flank')  # hông
    armpit = fields.Float(string='Armpit')  # Nách
    lats = fields.Float(string='Lats')  # xoài
    back = fields.Float(string='Back')  # lưng
    weight = fields.Float(string='Weight')  # cân nặng
    high = fields.Float(string='High')  # chiều cao
    upper_abdomen = fields.Float(string='Upper Abdomen')  # bụng trên
    middle_abdomen = fields.Float(string='Middle Abdomen')  # bụng giữa
    abdomen = fields.Float(string='Abdomen')  # bụng dưới
    right_upper_calf = fields.Float(string='Right Upper Calf')  # bắp chan phải trên
    left_upper_calf = fields.Float(string='Left Upper Calf')  # bắp chan phải trên
    right_lower_calf = fields.Float(string='Right Lower Calf')  # bắp chan phải trên
    left_lower_calf = fields.Float(string='Left Lower Calf')  # bắp chan phải trên
    measurement_time = fields.Datetime(string='Measurement  time')  # Thời gian đo
    technician = fields.Many2one('hr.employee', string='Technicain')  # Kỹ thuật viên
    note = fields.Char(string='Note')
    therapy_record_id = fields.Many2one('therapy.record', string='Therapy Record')

    @api.model
    def create(self, vals):
        if vals.get('name', _('New')) == _('New'):
            if vals['therapy_record_id']:
                partner_id = self.env['therapy.record'].search([('id', '=', vals['therapy_record_id'])]).partner_id.id
                array_date = vals['measurement_time'].split(' ')[0].split('-')
                measurement_time = str(array_date[2]) + str(array_date[1]) + str(array_date[0])
                vals['name'] = 'CSGB_' + str(partner_id) + '_' + measurement_time
        return super(BodyIndex, self).create(vals)


# Phiếu chỉ định
class PrescriptionTask(models.Model):
    _name = 'prescription.task'

    name = fields.Char(string='Prescription Task')
    partner_id = fields.Many2one('res.partner', string='Partner')
    employee_id = fields.Many2one('hr.employee', string='Prescripter')
    create_date = fields.Datetime(string='Create Date', default=fields.Datetime.now)
    time_prescription = fields.Datetime(string='Prescription Time', default=fields.Datetime.now)
    note = fields.Text(string='Note')
    state = fields.Selection([('draft', 'Draft'), ('confirm', 'Confirm')], default='draft', string='State')
    prescription_task_line_warranty_ids = fields.One2many('prescription.task.line', 'prescription_task_id',
                                                          string='Prescription Task Line',
                                                          domain=lambda self: [('type', '=', 'warranty')])
    prescription_task_line_add_ids = fields.One2many('prescription.task.line', 'prescription_task_id',
                                                     string='Prescription Task Line',
                                                     domain=lambda self: [('type', '=', 'add')])
    prescription_task_line_remain_ids = fields.One2many('prescription.task.line', 'prescription_task_id',
                                                           string='Prescription Task Line',
                                                           domain=lambda self: [('type', '=', 'remain')])
    prescription_task_line_medicine_ids = fields.One2many('prescription.task.line', 'prescription_task_id',
                                                          string='Prescription Task Line',
                                                          domain=lambda self: [('type', '=', 'medicine')])
    therapy_record_id = fields.Many2one('therapy.record', 'Therapy Record')

    @api.model
    def default_get(self, fields):
        res = super(PrescriptionTask, self).default_get(fields)
        user_id = self._context.get('uid')
        user = self.env['res.users'].browse(user_id)
        res['employee_id'] = user.id
        return res

    @api.multi
    def action_get_product_remain(self):
        for task in self:
            if task.therapy_record_id:
                task.prescription_task_line_remain_ids = False
                arr_prescription_task_line_remain = []
                therapy_id = task.therapy_record_id.id
                products_therapy = task.env['product.therapy'].search([('therapy_record_id', '=', therapy_id)])
                if products_therapy:
                    for product_therapy in products_therapy:
                        if product_therapy.qty_actual != 0:
                            arr_prescription_task_line_remain.append((0, 0, {
                                'product_id': product_therapy.product_id.id,
                                'qty': 0,
                                'qty_actual': product_therapy.qty_actual,
                                'uom_id': product_therapy.uom_id.id,
                                'note': '',
                                'type': 'remain'
                            }))
                    task.prescription_task_line_remain_ids = arr_prescription_task_line_remain
                else:
                    task.prescription_task_line_remain_ids = False

    @api.multi
    def action_confirm(self):
        for task in self:
            task.write({
                'state': 'confirm',
            })

    @api.model
    def create(self, vals):
        if vals.get('name', _('New')) == _('New'):
            array_date = vals['create_date'].split(' ')[0].split('-')
            create_date = str(array_date[2]) + str(array_date[1]) + str(array_date[0])
            partner_id = self.env['res.partner'].search([('id', '=', vals['partner_id'])])
            vals['name'] = 'PCD_%s_%s' % (str(partner_id.x_code), str(create_date))
        return super(PrescriptionTask, self).create(vals)

    @api.multi
    def write(self, vals):
        if vals.get('partner_id'):
            array_date = self.create_date.split(' ')[0].split('-')
            create_date = str(array_date[2]) + str(array_date[1]) + str(array_date[0])
            partner_id = self.env['res.partner'].search([('id', '=', vals['partner_id'])])
            vals['name'] = 'PCD_%s_%s' % (str(partner_id.x_code), str(create_date))
        return super(PrescriptionTask, self).write(vals)
        print(self)



# Phiếu chỉ định Line
class PrescriptionTaskLine(models.Model):
    _name = 'prescription.task.line'

    name = fields.Char('Prescription Task Line')
    prescription_task_id = fields.Many2one('prescription.task', 'Prescription Task')
    type = fields.Selection(
        [('warranty', 'Warranty'), ('add', 'Add'), ('remain', 'Remain'), ('medicine', 'Medicine')], string='Type')
    product_id = fields.Many2one('product.product', 'Product')
    uom_id = fields.Many2one('product.uom', string='Unit of  Measure')
    qty = fields.Integer(string='Qty')  # Số lượng
    qty_actual = fields.Integer(string='Qty Actual')  # SỐ lượng khả dụng
    price_unit = fields.Float(string='Price Unit', default=0)
    amount = fields.Float(string='Amount', default=0)
    note = fields.Char('Note')
    # product_therapy_ids = fields.One2many('product.therapy', 'prescription_task_line_id',
    #                                       'Product Therapy')  # tổng sản phẩm, dịch vụ tồn

    @api.onchange('product_id')
    def _onchange_product_id(self):
        if self.product_id:
            self.uom_id = self.product_id.product_tmpl_id.uom_id.id
            self.price_unit = self.product_id.product_tmpl_id.price_unit
            therapy_record_id = self.prescription_task_id.therapy_record_id
            product_therapy = self.env['product.therapy'].search([('therapy_record_id', '=', therapy_record_id.id)])
            for product in product_therapy:
                self.qty = product.filtered(lambda pr: pr.id == self.product_id.id).qty

    @api.onchange('qty_actual')
    def _onchange_qty_actual(self):
        if self.qty_actual and self.product_id:
            self.amount = self.qty_actual * self.price_unit


# Sản phẩm/ dịch vụ tồn
class ProductTherapy(models.Model):
    _name = 'product.therapy'

    name = fields.Char('Product Therapy')
    therapy_record_id = fields.Many2one('therapy.record', 'Therapy Record')
    product_id = fields.Many2one('product.product', 'Product')
    uom_id = fields.Many2one('product.uom', string='Unit of  Measure')
    qty_used = fields.Integer(string='Qty Used')
    qty_actual = fields.Integer(string='Qty Actual', compute='_compute_qty_actual')
    qty_max = fields.Integer(string='Qty Max')
    # date_therapy = fields.Date('Date Therapy')
    # note = fields.Char(string='Note')
    # prescription_task_line_id = fields.Many2one('prescription.task.line', string='Prescription Task Line')

    @api.onchange('product_id')
    def _onchange_product_id(self):
        if self.product_id:
            self.uom_id = self.product_id.product_tmpl_id.uom_id.id

    @api.depends('qty_used', 'qty_max')
    def _compute_qty_actual(self):
        for product in self:
            product.qty_actual = product.qty_max - product.qty_used
