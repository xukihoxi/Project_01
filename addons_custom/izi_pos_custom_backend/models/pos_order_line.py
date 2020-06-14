# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import except_orm, UserError, ValidationError


class PosOrderLine(models.Model):
    _inherit = 'pos.order.line'

    x_discount = fields.Float('Discount',track_visibility='always')
    lot_name = fields.Char("Lot Name")
    x_qty = fields.Float('Qty outgoing')
    x_check_service = fields.Boolean('Check Service', compute='_compute_check_service', default=False, )
    x_charge_refund = fields.Boolean("Charge Refund", compute='_compute_check_service', default=False)
    x_quantity_refund = fields.Float("Quantity Refund", default=0)
    x_name_set_id = fields.Many2one('product.name.set', string="Name")
    x_custom_discount = fields.Boolean('Custom discount', copy=False)
    x_edit_price = fields.Boolean(string="Edit price", compute='_compute_x_edit_price', copy=False)
    # x_uom_id = fields.Many2one('product.uom', relate="product_id.uom_id", string="Uom")

    @api.multi
    def unlink(self):
        for line in self:
            for tmp in line.pack_lot_ids:
                tmp.unlink()
        return super(PosOrderLine, self).unlink()

    @api.depends('product_id')
    def _compute_x_edit_price(self):
        for s in self:
            for product_edit_price in s.order_id.session_id.config_id.product_edit_price_ids:
                if s.product_id.id == product_edit_price.id:
                    s.x_edit_price = True
                    break

    @api.depends('price_unit', 'tax_ids', 'qty', 'discount', 'product_id', 'x_discount')
    def _compute_amount_line_all(self):
        for line in self:
            if line.qty != 0:
                fpos = line.order_id.fiscal_position_id
                tax_ids_after_fiscal_position = fpos.map_tax(line.tax_ids, line.product_id,
                                                             line.order_id.partner_id) if fpos else line.tax_ids
                price = (line.price_unit - line.x_discount / line.qty) * (1 - (line.discount or 0.0) / 100.0)
                taxes = tax_ids_after_fiscal_position.compute_all(price, line.order_id.pricelist_id.currency_id,
                                                                  line.qty,
                                                                  product=line.product_id,
                                                                  partner=line.order_id.partner_id)
                line.price_subtotal = line.price_subtotal_incl = taxes['total_included']
                # line.write({
                #     'price_subtotal_incl': taxes['total_included'],
                #     'price_subtotal': taxes['total_excluded'],
                # })

    @api.onchange('qty', 'discount', 'price_unit', 'tax_ids')
    def _onchange_qty(self):
        pass
        # if self.product_id:
        #     if not self.order_id.pricelist_id:
        #         raise UserError(_('You have to select a pricelist in the sale form !'))
        #     price = self.price_unit * (1 - (self.discount or 0.0) / 100.0)
        #     self.price_subtotal = self.price_subtotal_incl = price * self.qty
        #     if (self.product_id.taxes_id):
        #         taxes = self.product_id.taxes_id.compute_all(price, self.order_id.pricelist_id.currency_id, self.qty,
        #                                                      product=self.product_id, partner=False)
        #         self.price_subtotal = taxes['total_excluded']
        #         self.price_subtotal_incl = taxes['total_included']

    @api.onchange('product_id')
    def _onchange_product(self):
        for s in self:
            s.x_name_set_id = False

    @api.onchange('price_unit')
    def onchange_price_unit(self):
        if self.product_id:
            price = self.order_id.pricelist_id.get_product_price(self.product_id, self.qty or 1.0, self.order_id.partner_id)
            if (self.price_unit * self.qty - self.x_discount) * (100 - self.discount) / 100 < price < price:
                self.x_custom_discount = False
    @api.onchange('discount')
    def onchange_discount(self):
        if self.product_id:
            price = self.order_id.pricelist_id.get_product_price(self.product_id, self.qty or 1.0,self.order_id.partner_id)
            if (self.price_unit * self.qty - self.x_discount) * (100 - self.discount) / 100 < price < price:
                self.x_custom_discount = False

    @api.onchange('x_discount')
    def onchange_x_discount(self):
        if self.product_id:
            price = self.order_id.pricelist_id.get_product_price(self.product_id, self.qty or 1.0,self.order_id.partner_id)
            if (self.price_unit * self.qty - self.x_discount) * (100 - self.discount) / 100 < price < price:
                self.x_custom_discount = False

    @api.onchange('product_id', 'qty')
    def _onchange_product_qty(self):
        for line in self:
            if line.product_id.product_tmpl_id.x_type_card in ('tdv', 'pmh') and line.qty != 1:
                raise except_orm('Cảnh báo!',
                                 ('Bạn chỉ có thể bán thẻ dịch vụ, phiếu mua hàng với số lượng là 1 trên 1 dòng'))
            if line.qty == 0:
                raise except_orm('Cảnh báo!',
                                 ('Bạn chỉ có thể bán sản phẩm với số lượng khác 0 trên 1 dòng'))
            if line.product_id and line.product_id.default_code != 'COIN':
                # line.price_unit = 0
                if line.product_id.type != 'service':
                    total_availability = self.env['stock.quant']._get_available_quantity(line.product_id, line.order_id.location_id)
                    warning_mess = {
                        'title': _('Cảnh báo!'),
                        'message': _('Sản phẩm "' + str(
                            line.product_id.product_tmpl_id.name) + '" đang có số lượng tồn kho là ' + str(
                            total_availability)) + ' đơn vị sản phẩm.'
                    }
                    if line.qty > total_availability:
                        return {'warning': warning_mess}

    # @api.onchange('x_qty', 'qty')
    # def _check_x_qty(self):
    #     if self.x_qty and self.qty:
    #         if self.qty <= 0:
    #             if self.x_qty > self.qty:
    #                 self.x_qty = self.qty
    #             # raise except_orm('Cảnh báo!',
    #             #                  ('Số lượng thực xuất không được lớn hơn số lượng mua'))

    @api.onchange('x_qty', 'qty')
    def _check_x_qty(self):
        self.x_qty = self.qty
        if self.x_qty > 0 and self.qty:
            if abs(self.x_qty) > abs(self.qty):
                raise except_orm('Cảnh báo!',
                                 ('Số lượng thực xuất không được lớn hơn số lượng mua'))

    @api.onchange('qty')
    def _check_qty(self):
        for line in self:
            if line.order_id.x_pos_partner_refund_id.id != False:
                for tmp in line.order_id.x_pos_partner_refund_id.lines:
                    if line.product_id.id == tmp.product_id.id and not tmp.x_is_gift :
                        if abs(tmp.qty) < abs(line.qty):
                            raise except_orm("Cảnh báo!", ("Bạn không thể refund số lượng nhiều hơn lúc mua"))
                        if line.qty > 0:
                            raise except_orm("Cảnh báo!", ("Bạn không thể refund số lượng nhiều hơn lúc mua"))

    @api.depends('product_id')
    def _compute_check_service(self):
        for line in self:
            if line.product_id.product_tmpl_id.type == 'service':
                line.x_check_service = True
            if line.product_id.id == line.order_id.session_id.config_id.x_charge_refund_id.id:
                line.x_charge_refund = True
            for i in line.order_id.session_id.config_id.product_edit_price_ids:
                if line.product_id.id == i.id:
                    line.x_charge_refund = True
                    continue

    @api.onchange('product_id')
    def _onchange_izi_pos_product_id(self):
        list = []
        if self.order_id:
            for item in self.order_id.session_id.config_id.x_category_ids:
                product_ids = self.env['product.product'].search(
                    [('pos_categ_id', '=', item.id), ('active', '=', True) ,('available_in_pos', '=', True)])
                for product_id in product_ids:
                    list.append(product_id.id)
        #ngadv test
        # product_ids = self.env['product.product'].search([])
        # for product_id in product_ids:
        #     list.append(product_id.id)
        return {
            'domain': {'product_id': [('id', 'in', list)]}
        }