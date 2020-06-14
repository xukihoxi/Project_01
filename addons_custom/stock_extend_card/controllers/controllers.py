# -*- coding: utf-8 -*-
from odoo import http

# class StockExtendCard(http.Controller):
#     @http.route('/stock_extend_card/stock_extend_card/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/stock_extend_card/stock_extend_card/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('stock_extend_card.listing', {
#             'root': '/stock_extend_card/stock_extend_card',
#             'objects': http.request.env['stock_extend_card.stock_extend_card'].search([]),
#         })

#     @http.route('/stock_extend_card/stock_extend_card/objects/<model("stock_extend_card.stock_extend_card"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('stock_extend_card.object', {
#             'object': obj
#         })