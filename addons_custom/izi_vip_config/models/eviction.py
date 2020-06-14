# -*- coding: utf-8 -*-

from odoo import models, fields, api,_

class Eviction(models.Model):
    _name = 'izi.vip.config.eviction'

    vip_config_id = fields.Many2one('izi.vip.config', string='Vip config')
    name = fields.Char('Name')
    rank_id = fields.Many2one('crm.vip.rank', string=u'Hạng',required=1)
    point = fields.Float('Point',required=1)
    lines =fields.One2many('izi.vip.config.eviction.line','eviction_id',string='Lines')

    _sql_constraints = [
        ('name_uniq', 'unique (name)', 'Name must be unique!'),
    ]

class EvictionLine(models.Model):
    _name = 'izi.vip.config.eviction.line'

    eviction_id = fields.Many2one('izi.vip.config.eviction')
    product_id = fields.Many2one('product.product', string='Product')
    uom_id = fields.Many2one('product.uom', string='Uom')
    qty = fields.Float('Qty')
    price_unit = fields.Float('Price')

    @api.onchange('product_id')
    def _onchange_product_uom(self):
        if self.product_id:
            self.uom_id = self.product_id.product_tmpl_id.uom_id.id
            self.price_unit = self.product_id.product_tmpl_id.list_price
