# -*- coding: utf-8 -*-

from odoo import models, fields, api, tools, _
from odoo.tools import float_compare, pycompat
from datetime import datetime
from odoo.exceptions import except_orm, ValidationError


class Image(models.Model):
    _name = "izi.images"

    name = fields.Char()
    old_service_card_id = fields.Many2one('izi.service.card.using')
    new_service_card_id = fields.Many2one('izi.service.card.using')
    note = fields.Text(string="Note")

    image_customer = fields.Binary(
        "Customer Image", attachment=True)
    image_small = fields.Binary(
        "Small-sized image", compute='_compute_images')

    @api.one
    @api.depends('image_customer')
    def _compute_images(self):
        if self._context.get('bin_size'):
            self.image_small = self.image_customer
        else:
            resized_images = tools.image_get_resized_images(self.image_customer, return_big=True, avoid_resize_medium=True)
            self.image_small = resized_images['image_small']