# -*- coding: utf-8 -*-
from odoo import http

# class IziCrmInteraction(http.Controller):
#     @http.route('/izi_crm_interaction/izi_crm_interaction/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/izi_crm_interaction/izi_crm_interaction/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('izi_crm_interaction.listing', {
#             'root': '/izi_crm_interaction/izi_crm_interaction',
#             'objects': http.request.env['izi_crm_interaction.izi_crm_interaction'].search([]),
#         })

#     @http.route('/izi_crm_interaction/izi_crm_interaction/objects/<model("izi_crm_interaction.izi_crm_interaction"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('izi_crm_interaction.object', {
#             'object': obj
#         })