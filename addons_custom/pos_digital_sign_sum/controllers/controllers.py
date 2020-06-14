# -*- coding: utf-8 -*-
from odoo import http

# class PosDigitalSignSum(http.Controller):
#     @http.route('/pos_digital_sign_sum/pos_digital_sign_sum/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/pos_digital_sign_sum/pos_digital_sign_sum/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('pos_digital_sign_sum.listing', {
#             'root': '/pos_digital_sign_sum/pos_digital_sign_sum',
#             'objects': http.request.env['pos_digital_sign_sum.pos_digital_sign_sum'].search([]),
#         })

#     @http.route('/pos_digital_sign_sum/pos_digital_sign_sum/objects/<model("pos_digital_sign_sum.pos_digital_sign_sum"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('pos_digital_sign_sum.object', {
#             'object': obj
#         })