# -*- coding: utf-8 -*-

from odoo import models, fields, api
from datetime import datetime, timedelta
from odoo.exceptions import ValidationError, except_orm


class Claim(models.Model):
    _name = 'crm.claim'
    _description = 'Claim'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string="Subject")
    claim_date = fields.Datetime(string="Claim date", track_visibility='onchange')
    partner_id = fields.Many2one('res.partner', string="Partner", track_visibility='onchange')
    crm_team_id = fields.Many2one(related='partner_id.x_crm_team_id', string="Team", readonly=1)
    user_id = fields.Many2one(related='partner_id.user_id', string="User", readonly=1)
    type_id = fields.Many2one('crm.claim.type', string="Type", track_visibility='onchange')
    content = fields.Text(string="Content", track_visibility='onchange')
    handler_id = fields.Many2one('res.users', string="Handler", track_visibility='onchange')
    deadline = fields.Date(string="Deadline", track_visibility='onchange')
    cause = fields.Text(string="Cause", track_visibility='onchange')
    resolution = fields.Text(string="Resolution", track_visibility='onchange')
    cause_refuse = fields.Text(string="Cause refuse", track_visibility='onchange')
    state = fields.Selection([('new', 'New'), ('processing', 'Processing'), ('done', 'Done'), ('refuse', 'Refuse')], default='new', string="State", track_visibility='onchange')

    @api.multi
    def action_assign(self):
        if self.handler_id and self.deadline:
            if self.state != 'new': raise except_orm("Thông báo", "Khiếu nại đã thay đổi trạng thái vui lòng tải lại trang web!")
            self.state = "processing"
        else:
            view_id = self.env.ref('izi_crm_claim.crm_claim_popup_assign_form_view').id
            return {
                'name': "Chọn người xử lý và hạn chót",
                'type': 'ir.actions.act_window',
                'res_model': 'crm.claim',
                'res_id': self.id,
                'view_type': 'form',
                'view_mode': 'form',
                'views': [(view_id, 'form')],
                'target': 'new',
            }

    @api.multi
    def action_handle(self):
        if self.cause and self.resolution:
            if self.state != 'processing': raise except_orm("Thông báo", "Khiếu nại đã thay đổi trạng thái vui lòng tải lại trang web!")
            self.write({
                'state': "done"
            })
        else:
            view_id = self.env.ref('izi_crm_claim.crm_claim_popup_handle_form_view').id
            return {
                'name': "Nhập thông tin xử lý",
                'type': 'ir.actions.act_window',
                'res_model': 'crm.claim',
                'res_id': self.id,
                'view_type': 'form',
                'view_mode': 'form',
                'views': [(view_id, 'form')],
                'target': 'new',
            }

    @api.multi
    def action_refuse(self):
        if self.cause_refuse:
            self.write({
                'state': "refuse"
            })
        else:
            view_id = self.env.ref('izi_crm_claim.crm_claim_popup_refuse_form_view').id
            return {
                'name': "Nhập lý do từ chối",
                'type': 'ir.actions.act_window',
                'res_model': 'crm.claim',
                'res_id': self.id,
                'view_type': 'form',
                'view_mode': 'form',
                'views': [(view_id, 'form')],
                'target': 'new',
            }

    @api.multi
    def action_back(self):
        if self.state in ('processing', 'refuse'):
            self.state = "new"
        elif self.state == 'done':
            self.state = 'processing'

    @api.model
    def create(self, vals):
        claim = super(Claim,self).create(vals)
        if not claim.name:
            claim.write({
                'name': '%s - %s' % (str(claim.partner_id.name), str(claim.type_id.name))
            })
        return claim


class ClaimType(models.Model):
    _name = 'crm.claim.type'
    _description = 'Claim type'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string="Name")
