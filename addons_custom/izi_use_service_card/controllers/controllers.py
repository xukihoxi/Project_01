# -*- coding: utf-8 -*-
from odoo import http

# class IziUseServiceCard(http.Controller):
#     @http.route('/izi_use_service_card/izi_use_service_card/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/izi_use_service_card/izi_use_service_card/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('izi_use_service_card.listing', {
#             'root': '/izi_use_service_card/izi_use_service_card',
#             'objects': http.request.env['izi_use_service_card.izi_use_service_card'].search([]),
#         })

#     @http.route('/izi_use_service_card/izi_use_service_card/objects/<model("izi_use_service_card.izi_use_service_card"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('izi_use_service_card.object', {
#             'object': obj
#         })