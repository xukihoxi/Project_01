# -*- coding: utf-8 -*-
from odoo import http

# class StockReportBirt(http.Controller):
#     @http.route('/stock_report_birt/stock_report_birt/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/stock_report_birt/stock_report_birt/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('stock_report_birt.listing', {
#             'root': '/stock_report_birt/stock_report_birt',
#             'objects': http.request.env['stock_report_birt.stock_report_birt'].search([]),
#         })

#     @http.route('/stock_report_birt/stock_report_birt/objects/<model("stock_report_birt.stock_report_birt"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('stock_report_birt.object', {
#             'object': obj
#         })