# -*- coding: utf-8 -*-

from odoo import models, fields, api,_
from datetime import datetime
from odoo.exceptions import ValidationError, RedirectWarning, except_orm
from datetime import date, datetime
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from odoo.tools import mute_logger
import logging

class ResPartner(models.Model):
    _inherit = 'res.partner'

    inventory_delivery_ids = fields.One2many('product.delivery.line', 'partner_id', 'Inventory')
    # payment_ids = fields.One2many(related='pos_order_id.statement_ids', string="Payment")
    # toolbar = "True"
