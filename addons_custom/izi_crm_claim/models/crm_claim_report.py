# -*- coding: utf-8 -*-

from odoo import models, fields, api
from datetime import datetime, timedelta
from odoo.exceptions import ValidationError, except_orm


class Claim(models.TransientModel):
    _name = 'crm.claim.report'


    url_report = fields.Text(string="Url report", default="https://izisolution.vn/")

