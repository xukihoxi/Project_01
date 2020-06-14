from odoo import models, fields, api,_
from datetime import datetime
from odoo.exceptions import ValidationError, RedirectWarning, except_orm
from datetime import date, datetime
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from odoo.tools import mute_logger
import logging



class StockPickingInherit(models.Model):
    _inherit = 'stock.picking'

    x_reason = fields.Many2one('stock.picking.reason', string='Reason')