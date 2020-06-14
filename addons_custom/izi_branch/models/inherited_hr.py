# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import except_orm
import re

class CrmTeam(models.Model):
    _inherit = 'hr.department'

    x_branch_id = fields.Many2one('res.branch', "Branch")

