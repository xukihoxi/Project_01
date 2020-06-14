# -*- coding: utf-8 -*-
from odoo import http

# class CrmReportBirt(http.Controller):
#     @http.route('/crm_report_birt/crm_report_birt/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/crm_report_birt/crm_report_birt/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('crm_report_birt.listing', {
#             'root': '/crm_report_birt/crm_report_birt',
#             'objects': http.request.env['crm_report_birt.crm_report_birt'].search([]),
#         })

#     @http.route('/crm_report_birt/crm_report_birt/objects/<model("crm_report_birt.crm_report_birt"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('crm_report_birt.object', {
#             'object': obj
#         })