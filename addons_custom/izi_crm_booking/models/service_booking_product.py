# -*- coding: utf-8 -*-


from odoo import models, fields, api, _


class ServiceBookingProduct(models.Model):
    _name = 'service.booking.product'
    _description = 'Service booking product'

    product_id = fields.Many2one('product.product', string='Product')
    qty = fields.Integer(string='Quantity', default=1)
    service_booking_id = fields.Many2one('service.booking', string='Service booking')
    amount_total = fields.Float(string="Amount total")

    _sql_constraints = [
        ('check_qty', 'check(qty > 0)', 'Product quantity can not less than 0')
    ]

    @api.onchange('product_id', 'qty')
    def _onchange_product_id_qyt(self):
        if not self.service_booking_id.customer_id:
            self.product_id = False
            self.qty = False
            return {
                'warning': {
                    'title': _('Thông báo'),
                    'message': _('Vui lòng chọn khách hàng trước khi chọn sản phẩm!')}
            }

        if self.product_id and self.qty:
            priceprice = self.service_booking_id.customer_id.property_product_pricelist.get_product_price(
                                         self.product_id, self.qty or 1.0,
                                         self.service_booking_id.customer_id)
            self.amount_total = priceprice  * self.qty

