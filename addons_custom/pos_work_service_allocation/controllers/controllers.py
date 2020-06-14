# -*- coding: utf-8 -*-
from odoo import http

# class PosWorkServiceAllocation(http.Controller):
#     @http.route('/pos_work_service_allocation/pos_work_service_allocation/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/pos_work_service_allocation/pos_work_service_allocation/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('pos_work_service_allocation.listing', {
#             'root': '/pos_work_service_allocation/pos_work_service_allocation',
#             'objects': http.request.env['pos_work_service_allocation.pos_work_service_allocation'].search([]),
#         })

#     @http.route('/pos_work_service_allocation/pos_work_service_allocation/objects/<model("pos_work_service_allocation.pos_work_service_allocation"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('pos_work_service_allocation.object', {
#             'object': obj
#         })