# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class Accumulation(models.Model):
    _name = 'izi.vip.config.accumulation'

    vip_config_id = fields.Many2one('izi.vip.config', string='Vip config')
    rank_id = fields.Many2one('crm.vip.rank', string=u'Hạng', required=1)
    revenue= fields.Float('Revenue',required=1)
    factor = fields.Float('Factor',required=1)
    note = fields.Text('Note')
