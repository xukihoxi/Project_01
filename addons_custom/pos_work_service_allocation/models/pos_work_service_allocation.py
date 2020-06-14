# -*- coding: utf-8 -*-

from odoo import models, fields, api, _

class PosWorkServiceAllocation(models.Model):
    _name = 'pos.work.service.allocation'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char('Name', default="/", track_visibility='onchange')
    date = fields.Datetime("Date", track_visibility='onchange')
    use_service_id = fields.Many2one('izi.service.card.using', "Use Service", track_visibility='onchange')
    pos_session_id = fields.Many2one('pos.session', "Session", track_visibility='onchange')
    partner_id = fields.Many2one('res.partner', "Partner", track_visibility='onchange')
    service_id = fields.Many2one('product.product', "Service", track_visibility='onchange')
    employee = fields.Char("Employee", track_visibility='onchange')
    pos_work_lines = fields.One2many('pos.work.service.allocation.line','pos_work_service_id', "Pos Work Line")
    state = fields.Selection([('draft', "Draft"), ('done', "Done")], track_visibility='onchange')

    @api.model
    def create(self, vals):
        if vals.get('name', _('New')) == _('New'):
            vals['name'] = self.env['ir.sequence'].next_by_code('pos.work.service.allocation') or _('New')
        return super(PosWorkServiceAllocation, self).create(vals)
