# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import ValidationError, MissingError
from datetime import date
from dateutil.relativedelta import relativedelta
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT


class UpRankWizard(models.TransientModel):
    _name = 'crm.vip.customer.uprank'

    partner_id = fields.Many2one('res.partner', string=u'Khách hàng', readonly=True)
    name = fields.Char(string='Name', related='partner_id.name')

    rank_current = fields.Many2one(string=u'Hạng hiện tại', related='partner_id.x_rank', readonly=True)
    rank_request = fields.Many2one('crm.vip.rank', string=u'Hạng yêu cầu', required=True)
    # register_date = fields.Date(string=u'Ngày yêu cầu', required=True, default=date.today())
    month_rank = fields.Integer(string=u'Số tháng')
    note = fields.Text(string=u'Ghi chú')
    is_exception = fields.Boolean(string='Ngoại lệ', default=False)
    type = fields.Selection([('accumulate', 'Accumulation'), ('suddenly', 'Suddenly'), ('except', 'Exception')], 'Request type')

    @api.onchange('rank_request')
    def onchange_request_rank(self):
        if self.rank_request:
            rule_id = self.env['crm.vip.rank.rule'].search([('current_rank_id', '=', self.partner_id.x_rank.id)])
            if not rule_id:
                raise ValidationError("Rule for selected rank is not defined!")
            self.is_exception = True
            self.type = 'except'
            self.month_rank = self.rank_request.active_month
            # Lấy số doanh thu yêu cầu cho trường hợp phát sinh đột biến
            suddenly_rank = {}
            normally_rank = None
            for line in rule_id.line_ids:
                if line.type == 'suddenly' and line.rank_id.id == self.rank_request.id:
                    suddenly_rank[line.rank_id.id] = line
                elif line.type == 'up' and line.rank_id.id == self.rank_request.id:
                    normally_rank = line
            # Nếu hạng yêu cầu có quy định cho trường hợp phát sinh đột biến
            if len(suddenly_rank) and self.rank_request.id in suddenly_rank:
                # Kiểm tra nếu có doanh thu đột biến
                if self.partner_id.check_suddenly_revenue(suddenly_rank[self.rank_request.id].revenue):
                    self.is_exception = False
                    self.type = 'suddenly'
            # Nếu hạng yêu cầu có quy định cho lên hạng bình thường
            if normally_rank:
                # Lấy doanh thu tích luỹ trong 1 năm
                ayear_revenue = self.partner_id.get_ayear_revenue_from_now()
                # Nếu tổng doanh thu đáp ứng yêu cầu lên hạng bình thường (1 lần duyệt)
                if ayear_revenue >= normally_rank.revenue:
                    self.is_exception = False
                    self.type = 'accumulate'
            # else:
            #     raise MissingError("There is no defined rule for requested rank from customer's rank!")

    @api.model
    def default_get(self, fields):
        res = super(UpRankWizard, self).default_get(fields)
        vip_id = self._context.get('active_id')
        vip_record = self.env['crm.vip.customer'].browse(vip_id)
        res['partner_id'] = vip_record.partner_id.id
        return res

    @api.multi
    def action_uprank_request(self):
        self.ensure_one()
        # Kiểm tra nếu KH đã có bản ghi yêu cầu lên hạng đang chờ duyệt
        existed_req = self.env['crm.vip.customer.confirm'].search_count([('partner_id', '=', self.partner_id.id), ('state', 'in', ['new', 'confirm'])])
        if existed_req > 0:
            raise ValidationError("Khách hàng này đã có yêu cầu đang chờ duyệt, không thể tạo thêm yêu cầu!")
        # Tạo bản ghi yêu cầu xác nhận - chờ duyệt
        type = 'except'
        if self.rank_request:
            rule_id = self.env['crm.vip.rank.rule'].search([('current_rank_id', '=', self.partner_id.x_rank.id)])
            if not rule_id:
                raise ValidationError("Rule for selected rank is not defined!")
            self.is_exception = True
            self.type = 'except'
            self.month_rank = self.rank_request.active_month
            # Lấy số doanh thu yêu cầu cho trường hợp phát sinh đột biến
            suddenly_rank = {}
            normally_rank = None
            for line in rule_id.line_ids:
                if line.type == 'suddenly' and line.rank_id.id == self.rank_request.id:
                    suddenly_rank[line.rank_id.id] = line
                elif line.type == 'up' and line.rank_id.id == self.rank_request.id:
                    normally_rank = line
            # Nếu hạng yêu cầu có quy định cho trường hợp phát sinh đột biến
            if len(suddenly_rank) and self.rank_request.id in suddenly_rank:
                # Kiểm tra nếu có doanh thu đột biến
                if self.partner_id.check_suddenly_revenue(suddenly_rank[self.rank_request.id].revenue):
                    type = 'manual'
            # Nếu hạng yêu cầu có quy định cho lên hạng bình thường
            if normally_rank:
                # Lấy doanh thu tích luỹ trong 1 năm
                ayear_revenue = self.partner_id.get_ayear_revenue_from_now()
                # Nếu tổng doanh thu đáp ứng yêu cầu lên hạng bình thường (1 lần duyệt)
                if ayear_revenue >= normally_rank.revenue:
                    type = 'manual'
            # else:
            #     raise MissingError("There is no defined rule for requested rank from customer's rank!")
        self.env['crm.vip.customer.confirm'].create({
            'partner_id': self.partner_id.id,
            'month_rank': self.month_rank,
            'rank_request': self.rank_request.id,
            'rank_current': self.partner_id.x_rank.id or False,
            'note': self.note,
            'type': type,
            'state': 'new'
        })
        # Tạo bản ghi lịch sử lên hạng - chờ duyệt
        vip_record_id = self.env['crm.vip.customer'].search_read([('partner_id', '=', self.partner_id.id)], limit=1)
        self.env['crm.vip.customer.history'].create({
            'partner_id': self.partner_id.id,
            'rank_current': self.partner_id.x_rank.id,
            'rank_request': self.rank_request.id,
            'vip_custom_id': int(vip_record_id[0]['id']),
            'state': 'pending',
        })
