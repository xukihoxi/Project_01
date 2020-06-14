# -*- coding: utf-8 -*-
from odoo import http

# class PosDestroyService(http.Controller):
#     @http.route('/pos_destroy_service/pos_destroy_service/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/pos_destroy_service/pos_destroy_service/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('pos_destroy_service.listing', {
#             'root': '/pos_destroy_service/pos_destroy_service',
#             'objects': http.request.env['pos_destroy_service.pos_destroy_service'].search([]),
#         })

#     @http.route('/pos_destroy_service/pos_destroy_service/objects/<model("pos_destroy_service.pos_destroy_service"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('pos_destroy_service.object', {
#             'object': obj
#         })