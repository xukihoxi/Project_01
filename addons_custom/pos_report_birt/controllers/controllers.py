# -*- coding: utf-8 -*-
from odoo import http

# class PosReportBirt(http.Controller):
#     @http.route('/pos_report_birt/pos_report_birt/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/pos_report_birt/pos_report_birt/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('pos_report_birt.listing', {
#             'root': '/pos_report_birt/pos_report_birt',
#             'objects': http.request.env['pos_report_birt.pos_report_birt'].search([]),
#         })

#     @http.route('/pos_report_birt/pos_report_birt/objects/<model("pos_report_birt.pos_report_birt"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('pos_report_birt.object', {
#             'object': obj
#         })