# -*- coding: utf-8 -*-
from odoo import models, api, fields , _
import json
import os
from os import listdir
from os.path import isfile, join
import logging
from odoo.exceptions import MissingError

logger = logging.getLogger(__name__)


class ResPartnerFile(models.TransientModel):
    _name = 'res.partner.file'
    _description = "Ảnh hồ sơ khách hàng"

    @api.model
    def default_get(self, fields_list):
        res = super(ResPartnerFile, self).default_get(fields_list)
        if self._context and self._context.get('partner_id'):
            partner = self.env['res.partner'].browse(self._context['partner_id'])
            if partner and len(partner.x_code):
                relative_path = self.env['ir.config_parameter'].sudo().get_param('partner_file.dir_location')
                relative_path = join(relative_path or '', partner.x_code or '')
                absolute_path = os.getcwd() + relative_path
                files = None
                try:
                    files = [join(relative_path, f) for f in listdir(absolute_path) if isfile(join(absolute_path, f))]
                except:
                    pass
                if isinstance(files, list) and len(files) > 0:
                    res['images'] = json.dumps(files)
                else:
                    raise MissingError("Không tìm thấy hồ sơ cũ của khách hàng này.")
        return res

    partner_id = fields.Many2one('res.partner', 'Khách hàng', readonly=1)
    name = fields.Char('Tên khách hàng', related='partner_id.name', readonly=1)
    images = fields.Char('Ảnh hồ sơ')
