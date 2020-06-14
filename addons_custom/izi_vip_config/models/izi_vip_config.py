# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import except_orm
from datetime import datetime



class VipConfig(models.Model):
    _name = 'izi.vip.config'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char('Name', track_visibility='always', required=1)
    from_date = fields.Date('From date', track_visibility='onchange')
    to_date = fields.Date('To date', track_visibility='onchange')
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.user.company_id.id,
                                 track_visibility='onchange')
    config_id = fields.Many2one('pos.config', string='Pos config', track_visibility='onchange')
    round = fields.Integer('Round', track_visibility='onchange')
    accumulation_ids = fields.One2many('izi.vip.config.accumulation', 'vip_config_id', string='Accumulation')
    eviction_ids = fields.One2many('izi.vip.config.eviction', 'vip_config_id', string='Eviction')
    type = fields.Selection([('accumulation', 'Accumulation'), ('eviction', 'Eviction')], 'Type')
    note = fields.Text('Note')
    active = fields.Boolean('Active', default=False)

    def _check_config(self, company, config, from_date, to_date,type):
        VipConfig = self.env['izi.vip.config'].search(
            [('active', '=', True),('type', '=', type), ('company_id', '=', company), ('config_id', '=', config)])
        for vip in VipConfig:
            if (vip.from_date < from_date and vip.to_date > from_date) or (
                    vip.from_date < to_date and vip.to_date > to_date) or (
                    vip.from_date >= from_date and vip.to_date <= to_date):
                raise except_orm('Cảnh báo!', (
                    "Bạn đã cấu hình quy tắc cho điểm bán hàng này. Vui lòng kiểm tra lại!"))
        return True

    @api.model
    def create(self, vals):
        check = self._check_config(vals.get("company_id"),vals.get("config_id"),vals.get("from_date"),vals.get("to_date"),vals.get("type"))
        vals['active'] = True
        return super(VipConfig,self).create(vals)

