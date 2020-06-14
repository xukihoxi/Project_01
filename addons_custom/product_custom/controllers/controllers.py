# -*- coding: utf-8 -*-
from odoo import http

# class ProductCustom(http.Controller):
#     @http.route('/product_custom/product_custom/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/product_custom/product_custom/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('product_custom.listing', {
#             'root': '/product_custom/product_custom',
#             'objects': http.request.env['product_custom.product_custom'].search([]),
#         })

#     @http.route('/product_custom/product_custom/objects/<model("product_custom.product_custom"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('product_custom.object', {
#             'object': obj
#         })