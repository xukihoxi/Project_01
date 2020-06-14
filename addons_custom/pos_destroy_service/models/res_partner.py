# -*- coding: utf-8 -*-
from odoo import models, api, fields , _
from odoo.exceptions import except_orm
from odoo.osv import expression

class ResPartnerCustom(models.Model):
    _inherit = 'res.partner'

    destroy_service_ids = fields.One2many('pos.destroy.service', 'partner_id', string="Destroy Service")
