# -*- coding: utf-8 -*-
from odoo import http

# class RptRevenue(http.Controller):
#     @http.route('/rpt_revenue/rpt_revenue/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/rpt_revenue/rpt_revenue/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('rpt_revenue.listing', {
#             'root': '/rpt_revenue/rpt_revenue',
#             'objects': http.request.env['rpt_revenue.rpt_revenue'].search([]),
#         })

#     @http.route('/rpt_revenue/rpt_revenue/objects/<model("rpt_revenue.rpt_revenue"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('rpt_revenue.object', {
#             'object': obj
#         })