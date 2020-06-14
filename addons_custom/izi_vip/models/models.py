# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import AccessDenied, MissingError
from datetime import date, datetime
from dateutil.relativedelta import relativedelta
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT
from odoo.exceptions import except_orm

import logging
logger = logging.getLogger(__name__)


class ResPartnerRevenue(models.Model):
    _name = 'crm.vip.customer.revenue'
    _order = 'create_date desc'
    _description = u'Doanh thu'

    partner_id = fields.Many2one('res.partner', u'Khách hàng')
    order_id = fields.Many2one('pos.order', string='Pos Order')
    journal_id = fields.Many2one('account.journal', string="Journal")
    amount = fields.Float(u'Doanh thu')
    date = fields.Date(u'Ngày ghi nhận')


class ResPartner(models.Model):
    _inherit = 'res.partner'

    x_rank = fields.Many2one('crm.vip.rank', string=u'Hạng VIP')
    x_revenue_ids = fields.One2many('crm.vip.customer.revenue', 'partner_id', u'Doanh thu')


    def check_suddenly_revenue(self, requested_revenue):
        ayear_ago = (date.today() - relativedelta(years=1, days=1)).strftime(DEFAULT_SERVER_DATE_FORMAT)
        sql = "select amount from crm_vip_customer_revenue where partner_id=%s and amount >= %s and date > %s limit 1"
        self.env.cr.execute(sql, (self.id, requested_revenue, ayear_ago))
        matched = self.env.cr.dictfetchone()
        if matched:
            return True
        return False

    def get_ayear_revenue_from_now(self):
        ayear_ago = (date.today() - relativedelta(years=1, days=1)).strftime(DEFAULT_SERVER_DATE_FORMAT)
        # Truy vấn tổng doanh thu từ lần cuối lên hạng hoặc trong 1 năm
        sql = 'SELECT SUM(amount) AS total ' \
              'FROM crm_vip_customer_revenue ' \
              'WHERE partner_id=%s AND date > %s' \
              'GROUP BY partner_id'
        self.env.cr.execute(sql, (self.id, ayear_ago))
        revenue = self.env.cr.dictfetchone()
        return int(revenue['total']) if revenue else 0

class ExceptDiscountProduct(models.Model):
    _name = 'crm.vip.product.except'
    _description = u'Vip product except'

    product_id = fields.Many2one('product.product', 'Product')
    max_amount = fields.Integer('Maximum amount', help="Maximum amount to discount, left 0 to discount all")
    discount = fields.Float('Discount (%)')
    rank_id = fields.Many2one('crm.vip.rank', 'Rank ID')

    _sql_constraints = [
        ('product_rank_uniq', 'unique(product_id, rank_id)', u'Products list except contains duplicate!')
    ]


class VipRank(models.Model):
    _name = 'crm.vip.rank'
    _description = u'Hạng VIP'
    _order = 'level asc'

    code = fields.Char(string=u"Mã", help=u'Mã hạng VIP', required=True)
    name = fields.Char(string=u"Tên", help=u'Tên hạng VIP', required=True)
    descx = fields.Char(string=u"Mô tả", required=True)
    active = fields.Boolean(string=u"Kích hoạt?", default=True)
    level = fields.Integer(string=u'Cấp độ')
    active_month = fields.Integer(string=u'Tháng kích hoạt', help=u"Số tháng kích hoạt VIP")
    image = fields.Binary(string=u'Ảnh đại diện')
    policy = fields.Html(string=u'Chính sách')
    discount_service = fields.Float(u'Giảm giá dịch vụ (%)', help=u"Giảm giá tính trên dịch vụ mà KH mua (đơn vị %)")
    discount_product = fields.Float(u'Giảm giá sản phẩm (%)', help=u"Giảm giá tính trên sản phẩm mà KH mua (đơn vị %)")
    except_product_ids = fields.One2many('crm.vip.product.except', 'rank_id', 'Except products')

    @api.model
    def name_search(self, name='', args=None, operator='ilike', limit=100):
        args = args or []
        partner_id = self._context.get('partner_id', None)
        if self._context.get('get_allow_ranks', False) and partner_id:
            # Chỉ tìm các hạng có level nhỏ hơn hạng hiện tại của khách hàng
            partner = self.env['res.partner'].browse(partner_id)
            level = 100
            try: level = partner.x_rank.level
            except: pass
            recs = self.search(['&', ('level', '<', level), ('name', operator, name)] + args, limit=limit)
        else:
            recs = self.search([('name', operator, name)] + args, limit=limit)
        return recs.name_get()


class VipRankRuleLine(models.Model):
    _name = 'crm.vip.rank.rule.line'
    _description = u'Up/down rank rules line'
    _order = 'rank_level asc, revenue desc'

    rank_id = fields.Many2one('crm.vip.rank', 'Rank')
    rank_level = fields.Integer(related='rank_id.level', string='Rank level', store=True)
    revenue = fields.Float("Revenue")
    reward_points = fields.Float('Reward points')
    type = fields.Selection([('up', 'Rank up'), ('down', 'Rank down'), ('keep', 'Rank keep'), ('suddenly', 'Suddenly')], 'Rule type')
    rule_id = fields.Many2one('crm.vip.rank.rule', 'Rule')

    _sql_constraints = [
        ('rule_id_rank_id_type_uniq', 'unique(rule_id, rank_id, type)',
         u'Rank rule lists contains some duplicate rank items with the same type!')
    ]


class VipRankRule(models.Model):
    _name = 'crm.vip.rank.rule'
    _description = u'Up/down rank rules'

    name = fields.Char("Name")
    current_rank_id = fields.Many2one('crm.vip.rank', 'Current rank')
    active = fields.Boolean("Active", default=True)
    line_ids = fields.One2many('crm.vip.rank.rule.line', 'rule_id', 'Target ranks')
    note = fields.Text("Description")

    _sql_constraints = [
        ('current_rank_id_uniq', 'unique(current_rank_id)',
         u'Rule for selected current rank already existed!')
    ]


class VipCustomer(models.Model):
    _name = 'crm.vip.customer'
    _description = u'KH VIP'

    partner_id = fields.Many2one('res.partner', string=u'Khách hàng', domain=([('customer', '=', True)]), required=True)
    name = fields.Char(string=u'Tên', related='partner_id.name')
    partner_code = fields.Char(string=u'Mã KH', related='partner_id.x_code')
    image = fields.Binary(string=u"Ảnh đại diện", related='partner_id.image_small')
    phone = fields.Char(string=u'Điện thoại', related='partner_id.phone', readonly=True)
    email = fields.Char(string='Email', related='partner_id.email', readonly=True)
    birthday = fields.Date(string=u'Sinh nhật', related='partner_id.x_birthday', readonly=True)
    address = fields.Char(string=u'Địa chỉ', related='partner_id.street', readonly=True)
    vip_rank = fields.Many2one('crm.vip.rank', string=u'Hạng VIP', related='partner_id.x_rank', readonly=True)
    user_id = fields.Many2one(string=u'Nhân viên chăm sóc', related='partner_id.user_id', readonly=True)
    revenue_ids = fields.One2many(string=u'Doanh thu', related='partner_id.x_revenue_ids', readonly=True)
    uprank_date = fields.Date(string=u'Ngày lên hạng')
    uprank_expire_date = fields.Date(string=u'Ngày xuống hạng')
    vip_history_ids = fields.One2many('crm.vip.customer.history', 'vip_custom_id', u'Lịch sử hạng')

    _sql_constraints = [
        ('partner_id_unique', 'unique(partner_id)', u'Khách hàng này đã tồn tại lịch sử lên hạng !')
    ]

    @api.model
    def schedule_update_rank(self):
        this_month = date.today() + relativedelta(months=1, days=-date.today().day)
        # Ngày cuối cùng của tháng
        # if this_month.day != date.today().day:
        #     return True
        # Các quy tắc lên/xuống hạng thẻ
        rank_rules = self.env['crm.vip.rank.rule'].search([('active', '=', True)])
        rank_rules_dict = {}
        for rule in rank_rules:
            rank_rules_dict[rule.current_rank_id.id] = True
            suddenly = '%s_suddenly' % rule.current_rank_id.id
            up = '%s_up' % rule.current_rank_id.id
            down = '%s_down' % rule.current_rank_id.id
            keep = '%s_keep' % rule.current_rank_id.id
            rank_rules_dict[suddenly] = {}
            rank_rules_dict[up] = {}
            rank_rules_dict[down] = {}
            rank_rules_dict[keep] = {}
            for line in rule.line_ids:
                if line.type == 'suddenly':
                    rank_rules_dict[suddenly][line.id] = {'rank_id': line.rank_id.id, 'active_month': line.rank_id.active_month, 'rank_level': line.rank_level, 'revenue': line.revenue}
                elif line.type == 'up':
                    rank_rules_dict[up][line.id] = {'rank_id': line.rank_id.id, 'rank_level': line.rank_level, 'revenue': line.revenue}
                elif line.type == 'down':
                    rank_rules_dict[down][line.id] = {'rank_id': line.rank_id.id, 'rank_level': line.rank_level, 'revenue': line.revenue}
                elif line.type == 'keep':
                    rank_rules_dict[keep][line.id] = {'rank_id': line.rank_id.id, 'rank_level': line.rank_level, 'revenue': line.revenue}
            rank_rules_dict[suddenly] = sorted(rank_rules_dict[suddenly].items(), key=lambda x:x[1]['revenue'], reverse=True)
            rank_rules_dict[up] = sorted(rank_rules_dict[up].items(), key=lambda x:x[1]['revenue'], reverse=True)
            rank_rules_dict[down] = sorted(rank_rules_dict[down].items(), key=lambda x:x[1]['revenue'], reverse=False)
            if len(rank_rules_dict[keep]) > 1:
                logger.error("VIP rule id=%s got more than one keep rank rule!" % rule.current_rank_id.id)
        # Các KH cần cập nhật hạng thẻ
        records = self.search([('uprank_expire_date', '=', date.today())])
        print(rank_rules_dict)
        for record in records:
            # Kiểm tra nếu KH đang có yêu cầu lên hạng chờ duyệt thì bỏ qua
            existed = self.env.cr.execute('SELECT 1=1 FROM crm_vip_customer_confirm WHERE partner_id=' + record.partner_id.id)
            if rank_rules_dict[record.vip_rank.id]:
                # TH lên hạng do doanh thu đột biến
                for rule in rank_rules_dict['%s_suddenly' % record.vip_rank.id]:
                    if rule[1]['rank_level'] < self.partner_id.x_rank.rank_level \
                            and record.partner_id.check_suddenly_revenue(rule[1]['revenue']):
                        # Tạo y/c lên hạng cho KH
                        self.env['crm.vip.customer.confirm'].create({
                            'partner_id': record.id,
                            'month_rank': rule[1]['active_month'],
                            'rank_request': rule[0],
                            'rank_current': self.partner_id.x_rank.id or False,
                            'note': 'Gợi ý lên hạng theo doanh thu',
                            'type': 'suddenly',
                            'state': 'new'
                        })
                        # Tạo bản ghi lịch sử lên hạng - chờ duyệt
                        self.env['crm.vip.customer.history'].create({
                            'partner_id': self.partner_id.id,
                            'rank_current': self.partner_id.x_rank.id,
                            'rank_request': rule[0],
                            'vip_custom_id': record.id,
                            'state': 'pending',
                        })
                # TH lên hạng do doanh thu tích luỹ
                # TH giữ hạng
                # TH xuống hạng


class VipCustomerConfirm(models.Model):
    _name = 'crm.vip.customer.confirm'
    _description = u'Xác nhận lên hạng'
    _order = 'create_date desc'

    partner_id = fields.Many2one('res.partner', string=u'Khách hàng')
    name = fields.Char(string=u'Tên', related='partner_id.name', readonly=True)
    partner_code = fields.Char(string=u'Mã KH', related='partner_id.x_code', readonly=True)
    phone = fields.Char(string=u'Điện thoại', related='partner_id.phone', readonly=True)
    email = fields.Char(string='Email', related='partner_id.email', readonly=True)
    birthday = fields.Date(string=u'Sinh nhật', related='partner_id.x_birthday', readonly=True)
    address = fields.Char(string=u'Địa chỉ', related='partner_id.street', readonly=True)
    vip_rank = fields.Many2one(string=u'Hạng VIP', related='partner_id.x_rank', readonly=True)
    user_id = fields.Many2one(string=u'Nhân viên chăm sóc', related='partner_id.user_id', readonly=True)
    rank_current = fields.Many2one('crm.vip.rank', string=u'Hạng hiện tại', readonly=True)
    rank_request = fields.Many2one('crm.vip.rank', string=u'Hạng yêu cầu', readonly=True)
    month_rank = fields.Integer(string=u'Số tháng')
    note = fields.Text(string=u'Ghi chú')
    cancel_reason = fields.Text('Cancel reason')
    type = fields.Selection([('auto', u'Tự động'), ('manual', u'Thủ công'), ('except', u'Ngoại lệ')], u'Loại yêu cầu', default='auto')
    state = fields.Selection([('new', 'Wait confirm'), ('confirm', 'Confirm'),
                              ('done', "Done"), ('cancel', 'Cancel')], u'Trạng thái', default='new')

    def uprank(self):
        old_rank_id = self.partner_id.x_rank.id
        # Cập nhật lịch sử lên hạng
        self.env['crm.vip.customer.history'].search(
            [('partner_id', '=', self.partner_id.id), ('state', '=', 'pending')], limit=1
        ).write({'state': 'approved', 'approved_uid': self._uid, 'approved_date': date.today()})
        # Cập nhật hạng của KH
        self.partner_id.write({'x_rank': self.rank_request.id})
        # Cập nhật thông tin VIP của KH
        self.env['crm.vip.customer'].search(
            [('partner_id', '=', self.partner_id.id)], limit=1
        ).write({'uprank_date': date.today(),
                 'uprank_expire_date': date.today() + relativedelta(months=self.rank_request.active_month + 1, days=-date.today().day)})
        new_rank_id = self.partner_id.x_rank.id
        # Cộng điểm VIP lên hạng
        up_rule = self.env['crm.vip.rank.rule'].search([('current_rank_id', '=', old_rank_id)], limit=1)
        if up_rule:
            for line in up_rule.line_ids:
                if line.rank_id.id == new_rank_id and line.reward_points > 0:
                    self.env['izi.vip.point.history'].create({
                        'partner_id': self.partner_id.id,
                        'date': date.today(),
                        'point': line.reward_points
                    })
                    break
        else:
            raise MissingError("There is no up rank rule for this confirm request!")

    @api.multi
    def action_approve_confirm_uprank(self):
        self.ensure_one()
        if self.user_has_groups('pos_security.group_pos_supervisor_user'):
            self.uprank()
            # Cập nhật trạng thái bản ghi xác nhận
            self.write({'state': 'done'})
        elif self.user_has_groups('sales_team.group_sale_manager'):
            if self.type == 'except':
                self.write({'state': 'confirm'})
            else:
                self.uprank()
                self.write({'state': 'done'})
        else:
            raise AccessDenied(u"Bạn không có quyền xác nhận lên hạng, thao tác không hoàn thành!")

    @api.multi
    def action_super_approve_confirm_uprank(self):
        self.ensure_one()
        if self.user_has_groups('pos_security.group_pos_supervisor_user'):
            self.uprank()
            # Cập nhật trạng thái bản ghi xác nhận
            self.write({'state': 'done'})
        else:
            raise AccessDenied(u"Bạn không có quyền xác nhận lên hạng, thao tác không hoàn thành!")

    @api.multi
    def action_reject_confirm_uprank(self):
        self.ensure_one()
        if self.user_has_groups('sales_team.group_sale_manager'):
            # Cập nhật lịch sử lên hạng
            self.env['crm.vip.customer.history'].search(
                [('partner_id', '=', self.partner_id.id), ('state', '=', 'pending')], limit=1
            ).write({'state': 'cancel'})
            # Cập nhật trạng thái bản ghi xác nhận
            self.write({'state': 'cancel'})
        else:
            raise AccessDenied(u"Bạn không có quyền từ chối lên hạng, thao tác không hoàn thành!")


class VipCustomerHistory(models.Model):
    _name = 'crm.vip.customer.history'
    _description = u'Lịch sử lên hạng'
    _order = 'create_date desc'

    partner_id = fields.Many2one('res.partner', string=u'Khách hàng')
    rank_current = fields.Many2one('crm.vip.rank', string=u'Hạng hiện tại', readonly=True)
    rank_request = fields.Many2one('crm.vip.rank', string=u'Hạng yêu cầu', readonly=True)
    state = fields.Selection([('pending', u'Chờ duyệt'), ('approved', u'Đã duyệt'), ('cancel', u'Đã từ chối')], u'Trạng thái', default='pending')
    approved_uid = fields.Many2one('res.users', u'Người duyệt cuối')
    approved_date = fields.Date('Ngày duyệt')
    vip_custom_id = fields.Many2one('crm.vip.customer', u'Khách hàng')
    type = fields.Selection([('up', u'Lên hạng'), ('down', u'Xuống hạng tự động')], u'Loại', default='up')

