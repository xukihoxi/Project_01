# -*- coding: utf-8 -*-
from odoo import http

# class IziPosChangePayment(http.Controller):
#     @http.route('/izi_pos_change_payment/izi_pos_change_payment/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/izi_pos_change_payment/izi_pos_change_payment/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('izi_pos_change_payment.listing', {
#             'root': '/izi_pos_change_payment/izi_pos_change_payment',
#             'objects': http.request.env['izi_pos_change_payment.izi_pos_change_payment'].search([]),
#         })

#     @http.route('/izi_pos_change_payment/izi_pos_change_payment/objects/<model("izi_pos_change_payment.izi_pos_change_payment"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('izi_pos_change_payment.object', {
#             'object': obj
#         })