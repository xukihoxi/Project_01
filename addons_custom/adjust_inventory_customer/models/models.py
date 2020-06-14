# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from datetime import datetime
from odoo.exceptions import except_orm, ValidationError, UserError


class Adjust(models.Model):
    _name = 'adjust.inventory.customer'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    serial = fields.Char("Code", required=True)
    name = fields.Char()
    date = fields.Datetime(string='Date', default=fields.Datetime.now)
    partner_id = fields.Many2one('res.partner', 'Khách hàng')
    x_rank = fields.Many2one('crm.vip.rank', string=u'Hạng VIP', track_visibility='onchange')
    x_loyal_total = fields.Float('Doanh thu tích lũy', track_visibility='onchange')
    x_debit_money = fields.Float('Công nợ',track_visibility='onchange')
    state = fields.Selection([('draft', "Draft"), ('done', "Done")], default='draft', track_visibility='onchange')

    card_detail_ids = fields.One2many('adjust.inventory.customer.service', 'x_search_id')
    coin_ids = fields.One2many('adjust.inventory.customer.coin', 'x_search_id')
    debit_ids = fields.One2many('adjust.inventory.customer.debit', 'x_search_id')
    deposit_ids = fields.One2many('adjust.inventory.customer.deposit', 'x_search_id')

    @api.onchange('partner_id')
    def _onchange_name(self):
        if self.partner_id:
            self.name = self.partner_id.name

    @api.multi
    def action_check(self):
        x_debit_money = 0
        if not self.serial:
            raise except_orm(("Cảnh báo!"), ('Xin nhập mã trước khi tìm kiếm'))
        else:
            for l in self.card_detail_ids:
                l.unlink()
            for l in self.coin_ids:
                l.unlink()
            for l in self.debit_ids:
                l.unlink()
            for l in self.deposit_ids:
                l.unlink()
            serial = self.serial.upper().strip()
            customer_id = self.env['res.partner'].search(
                ['|', '|', '|', ('x_code', '=', serial), ('x_old_code', '=', serial), ('phone', '=', serial),
                 ('mobile', '=', serial)], limit=1)
            if customer_id.id == False:
                raise except_orm(("Cảnh báo!"), ('Mã tìm kiếm không có trong hệ thống!'))
            # line
            card_detail_ids = self.env['adjust.inventory.customer.service']
            coin_ids = self.env['adjust.inventory.customer.coin']
            debit_ids = self.env['adjust.inventory.customer.debit']
            deposit_ids = self.env['adjust.inventory.customer.deposit']

            # san pham va dich vu
            import_product = self.env['stock.inventory.customer.update.product'].search(
                [('partner_id', '=', customer_id.id), ('inventory_id.state', '=', 'done')])
            for index in import_product:
                if index.lot_id:
                    # tdv
                    # dichvutrongthe
                    for detail in index.lot_id.x_card_detail_ids:
                        vals2 = {
                            'lot_id': index.lot_id.id,
                            'product_id': detail.product_id.id,
                            'total_qty': detail.total_qty,
                            'qty_hand': detail.qty_hand,
                            'qty_use': detail.qty_use,
                            'price_unit': detail.price_unit,
                            'remain_amount': detail.remain_amount,
                            'amount_total': detail.amount_total,
                            'x_search_id': self.id,
                        }
                        card_detail_ids.create(vals2)
                else:
                    debit_line = self.env['pos.debit.good.line'].search([('order_id', '=', index.order_id.id)])
                    for line in debit_line:
                        debit_vals_line = {
                            'order_id': index.order_id.id,
                            'product_id': line.product_id.id,
                            'qty': line.qty,
                            'qty_depot': line.qty_depot,
                            'qty_debit': line.qty_debit,
                            'date': line.date,
                            'debit_id': line.id,
                            'x_search_id': self.id,
                        }
                        debit_ids.create(debit_vals_line)
                x_debit_money += index.debt
            # the tien
            import_coin = self.env['stock.inventory.customer.update.coin'].search(
                [('partner_id', '=', customer_id.id), ('inventory_id.state', '=', 'done')])
            for index in import_coin:
                for tt in customer_id.virtual_money_ids:
                    if tt.order_id.id == index.order_id.id:
                        vals5 = {
                            'money': tt.money,
                            'order_id': tt.order_id.id,
                            'debt_amount': tt.debt_amount,
                            'expired': tt.expired,
                            'money_used': tt.money_used,
                            'typex': tt.typex,
                            'x_search_id': self.id,
                            'state': tt.state,
                            'virtual_money_id': tt.id,
                        }
                        coin_ids.create(vals5)
                        x_debit_money += tt.debt_amount

            # tien ky gui
            import_money = self.env['stock.inventory.customer.update.money'].search(
                [('partner_id', '=', customer_id.id), ('inventory_id.state', '=', 'done')])
            for index in import_money:
                line = self.env['pos.customer.deposit.line'].search(
                    [('amount', '=', index.x_amount), ('note', '=', 'Update')], limit=1)
                vals5 = {
                    'x_amount': index.x_amount,
                    'partner_id': customer_id.id,
                    'x_search_id': self.id,
                    'deposit_line': line.id,
                }
                deposit_ids.create(vals5)
            self.partner_id = customer_id.id
            self.name = customer_id.name
            self.x_rank = customer_id.x_rank.id
            self.x_loyal_total = customer_id.x_loyal_total
            self.x_debit_money = x_debit_money
        return True

    @api.multi
    def action_update(self):
        if self.state != 'draft':
            return True
        # Cập nhật lại dịch vụ
        for line in self.card_detail_ids:
            for detail in line.lot_id.x_card_detail_ids:
                if detail.product_id.id == line.product_id.id:
                    detail.total_qty = line.total_qty
                    detail.qty_hand = line.qty_hand
                    detail.qty_use = line.qty_use
                    detail.price_unit = line.price_unit
                    detail.remain_amount = line.remain_amount
                    detail.amount_total = line.amount_total
                    if detail.total_qty == 0:
                        detail.unlink()
            # cap nhat lai don hang
            order_line_lot = self.env['pos.order.line'].search([('lot_name', '=', line.lot_id.name)], limit=1)
            order_line_id = self.env['pos.order.line'].search(
                [('order_id', '=', order_line_lot.order_id.id), ('product_id', '=', line.product_id.id)], limit=1)

            if line.total_qty == 0:
                order_line_id.unlink()
            else:
                order_line_id.qty = line.total_qty
                order_line_id.x_qty = line.total_qty
                order_line_id.price_unit = line.price_unit
                order_line_id.x_subtotal_wo_discount = line.amount_total
                order_line_id.price_subtotal_incl = line.amount_total

        # Cập nhật lại nợ hàng:
        for line in self.debit_ids:
            if line.debit_id.debit_id.state != 'debit':
                raise except_orm(("Cảnh báo!"), ('Đơn nợ hàng của KH này đang được xử lý. Vui lòng kiểm tra lại!'))
            line.debit_id.qty = line.qty
            line.debit_id.qty_depot = line.qty_depot
            line.debit_id.qty_debit = line.qty_debit
            if line.debit_id.qty == 0:
                debit = line.debit_id
                line.debit_id = False
                debit.unlink()
            # cap nhat lai don hang
            order_line_id = self.env['pos.order.line'].search(
                [('order_id', '=', line.debit_id.order_id.id), ('product_id', '=', line.product_id.id)], limit=1)
            if line.qty == 0:
                order_line_id.unlink()
            else:
                order_line_id.qty = line.qty
                order_line_id.x_qty = line.qty_depot
                order_line_id.x_subtotal_wo_discount = order_line_id.price_unit * line.qty
                order_line_id.price_subtotal_incl = order_line_id.price_unit * line.qty

        # Cập nhật lại thẻ tiền
        for line in self.coin_ids:
            order_line_id = self.env['pos.order.line'].search([('order_id', '=', line.order_id.id)])
            for i in order_line_id:
                i.unlink()
        for line in self.coin_ids:
            if line.money == 0:
                virtual_money_id = line.virtual_money_id
                line.virtual_money_id = False
                virtual_money_id.unlink()
            else:
                line.virtual_money_id.money = line.money
                line.virtual_money_id.money_used = line.money_used
                line.virtual_money_id.debt_amount = line.debt_amount
            # cap nhat lai don hang
            # order_line_id = self.env['pos.order.line'].search([('order_id', '=', line.order_id.id)])
            # for i in order_line_id:
            #     i.unlink()
            discount = 0
            if line.typex == '2':
                discount = 100
            product_id = self.env['product.product'].search([('default_code', '=', 'COIN')])
            vals1 = {
                'product_id': product_id.id,
                'qty': line.money / product_id.product_tmpl_id.list_price,
                'price_unit': product_id.product_tmpl_id.list_price,
                'discount':discount,
                'order_id': line.order_id.id,
            }
            self.env['pos.order.line'].create(vals1)
        # Cập nhật lại tiền ký gửi
        for line in self.deposit_ids:
            line.deposit_line.amount = line.x_amount
        self.partner_id.x_rank = self.x_rank.id
        self.partner_id.x_loyal_total = self.x_loyal_total
        self.state = 'done'
