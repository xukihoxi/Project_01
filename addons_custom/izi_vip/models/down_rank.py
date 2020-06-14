# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import except_orm, ValidationError
from datetime import datetime, timedelta, date
import logging

_logger = logging.getLogger(__name__)


class DownRank(models.Model):
    _inherit = 'crm.vip.customer'

    # TODO : Tiendz
    # cấu hình xuống hạng 1 bậc = 100% số tiền quy đinh
    # cấu hình xuống hạng 2 bậc = 50% số tiền quy đinh
    # ví dụ: cần 60tr để duy trì hạng vàng, cấu hình xuống hạng bạc là 60tr, xuống thành viên là 30tr

    def set_down_rank(self):
        rank_tv = self.env.ref('izi_vip.vip_rank_base')
        partner_ids = self.env['res.partner'].search([('x_rank','!=',rank_tv.id),('x_rank','!=',False)])
        for partner_id in partner_ids:
            # lấy tổng doanh thu 1 năm
            revenue = partner_id.get_ayear_revenue_from_now()
            rule_id = self.env['crm.vip.rank.rule'].search([('current_rank_id', '=', partner_id.x_rank.id)])
            if not rule_id:
                raise ValidationError("Rule for selected rank is not defined!")
            # kiểm tra xuống bao nhiêu bậc hạng
            check_rank = False
            for line in rule_id.line_ids:
                if line.type == 'down':
                    if revenue < line.revenue:
                        check_rank = line.id
            if check_rank != False:
                for line in rule_id.line_ids:
                    if line.id == check_rank:
                        # kiểm tra đơn quản lý KH vip
                        vip_id = self.env['crm.vip.customer'].search([('partner_id', '=', partner_id.id)], limit=1)
                        if vip_id.id == False:
                            vip_id = self.env['crm.vip.customer'].create({
                                'partner_id': partner_id.id,
                            })
                        # tạo lịch sử xuống hạng
                        self.env['crm.vip.customer.history'].create({
                            'partner_id': partner_id.id,
                            'rank_current': partner_id.x_rank.id,
                            'rank_request': line.rank_id.id,
                            'state': 'approved',
                            'approved_date': fields.Date.today(),
                            'vip_custom_id': vip_id.id,
                            'type': 'down',
                        })
                        partner_id.x_rank = line.rank_id.id
