# -*- coding: utf-8 -*-
from odoo import http

# class PosPaymentMultiCurrency(http.Controller):
#     @http.route('/pos_payment_multi_currency/pos_payment_multi_currency/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/pos_payment_multi_currency/pos_payment_multi_currency/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('pos_payment_multi_currency.listing', {
#             'root': '/pos_payment_multi_currency/pos_payment_multi_currency',
#             'objects': http.request.env['pos_payment_multi_currency.pos_payment_multi_currency'].search([]),
#         })

#     @http.route('/pos_payment_multi_currency/pos_payment_multi_currency/objects/<model("pos_payment_multi_currency.pos_payment_multi_currency"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('pos_payment_multi_currency.object', {
#             'object': obj
#         })