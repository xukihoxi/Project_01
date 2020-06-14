# -*- coding: utf-8 -*-

from odoo import models, api

class PosServiceBed(models.Model):
    _inherit = 'pos.service.bed'

    @api.one
    def write(self, vals):
        self.env['bus.bus'].sendone(self.env.cr.dbname+'izi.view_synchronize',  {'model': self.room_id._name, 'id': self.room_id.id, 'type':'list,kanban,form'})
        return super(PosServiceBed, self).write(vals)

# class PosUserMaterial(models.Model):
#     _inherit = 'pos.user.material'
#
#     @api.one
#     def write(self, vals):
#         self.env['bus.bus'].sendone(self.env.cr.dbname + 'izi.view_synchronize',
#                                     {'model': self._name, 'id': self.id, 'type': 'list,kanban,form'})
#         return super(PosUserMaterial, self).write(vals)
#
#     @api.one
#     def create(self, vals):
#         self.env['bus.bus'].sendone(self.env.cr.dbname + 'izi.view_synchronize',
#                                     {'model': self._name, 'id': self.id, 'type': 'list,kanban,form'})
#         return super(PosUserMaterial, self).create(vals)
#
# class PosOrder(models.Model):
#     _inherit = 'pos.order'
#
#     @api.multi
#     def write(self, vals):
#         self.env['bus.bus'].sendone(self.env.cr.dbname + 'izi.view_synchronize',
#                                     {'model': self._name,'id': self.id, 'type': 'list,form'})
#         return super(PosOrder, self).write(vals)
#
# class CrmLead(models.Model):
#     _inherit = 'crm.lead'
#
#     @api.one
#     def write(self, vals):
#         self.env['bus.bus'].sendone(self.env.cr.dbname + 'izi.view_synchronize',
#                                     {'model': self._name,'id': self.id, 'type': 'list,kanban,form'})
#         return super(CrmLead, self).write(vals)
#
# class DestroyService(models.Model):
#     _inherit = 'pos.destroy.service'
#
#     @api.one
#     def write(self, vals):
#         self.env['bus.bus'].sendone(self.env.cr.dbname + 'izi.view_synchronize',
#                                     {'model': self._name,'id': self.id, 'type': 'list,kanban,form'})
#         return super(DestroyService, self).write(vals)
#
# class ExchangService(models.Model):
#     _inherit = 'izi.pos.exchange.service'
#
#     @api.one
#     def write(self, vals):
#         self.env['bus.bus'].sendone(self.env.cr.dbname + 'izi.view_synchronize',
#                                     {'model': self._name,'id': self.id, 'type': 'list,kanban,form'})
#         return super(ExchangService, self).write(vals)