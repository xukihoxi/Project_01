# -*- coding: utf-8 -*-

from odoo import models, fields, api
from datetime import datetime, date


class VipCustomerConfirm(models.Model):
    _inherit = 'crm.vip.customer.confirm'

    def uprank(self):
        current_rank_id = self.partner_id.x_rank.id
        super(VipCustomerConfirm, self).uprank()
        new_rank_id = self.partner_id.x_rank.id
        up_rule = self.env['crm.vip.rank.rule'].search([('current_rank_id', '=', current_rank_id), ('active', '=', True)], limit=1)
        if up_rule:
            rule_line = up_rule.line_ids.filtered(lambda r: r.rank_id.id == new_rank_id)
            if rule_line and len(rule_line) == 1:
                reward_points = rule_line.reward_points
                if reward_points > 0:
                    self.env['izi.vip.point.history'].create({
                        'partner_id': self.partner_id.id,
                        'date': datetime.now(),
                        'point': reward_points
                    })
