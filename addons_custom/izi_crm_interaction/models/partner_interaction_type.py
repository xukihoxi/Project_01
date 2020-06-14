# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import ValidationError


class PartnerInteractionType(models.Model):
    _name = 'partner.interaction.type'

    name = fields.Char(string="Name")
    survey_id = fields.Many2one('survey.survey', string="Survey")
    # default = fields.Boolean(string="Default")
    #
    # @api.constrains('default')
    # def _check_default(self):
    #     if self.default:
    #         interaction_type = self.search([('default', '=', True)])
    #         if interaction_type:
    #             raise ValidationError('Đã có trạng thái %s được sử dụng mặc định không thể tạo thêm trạng thái là mặc định!' % (str(interaction_type.name)))