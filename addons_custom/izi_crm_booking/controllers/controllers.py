# -*- coding: utf-8 -*-
from odoo import http

# class IziBooking(http.Controller):
#     @http.route('/izi_crm_booking/izi_crm_booking/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/izi_crm_booking/izi_crm_booking/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('izi_crm_booking.listing', {
#             'root': '/izi_crm_booking/izi_crm_booking',
#             'objects': http.request.env['izi_crm_booking.izi_crm_booking'].search([]),
#         })

#     @http.route('/izi_crm_booking/izi_crm_booking/objects/<model("izi_crm_booking.izi_crm_booking"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('izi_crm_booking.object', {
#             'object': obj
#         })