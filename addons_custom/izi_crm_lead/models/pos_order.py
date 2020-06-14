# -*- coding: utf-8 -*-

from odoo import fields, models,api


class PosOrder(models.Model):
    _inherit = "pos.order"

    x_opportunity_id = fields.Many2one('crm.lead', string='Opportunity', domain="[('type', '=', 'opportunity')]")

    @api.multi
    def action_order_complete(self):
        res = super(PosOrder, self).action_order_complete()
        if self.x_opportunity_id:
            self.x_opportunity_id.action_set_won()
        return res



class UseService(models.Model):
    _inherit = 'izi.service.card.using'

    x_opportunity_id = fields.Many2one('crm.lead', string='Opportunity', domain="[('type', '=', 'opportunity')]")

    @api.multi
    def action_confirm(self):
        sc = super(UseService, self).action_confirm()
        if self.x_opportunity_id:
            self.x_opportunity_id.action_set_won()
        return sc

    @api.multi
    def action_done(self):
        sc = super(UseService, self).action_done()
        if self.x_opportunity_id:
            if self.type == 'service':
                self.pos_order_id.x_opportunity_id = self.x_opportunity_id.id
        return sc


class PosDeposit(models.Model):
    _inherit = 'pos.customer.deposit.line'

    x_opportunity_id = fields.Many2one('crm.lead', string='Opportunity')

    @api.multi
    def action_done(self):
        res = super(PosDeposit, self).action_done()
        if self.x_opportunity_id:
            self.x_opportunity_id.action_set_won()
        return res
