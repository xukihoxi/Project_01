# -*- coding: utf-8 -*-

from odoo import models, fields, api

class PosWorkServiceAllocationLine(models.Model):
    _name = "pos.work.service.allocation.line"

    pos_session_id = fields.Many2one('pos.session', "Session")
    service_id = fields.Many2one('product.product', "Service")
    partner_id = fields.Many2one('res.partner', "Partner")
    employee_id = fields.Many2one('hr.employee', "Employee")
    work_lt = fields.Float("Work Lt")
    work_change = fields.Float("Work Change")
    date = fields.Datetime("Date")
    work_type = fields.Selection([('book', "Book"), ('tour', "Tour")], default='book')
    work_nv = fields.Selection([('doctor', "Doctor"), ('employee', "Employee")], default='employee')
    pos_work_service_id = fields.Many2one('pos.work.service.allocation')
    use_service_id = fields.Many2one('izi.service.card.using', "Use Service")
    use_service_line_id = fields.Many2one('izi.service.card.using.line', "Use Service Line")