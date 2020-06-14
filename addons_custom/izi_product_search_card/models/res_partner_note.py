# -*- coding: utf-8 -*-

from odoo import models, fields, api
from datetime import datetime
from odoo.exceptions import UserError, MissingError, ValidationError
from datetime import date, datetime
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT

class ResPartnerNote(models.TransientModel):
    _name = 'res.partner.note'

    note = fields.Char("Note")
    x_search_id = fields.Many2one('izi.product.search.card')
