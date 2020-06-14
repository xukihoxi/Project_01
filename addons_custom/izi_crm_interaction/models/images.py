# -*- coding: utf-8 -*-

from odoo import models, fields, api, tools, _


class Image(models.Model):
    _name = "partner.interaction.images"

    name = fields.Char(string="Note")
    # image = fields.Binary('Image', attachment=True)
    partner_interaction_id = fields.Many2one('partner.interaction')

    image = fields.Binary(
        "Image", attachment=True)
    image_small = fields.Binary(
        "Small-sized image", compute='_compute_images')

    @api.one
    @api.depends('image')
    def _compute_images(self):
        if self._context.get('bin_size'):
            self.image_small = self.image
        else:
            resized_images = tools.image_get_resized_images(self.image, return_big=True, avoid_resize_medium=True)
            self.image_small = resized_images['image_small']