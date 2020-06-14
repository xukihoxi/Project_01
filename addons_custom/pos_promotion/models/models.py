# -*- coding: utf-8 -*-

from odoo import api, fields, models, tools, SUPERUSER_ID, _
from odoo.exceptions import AccessDenied, AccessError, UserError, ValidationError, MissingError, except_orm
from datetime import date, datetime
from collections import namedtuple
Range = namedtuple('Range', ['start', 'end'])
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT


class PosPromotionActionLine(models.Model):
    _name = 'pos.promotion.action.line'

    @api.onchange('buy_product_id')
    def _onchange_product_id(self):
        if self.buy_product_id:
            self.promo_product_price = self.buy_product_id.list_price

    action_id = fields.Many2one('pos.promotion.action', 'Action')
    sequence = fields.Integer('Sequence', default=1)
    product_id = fields.Many2one('product.product', 'Product')
    product_qtt = fields.Integer('Quantity')
    product_price = fields.Float('Price')
    price_percent = fields.Float('Price (%)')

    @api.onchange('product_id')
    def onchange_price(self):
        if self.product_id.id:
            self.product_qtt = 1
            self.product_price = self.product_id.product_tmpl_id.list_price


class PosPromotionAction(models.Model):
    _name = 'pos.promotion.action'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char('Name', track_visibility='onchange')
    type = fields.Selection([
        ('discount_amount', 'Product discount'),
        ('discount_percent', 'Discount percent'),
         ('gift', 'Gift'),
        ('fixed_price', 'Fixed price'),
        ('fixed_percent', 'Fixed percent'),
         ('x1', 'Giảm % theo điều kiện'),
    ], 'Type', track_visibility='onchange')
    discount = fields.Float('Discount')
    product_id = fields.Many2one('product.product', 'Product')
    active = fields.Boolean('Is active?', default=True, track_visibility='onchange')
    line_ids = fields.One2many('pos.promotion.action.line', 'action_id', 'Products', track_visibility='onchange')
    domain = fields.Char('Domain')

    @api.multi
    def unlink(self):
        for r in self:
            sql = 'select 1=1 from pos_promotion_action_pos_promotion_line_rel where pos_promotion_action_id=%s limit 1' % r.id
            self.env.cr.execute(sql)
            res = self.env.cr.fetchone()
            if res:
                raise ValidationError("This action is in use, cannot delete!")
        return super(PosPromotionAction, self).unlink()

    @api.multi
    def button_activate(self):
        for record in self:
            record.active = not record.active


class PosPromotionRule(models.Model):
    _name = 'pos.promotion.rule'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char('Name', track_visibility='onchange')
    type = fields.Selection([('product', 'Product'), ('partner', 'Partner')], 'Type', default='product', track_visibility='onchange')
    count = fields.Integer('Count', default=1, track_visibility='onchange')
    domain = fields.Char('Domain', track_visibility='onchange')
    context = fields.Char('Context', track_visibility='onchange')

    @api.model
    def create(self, vals):
        model_obj = self.env['product.template'] if vals['type'] == 'product' else self.env['res.partner']
        try:
            model_obj.search(eval(vals['domain']))
        except:
            raise UserError("Rule to apply promotion is invalid %s" % vals['domain'])
        return super(PosPromotionRule, self).create(vals)

    @api.multi
    def write(self, vals):
        res = super(PosPromotionRule, self).write(vals)
        for r in self:
            model_obj = self.env['product.template'] if r.type == 'product' else self.env['res.partner']
            try:
                model_obj.search(eval(r.domain))
            except:
                raise UserError("Rule to apply promotion is invalid! %s" % r.domain)
        return res

    @api.multi
    def unlink(self):
        for r in self:
            sql = 'select 1=1 from pos_promotion_line_pos_promotion_rule_rel where pos_promotion_rule_id=%s limit 1' % r.id
            self.env.cr.execute(sql)
            res = self.env.cr.fetchone()
            if res:
                raise ValidationError("This rule is in use, cannot delete!")
        return super(PosPromotionRule, self).unlink()


class PosPromotionLine(models.Model):
    _name = 'pos.promotion.line'

    _order = 'sequence asc'

    sequence = fields.Integer('Sequence', default=1)
    promotion_id = fields.Many2one('pos.promotion', 'Promotion program')
    rule_ids = fields.Many2many('pos.promotion.rule', string='Rules')
    action_ids = fields.Many2many('pos.promotion.action', string='Actions')
    apply_once = fields.Boolean('Apply once')
    applied_partner_ids = fields.Many2many('res.partner', 'pos_promotion_line_partner_rel', 'promotion_line_id', 'partner_id', 'Applied customers')


class PosPromotion(models.Model):
    _name = 'pos.promotion'
    _description = u'Chương trình khuyến mại'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char('Name')
    date_start = fields.Date('Start date')
    date_end = fields.Date('End date')
    campaign_id = fields.Many2one('utm.campaign', 'Campaign')
    pos_id = fields.Many2one('pos.config', 'Point of Sale')
    line_ids = fields.One2many('pos.promotion.line', 'promotion_id', 'Promotion lines', copy=True)
    vip_include = fields.Boolean('VIP include', default=True)
    state = fields.Selection([('draft', 'Draft'), ('activated', 'Activated'), ('expired', 'Expired'),
                             ('cancel', 'Cancel')], 'State', default='draft')\

    @api.constrains('date_start', 'date_end')
    def _check_expired_date(self):
        if self.date_start > self.date_end:
            raise ValidationError(_(u"Ngày kết thúc không thể đặt trước ngày bắt đầu!"))

    @api.multi
    def button_activate(self):
        # Nếu không có dòng km nào -> ko cho active
        if not self.line_ids:
            raise ValidationError("Hãy thêm các quy tắc áp dụng trước khi kích hoạt chương trình khuyến mại này!")
        # Kiểm tra chồng chéo ngày bắt đầu - kết thúc của các ctkm trên cùng điểm bán
        # activated_promo = self.search([('pos_id', '=', self.pos_id.id), ('state', '=', 'activated')])
        # if len(activated_promo):
        #     for r in activated_promo:
        #         r1 = Range(start=datetime.strptime(r.date_start, DEFAULT_SERVER_DATE_FORMAT),
        #                    end=datetime.strptime(r.date_end, DEFAULT_SERVER_DATE_FORMAT))
        #         r2 = Range(start=datetime.strptime(self.date_start, DEFAULT_SERVER_DATE_FORMAT),
        #                    end=datetime.strptime(self.date_end, DEFAULT_SERVER_DATE_FORMAT))
        #         latest_start = max(r1.start, r2.start)
        #         earliest_end = min(r1.end, r2.end)
        #         delta = (earliest_end - latest_start).days + 1
        #         if max(0, delta):
        #             raise ValidationError("This promotion date range is overlap with date range of a promotion name \"%s\"" % r.name)
        self.state = 'activated'

    @api.multi
    def button_deactivate(self):
        self.state = 'cancel'

    @api.model
    def cron_check_expired_promotion_program(self):
        records = self.search([('state', '=', 'activated')])
        for record in records:
            if record.date_end:
                date_end = datetime.strptime(record.date_end, DEFAULT_SERVER_DATE_FORMAT).date()
                if date_end < date.today():
                    record.state = 'expired'

    @api.multi
    def write(self, vals):
        # if self.state != 'draft' and 'state' not in vals:
        #     raise UserError("This promotion program's state is %s and cannot be edit!" % dict(self._fields['state'].selection).get(self.state))
        return super(PosPromotion, self).write(vals)

    @api.multi
    def unlink(self):
        for r in self:
            if r.state != 'draft':
                raise UserError("You can only delete a promotion program that its state is Draft")
        return super(PosPromotion, self).unlink()

    @api.model
    def name_search(self, name='', args=None, operator='ilike', limit=100):
        args = args or []
        if len(name):
            args.append(('name', 'ilike', name))
        res = self.search(args, limit=limit)
        return res.name_get()

    @api.model
    def search(self, args, offset=0, limit=None, order=None, count=False):
        if self._context.get('izi_pos_promotion'):
            today = date.today().strftime(DEFAULT_SERVER_DATE_FORMAT)
            session_id = self.env['pos.session'].browse(self._context.get('izi_session_id'))
            tester_uids = self.env['ir.config_parameter'].sudo().get_param('pos.promo_tester_uid')
            try:
                tester_uids = eval(tester_uids)
            except:
                pass
            if (isinstance(tester_uids, list)) and self._uid in tester_uids:
                args += [
                    ('state', 'not in', ['expired', 'cancel']),
                    # ('pos_id', '=', session_id.config_id.id),
                    # ('date_start', '<=', today),
                    ('date_end', '>=', today),
                ]
            else:
                args += [
                    ('state', '=', 'activated'),
                    ('pos_id', '=', session_id.config_id.id),
                    ('date_start', '<=', today),
                    ('date_end', '>=', today),]

        return super(PosPromotion, self).search(args, offset, limit, order, count)
