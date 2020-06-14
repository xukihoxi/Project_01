# -*- coding: utf-8 -*-
from odoo import http

# class IziPosRefundInvoiceMakePaymnet(http.Controller):
#     @http.route('/izi_pos_refund_invoice_make_paymnet/izi_pos_refund_invoice_make_paymnet/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/izi_pos_refund_invoice_make_paymnet/izi_pos_refund_invoice_make_paymnet/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('izi_pos_refund_invoice_make_paymnet.listing', {
#             'root': '/izi_pos_refund_invoice_make_paymnet/izi_pos_refund_invoice_make_paymnet',
#             'objects': http.request.env['izi_pos_refund_invoice_make_paymnet.izi_pos_refund_invoice_make_paymnet'].search([]),
#         })

#     @http.route('/izi_pos_refund_invoice_make_paymnet/izi_pos_refund_invoice_make_paymnet/objects/<model("izi_pos_refund_invoice_make_paymnet.izi_pos_refund_invoice_make_paymnet"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('izi_pos_refund_invoice_make_paymnet.object', {
#             'object': obj
#         })