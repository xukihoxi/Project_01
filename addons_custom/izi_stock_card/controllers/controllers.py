# -*- coding: utf-8 -*-
from odoo import http

# class IziStockCard(http.Controller):
#     @http.route('/izi_stock_card/izi_stock_card/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/izi_stock_card/izi_stock_card/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('izi_stock_card.listing', {
#             'root': '/izi_stock_card/izi_stock_card',
#             'objects': http.request.env['izi_stock_card.izi_stock_card'].search([]),
#         })

#     @http.route('/izi_stock_card/izi_stock_card/objects/<model("izi_stock_card.izi_stock_card"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('izi_stock_card.object', {
#             'object': obj
#         })