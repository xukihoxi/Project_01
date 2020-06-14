# -*- coding: utf-8 -*-
from odoo import models, api, fields , _
from odoo.exceptions import except_orm
from odoo.osv import expression

class ResPartnerCustom(models.Model):
    _inherit = 'res.partner'

    deposit_line_ids = fields.One2many('pos.customer.deposit.line', 'partner_id', string="Destroy Service")
