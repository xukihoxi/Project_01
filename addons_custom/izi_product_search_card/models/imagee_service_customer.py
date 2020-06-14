# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError, except_orm, MissingError, ValidationError
from datetime import datetime, timedelta, date as my_date
from dateutil.relativedelta import relativedelta
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT
import logging

class ImageService(models.TransientModel):
    _name = 'image.service.transient'

    image = fields.Binary("Image")
    use_service_id = fields.Many2one('izi.service.card.using', "Use Service")
    date = fields.Datetime("Date")
    x_search_id = fields.Many2one('izi.product.search.card', 'Image Service')