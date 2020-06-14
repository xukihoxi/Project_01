# -*- coding: utf-8 -*-
from odoo import http

# class PosSecurity(http.Controller):
#     @http.route('/pos_security/pos_security/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/pos_security/pos_security/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('pos_security.listing', {
#             'root': '/pos_security/pos_security',
#             'objects': http.request.env['pos_security.pos_security'].search([]),
#         })

#     @http.route('/pos_security/pos_security/objects/<model("pos_security.pos_security"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('pos_security.object', {
#             'object': obj
#         })