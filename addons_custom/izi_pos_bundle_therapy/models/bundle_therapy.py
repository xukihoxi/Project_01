# -*- coding: utf-8 -*-
from odoo import api, fields, models, SUPERUSER_ID, _
from datetime import date, datetime
from odoo.exceptions import UserError, ValidationError, MissingError


# gói liệu trình
class BundleTherapy(models.Model):
    _name = 'bundle.therapy'

    name = fields.Char(string='Bundle Therapy')
    amount_total = fields.Float(string='Amount total')
    order_id = fields.Many2one('pos.order', string='Order')
    partner_id = fields.Many2one('res.partner', related='order_id.partner_id', string="Partner")
    state = fields.Selection([('in_therapy', 'In Therapy'), ('committed', 'Committed')], default="in_therapy", string='State')
    file_attach = fields.Binary(string='File Attach')
    bundle_therapy_line_ids = fields.One2many('bundle.therapy.line', 'bundle_therapy_id', string='Bundle Therapy Line')
    therapy_record_id = fields.Many2one('therapy.record', string='Therapy Record')

    # @api.model
    # def create(self, vals):
    #     order_id = self.env['pos.order'].search([('id', '=', vals['order_id'])])
    #     partner_code = order_id.partner_id.x_code
    #     vals['name'] = 'GLT_' + str(partner_code) + '_' + str(datetime.today())
    #     return super(BundleTherapy, self).create(vals)

    @api.model
    def create(self, vals):
        bundle_therapy = super(BundleTherapy, self).create(vals)
        bundle_therapy.write({
            'name': 'GLT_%s_%s' % (str(bundle_therapy.partner_id.x_code), str(bundle_therapy.create_date))
        })
        return bundle_therapy

# gói liệu trình line
class BundleTherapyLine(models.Model):
    _name = 'bundle.therapy.line'

    name = fields.Char('Bundle Therapy')
    product_id = fields.Many2one('product.product', string='Product')
    uom_id = fields.Many2one('product.uom', string='Unit of  Measure')
    qty = fields.Integer(string='Qty')
    body_area_ids = fields.Many2many('body.area', string="Body area")
    bundle_therapy_id = fields.Many2one('bundle.therapy', string='Bundle Therapy')
