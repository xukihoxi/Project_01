
import re
import logging
from odoo import api, fields, models
from odoo.tools.translate import _
_logger = logging.getLogger(__name__)


class District(models.Model):
    _description = "District"
    _name = 'res.district'
    _order = 'code'

    state_id = fields.Many2one('res.country.state', string='State')
    name = fields.Char(string='District Name')
    code = fields.Char(string='State Code', help='The state code.', required=True)

    _sql_constraints = [
        ('name_code_uniq', 'unique(state_id, code)', 'The code of the district must be unique by state !')
    ]

    @api.model
    def name_search(self, name='', args=None, operator='ilike', limit=100):
        if args is None:
            args = []
        if self.env.context.get('state_id'):
            args = args + [('state_id', '=', self.env.context.get('state_id'))]
        firsts_records = self.search([('code', '=ilike', name)] + args, limit=limit)
        search_domain = [('name', operator, name)]
        search_domain.append(('id', 'not in', firsts_records.ids))
        records = firsts_records + self.search(search_domain + args, limit=limit)
        return [(record.id, record.display_name) for record in records]