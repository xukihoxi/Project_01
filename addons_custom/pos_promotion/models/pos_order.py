# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError, except_orm, MissingError, ValidationError
from datetime import datetime, date
from dateutil.relativedelta import relativedelta
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT
import math
import logging

logger = logging.getLogger(__name__)


class PosOrder(models.Model):
    _inherit = 'pos.order'

    x_promotion_id = fields.Many2one('pos.promotion', 'Promotion')
    x_discount_promo = fields.Float('Promotion discount', compute='_compute_x_amount_total', store=False)

    x_applied_promo = fields.Char('Applied action', readonly=1)

    @api.multi
    def process_customer_signature(self):
        if self.x_applied_promo and len(self.x_applied_promo):
            applied_actions = map(int, self.x_applied_promo.split(','))
            promo_ids = self.env['pos.promotion.line'].browse(applied_actions)
            promo_ids.applied_partner_ids = [4, self.partner_id.id]
        super(PosOrder, self).process_customer_signature()

    @api.multi
    def action_compute_order_discount(self):
        self.ensure_one()
        if self.lines and not self.x_pos_partner_refund_id:
            # Lấy điểm bán hàng theo phiên trên đơn hàng
            try: pos_id = self.session_id.config_id.id
            except: raise UserError("Session must be opened before promotion calculating is execute!")
            # Kiểm tra nếu có chương trình KH đang hoạt động
            # today = date.today().strftime(DEFAULT_SERVER_DATE_FORMAT)
            # active_promo = self.env['pos.promotion'].search([('state', '=', 'activated'), ('pos_id', '=', pos_id),
            #                                                  ('date_start', '<=', today), ('date_end', '>=', today)])
            if not self.pricelist_id:
                raise UserError(
                    _('You have to select a pricelist in the form !\n'
                      'Please set one before choosing a product.'))
            product_obj = self.env['product.product']
            # Tổng số các sản phẩm chọn mua bao gồm sản phẩm lặp
            to_buy_product_dict = {}
            to_buy_product_ids = []
            # Số lượng thực xuất của các dòng quà tặng
            gift_real_out_dict = {}
            # Loại bỏ các sản phẩm là quà, các giảm giá, khuyến mãi đã tính trước đó (NẾU CÓ)
            for line in self.lines:
                if line.x_is_gift:
                    gift_real_out_dict[line.product_id.id] = line.x_qty
                    line.unlink()
                elif line.product_id.default_code and line.product_id.default_code.upper() == 'COIN':
                    # line.x_discount = 0
                    # line.discount = 0
                    # if line.product_id not in self.session_id.config_id.product_edit_price_ids:
                    #     line.price_unit = self.pricelist_id.get_product_price(line.product_id, 1.0, self.partner_id)
                    to_buy_product_ids.append(line.product_id.id)
                    if line.product_id.id in to_buy_product_dict:
                        to_buy_product_dict[line.product_id.id] += line.qty
                    else:
                        to_buy_product_dict[line.product_id.id] = line.qty
                elif not (line.product_id.default_code and line.product_id.default_code.upper() == 'PDDV'):
                    # line.x_discount = 0
                    # line.discount = 0
                    # if line.product_id not in self.session_id.config_id.product_edit_price_ids:
                    #     line.price_unit = self.pricelist_id.get_product_price(line.product_id, line.qty, self.partner_id)
                    to_buy_product_ids.append(line.product_id.id)
                    if line.product_id.id in to_buy_product_dict:
                        to_buy_product_dict[line.product_id.id] += line.qty
                    else:
                        to_buy_product_dict[line.product_id.id] = line.qty

            to_buy_product_dict2 = dict(to_buy_product_dict)
            to_buy_product_dict3 = dict(to_buy_product_dict)
            #ngoant xu ly doan chap thuan ctkm neu ban duoi gia
            #xử lý field x_custom_discount cho từng line
            for line in self.lines:
                price = self.pricelist_id.get_product_price(line.product_id, line.qty or 1.0, self.partner_id)
                if (line.price_unit * line.qty - line.x_discount) * (100 - line.discount) / 100 < price:
                    line.x_custom_discount = False
            # Nếu có chương trình khuyến mại -> thực hiện tính khuyến mại
            if self.x_promotion_id:
                # Các áp dụng khuyến mại và số lượng được chấp nhận
                to_promo_action_dict = {}
                partner_obj = self.env['res.partner']
                # Tất cả các áp dụng trong ctkm
                promo_actions = {}
                # Tính chiết khấu theo ctkm
                applied_records = []
                for line in self.x_promotion_id.line_ids:
                    # Số điều kiện đạt
                    pass_rule = 0
                    # Số lần áp dụng khuyến mại
                    count_action_apply = 0
                    # Xác định các điều kiện áp dụng KM
                    for rule in line.rule_ids:
                        try: rule_domain = eval(rule.domain)
                        except Exception as e:
                            raise UserError("Some of rules to apply promotion are invalid! %s" % str(e))

                        # Loại trừ các mã DV đặc biệt
                        for domain in rule_domain:
                            if domain[0] == 'type' and domain[1] == '=' and domain[2] == 'service':
                                rule_domain.append(['default_code', 'not in', ['COIN', 'PDDV', 'DISCOUNT', 'VDISCOUNT', 'PHOI']])

                        # Loại các chương trình áp dụng 1 lần đã áp dụng cho KH mua đơn
                        if line.apply_once and self.partner_id.id in line.applied_partner_ids.ids:
                            continue

                        # Nếu điều kiện áp dụng cho sản phẩm
                        if rule.type == 'product':
                            # Lấy các sản phẩm theo điều kiện
                            rule_domain.append(['id', 'in', to_buy_product_ids])
                            try: mapped_rule_products = product_obj.search(rule_domain)
                            except: raise UserError("Some of product rules to apply promotion are invalid!")
                            if len(mapped_rule_products):
                                mapped_product_count = {}
                                f = True
                                for mapped_product in mapped_rule_products:
                                    if mapped_product.id in to_buy_product_dict and to_buy_product_dict[mapped_product.id] >= rule.count:
                                        mapped_product_count[mapped_product.id] = to_buy_product_dict[mapped_product.id]
                                    else:
                                        f = False
                                if f:
                                    if rule.count != 0:
                                        lowest = None
                                        for i in mapped_product_count:
                                            count_action = 1 if rule.count == -1 else math.floor(mapped_product_count[i] / rule.count)
                                            if not lowest or count_action < lowest:
                                                lowest = count_action
                                                to_buy_product_dict3[i] -= 0 if rule.count == -1 else lowest * rule.count
                                            else:
                                                to_buy_product_dict3 = dict(to_buy_product_dict)
                                        count_action_apply = lowest or 0
                                    pass_rule += 1

                        # Nếu điều kiện áp dụng cho KH
                        elif rule.type == 'partner':
                            try: mapped_partner = partner_obj.search(rule_domain)
                            except: raise UserError("Partner rule to apply promotion is invalid!")
                            # Nếu KH không thuộc điều kiện KM => Chuyển qua dòng KM khác
                            if self.partner_id.id not in mapped_partner.ids:
                                continue
                            else:
                                pass_rule += 1
                                if pass_rule == len(line.rule_ids) and not count_action_apply:
                                    count_action_apply = 1
                    # Nếu số điều kiện đạt = số điều kiện km => thực hiện action
                    if pass_rule == len(line.rule_ids) and count_action_apply:
                        if line.apply_once:
                            applied_records.append(line.id)
                        to_buy_product_dict = dict(to_buy_product_dict3)
                        for actition_id in line.action_ids:
                            if actition_id.id not in to_promo_action_dict:
                                to_promo_action_dict[actition_id.id] = count_action_apply
                                promo_actions[actition_id.id] = actition_id
                            else:
                                to_promo_action_dict[actition_id.id] += count_action_apply
                # Ghi lại các dòng khuyến mại được chấp nhận
                if len(applied_records):
                    self.x_applied_promo = ','.join(map(str, applied_records))
                # Nếu có các áp dụng KM
                if len(to_promo_action_dict):
                    gift_products = {}                  # Tặng quà
                    fixed_price_product_dict = {}       # Giá cố định
                    discount_percent = 0.0              # Giảm %
                    discount_amount = 0.0               # Giảm số tiền cụ thể
                    discount_amount_product_dict = {}

                    # Cộng dồn các khuyến mại
                    for action in to_promo_action_dict:
                        if not promo_actions[action].active: continue
                        if promo_actions[action].type == 'gift':
                            # Thêm các sản phẩm được tặng
                            for p in promo_actions[action].line_ids:
                                if p.product_id.id in gift_products:
                                    gift_products[p.product_id.id] += to_promo_action_dict[action] * p.product_qtt
                                else:
                                    gift_products[p.product_id.id] = to_promo_action_dict[action] * p.product_qtt
                        elif promo_actions[action].type == 'discount_amount':
                            if promo_actions[action].product_id.id in discount_amount_product_dict:
                                discount_amount_product_dict[promo_actions[action].product_id.id] += to_promo_action_dict[action] * promo_actions[action].discount
                            else:
                                discount_amount_product_dict[promo_actions[action].product_id.id] = to_promo_action_dict[action] * promo_actions[action].discount
                        elif promo_actions[action].type == 'discount_percent':
                            discount_percent += promo_actions[action].discount
                        elif promo_actions[action].type == 'fixed_price':
                            for p in promo_actions[action].line_ids:
                                fixed_price_product_dict[p.product_id.id] = p.product_price
                    # Áp giá cố định các sản phẩm
                    if len(fixed_price_product_dict):
                        for line in self.lines:
                            if line.product_id.id in fixed_price_product_dict:
                                line.price_unit = fixed_price_product_dict[line.product_id.id]
                                line.x_custom_discount = True
                    # Giảm giá sp/dv cụ thể
                    if len(discount_amount_product_dict):
                        for line in self.lines:
                            if line.product_id.id in discount_amount_product_dict:
                                line.x_discount += discount_amount_product_dict[line.product_id.id]
                                line.x_custom_discount = True
                    # Giảm giá theo miền
                    for action in to_promo_action_dict:
                        if promo_actions[action].type == 'x1':
                            try:
                                action_domain = [('id', 'in', to_buy_product_ids)] + eval(promo_actions[action].domain)
                                mapped_product_action = self.env['product.product'].search(action_domain)
                            except:
                                raise UserError("Action domain %s is invalid!" % promo_actions[action].name)
                            for line in self.lines:
                                if line.product_id.id in mapped_product_action.ids:
                                    line.x_discount += line.qty * (line.price_unit - line.x_discount / line.qty) * \
                                                       promo_actions[action].discount / 100.0
                                    line.x_custom_discount = True

                    # Tính chiết khấu giảm giá bậc thang
                    for action in to_promo_action_dict:
                        if promo_actions[action].type == 'fixed_percent':
                            if promo_actions[action].product_id.id in to_buy_product_dict2:
                                for item in self.lines.filtered(
                                        lambda r: r.product_id.id == promo_actions[action].product_id.id):
                                    item_discount = 0.0
                                    qty_line = to_buy_product_dict2[promo_actions[action].product_id.id]
                                    for x in promo_actions[action].line_ids:
                                        if to_buy_product_dict2[promo_actions[action].product_id.id] >= x.product_qtt:
                                            qty = min(x.product_qtt, to_buy_product_dict2[promo_actions[action].product_id.id])
                                            item_discount += qty * (item.price_unit - item.x_discount/qty_line) * x.price_percent / 100
                                            to_buy_product_dict2[promo_actions[action].product_id.id] -= x.product_qtt
                                    item.x_discount += item_discount
                                    item.x_custom_discount = True
                    # Áp dụng tặng quà
                    if len(gift_products):
                        for pid in gift_products:
                            record = product_obj.browse(pid)
                            if record:
                                price = self.pricelist_id.get_product_price(record, 1.0, self.partner_id)
                                self.env['pos.order.line'].create({
                                    'product_id': pid,
                                    'qty': gift_products[pid],
                                    'price_unit': price,
                                    'discount': 100.0,
                                    'order_id': self.id,
                                    'x_is_gift': True,
                                    'x_custom_discount':True,
                                    'x_qty': gift_real_out_dict[pid] if pid in gift_real_out_dict else gift_products[pid],
                                })
                    # Áp dụng giảm giá % các sản phẩm
                    sum_discount_amount = 0.0
                    if discount_percent:
                        sum_discount_amount += self.amount_total * discount_percent / 100.0
                        for product in self.lines:
                            product.x_discount += product.price_subtotal_incl * discount_percent / 100.0
                            line.x_custom_discount = True
                    # Giảm tiền tổng đơn
                    if discount_amount:
                        sum_discount_amount += discount_amount
                        discount_amount_left = discount_amount
                        for index, product in enumerate(self.lines):
                            if not product.x_is_gift:
                                line.x_custom_discount = True
                                if index < len(self.lines) - 1:
                                    per_product = int((discount_amount * (product.price_subtotal_incl / self.amount_total)) / 1000) * 1000
                                    product.x_discount += per_product
                                    discount_amount_left -= per_product
                                else:
                                    product.x_discount += discount_amount_left

                # Nếu chương trình khuyến mại được chạy cùng chiết khấu VIP
                if self.x_promotion_id.vip_include:
                    # Tính chiết khấu VIP sau khi áp dụng ctkm
                    super(PosOrder, self).action_compute_order_discount()
                self._compute_x_amount_total()
            else:
                super(PosOrder, self).action_compute_order_discount()
