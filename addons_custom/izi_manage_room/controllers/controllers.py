# -*- coding: utf-8 -*-
from odoo import http

# class IziManageRoom(http.Controller):
#     @http.route('/izi_manage_room/izi_manage_room/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/izi_manage_room/izi_manage_room/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('izi_manage_room.listing', {
#             'root': '/izi_manage_room/izi_manage_room',
#             'objects': http.request.env['izi_manage_room.izi_manage_room'].search([]),
#         })

#     @http.route('/izi_manage_room/izi_manage_room/objects/<model("izi_manage_room.izi_manage_room"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('izi_manage_room.object', {
#             'object': obj
#         })