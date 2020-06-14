# -*- coding: utf-8 -*-
from odoo import http

# class IziPosCustomBackend(http.Controller):
#     @http.route('/izi_pos_custom_backend/izi_pos_custom_backend/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/izi_pos_custom_backend/izi_pos_custom_backend/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('izi_pos_custom_backend.listing', {
#             'root': '/izi_pos_custom_backend/izi_pos_custom_backend',
#             'objects': http.request.env['izi_pos_custom_backend.izi_pos_custom_backend'].search([]),
#         })

#     @http.route('/izi_pos_custom_backend/izi_pos_custom_backend/objects/<model("izi_pos_custom_backend.izi_pos_custom_backend"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('izi_pos_custom_backend.object', {
#             'object': obj
#         })