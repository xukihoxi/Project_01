# -*- coding: utf-8 -*-

from odoo import fields, models, api, _


class CrmServiceCalender(models.TransientModel):
    _name = 'crm.service.calender.reminder.transient'

    partner_id = fields.Many2one('res.partner', "Partner")
    phone = fields.Char("Phone")
    date = fields.Date("Date")
    product_id = fields.Many2one('product.product', "Service")
    note = fields.Char("Note")
    description = fields.Char("Description")
    service_calender_reminder_id = fields.Many2one('crm.service.calender.reminder', "Service Calender")
    type = fields.Selection([('service', "Service"), ('card', "Card")])
    total_quantity = fields.Float('Toal Quantity')
    quantity_used = fields.Float("Quantity Used")
    origin = fields.Char("Origin")
    note_before_custom = fields.Char('Note Before Custom')
    employee_id = fields.Many2one('hr.employee', "Employee")
    master_type = fields.Selection([('htkh', "HTKH"), ('nlkh', "NLKH")])
    x_search_id = fields.Many2one('izi.product.search.card' "Search")