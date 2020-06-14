# -*- coding: utf-8 -*-
from odoo import http

# class IziScanBarcode(http.Controller):
#     @http.route('/izi_scan_barcode/izi_scan_barcode/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/izi_scan_barcode/izi_scan_barcode/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('izi_scan_barcode.listing', {
#             'root': '/izi_scan_barcode/izi_scan_barcode',
#             'objects': http.request.env['izi_scan_barcode.izi_scan_barcode'].search([]),
#         })

#     @http.route('/izi_scan_barcode/izi_scan_barcode/objects/<model("izi_scan_barcode.izi_scan_barcode"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('izi_scan_barcode.object', {
#             'object': obj
#         })