# -*- coding: utf-8 -*-
from odoo import http

# class IziPosMoney(http.Controller):
#     @http.route('/izi_pos_money/izi_pos_money/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/izi_pos_money/izi_pos_money/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('izi_pos_money.listing', {
#             'root': '/izi_pos_money/izi_pos_money',
#             'objects': http.request.env['izi_pos_money.izi_pos_money'].search([]),
#         })

#     @http.route('/izi_pos_money/izi_pos_money/objects/<model("izi_pos_money.izi_pos_money"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('izi_pos_money.object', {
#             'object': obj
#         })