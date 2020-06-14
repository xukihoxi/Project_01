# -*- coding: utf-8 -*-
from odoo import http

# class StockSecurity(http.Controller):
#     @http.route('/stock_security/stock_security/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/stock_security/stock_security/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('stock_security.listing', {
#             'root': '/stock_security/stock_security',
#             'objects': http.request.env['stock_security.stock_security'].search([]),
#         })

#     @http.route('/stock_security/stock_security/objects/<model("stock_security.stock_security"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('stock_security.object', {
#             'object': obj
#         })