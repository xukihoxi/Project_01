
from odoo import api, fields, models, SUPERUSER_ID, _
from datetime import date
from odoo.exceptions import UserError, ValidationError, MissingError


class BodyArea(models.Model):
    _name = 'body.area'

    name = fields.Char(string="Name Area")


