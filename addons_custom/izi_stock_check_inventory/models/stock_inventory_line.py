# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError, AccessError,except_orm
from odoo.osv import osv
import xlrd
import base64


class StockInventoryCustom(models.Model):
    _inherit = 'stock.inventory.line'

    x_note = fields.Char("Ghi chú")
