# -*- coding: utf-8 -*-
from odoo import api, fields, models, SUPERUSER_ID, _
from datetime import date
from odoo.exceptions import UserError, except_orm, MissingError, ValidationError

COMBO_MAXTHIN = {'MTNANO': 'ONGMTNANO', 'MTLIPO': 'ONGMTLIPO'}


class PosOrder(models.Model):
    _inherit = 'pos.order'

    x_therapy_record_id = fields.Many2one('therapy.record', string='Therapy Record')
    x_categ_id = fields.Many2one('product.category', related='x_therapy_record_id.categ_id', string='Category')
    x_number_massage = fields.Integer(string='Number Massage', default=0)
    x_pos_order_complement_ids = fields.One2many('pos.order.complement', 'pos_order_id', string='Pos Order Complement')
    x_barem_id = fields.Many2one('bundle.therapy.barem', string='Barem')

    @api.multi
    def action_compute_barem(self):
        for order in self:
            #Kiểm tra đơn hàng có bán nhiều loại sp không?
            #Tính toán buổi massage
            order.x_pos_order_complement_ids = False
            if not order.lines: raise UserError("Chưa có sản phẩm để tính toán!")
            host_product = order.lines[0].product_id
            arr_body_area = []
            number_massage = 0
            arr_pos_order_complement =[]

            for line in order.lines:
                if line.product_id.id != host_product.id:
                    raise UserError(_("Chỉ bán bán một loại sản phẩm trong đơn bán gói liệu trình!"))
                if line.x_body_area_ids:
                    for body_area in line.x_body_area_ids:
                        arr_body_area.append(body_area.id)
            count_area = len(set(arr_body_area))
            if not count_area: raise UserError("Bạn chưa chọn vùng trị liệu khi bán gói liệu trình.")
            if host_product.default_code == 'MTNANO':#maxthin Nano max
                number_massage = ((order.amount_total / 1600000) * 1.2) / (count_area)
            else:# Các sản phẩm còn lại
                number_massage = (order.amount_total * 1.2) / (count_area * order.lines[0].price_unit)

            # Tìm kiếm barem
            # Lấy sp/dv của barem đổ vào sp bổ trợ
            barem = order.env['bundle.therapy.barem'].search([('value_bundle_min', '<=', order.amount_total),
                                                              ('value_bundle_max', '>=', order.amount_total),
                                                              ('product_id', '=', host_product.id)], limit=1)
            if not barem: raise UserError("Không tìm thấy barem phù hợp với giá trị đơn hàng. Vui lòng kiểm tra lại!")
            for bundle_therapy_barem_line_id in barem.bundle_therapy_barem_line_ids:
                arr_pos_order_complement.append((0, 0, {
                    'product_id': bundle_therapy_barem_line_id.product_id.id,
                    'qty': 0,
                    'qty_max': bundle_therapy_barem_line_id.qty,
                    'uom_id': bundle_therapy_barem_line_id.uom_id.id,
                }))

            order.write({
                'x_pos_order_complement_ids': arr_pos_order_complement,
                'x_barem_id': barem.id,
                'x_number_massage': int(number_massage)
            })

    @api.multi
    def action_send_payment(self):
        count = 0
        for order in self:
            if order.x_therapy_record_id:
                if not order.x_pos_order_complement_ids:
                    raise UserError(_("Bạn chưa tính toán và nhập sản phẩm bổ trợ cho gói liệu trình!"))
                else:
                    product_complement_ids = order.x_pos_order_complement_ids
                    for product_complement_id in product_complement_ids:
                        count += product_complement_id.qty
                        if product_complement_id.qty > product_complement_id.qty_max:
                            raise UserError(_("Số lượng sản phẩm/ Dịch vụ %s bổ trợ vượt quá số lượng cho phép! %s/%s" % (str(product_complement_id.product_id.default_code), str(product_complement_id.qty), str(product_complement_id.qty_max))))
                    if count < 1: raise UserError(_("Tổng số lượng sản phẩm/ Dịch vụ bổ trợ ít hơn 1!"))
        return super(PosOrder, self).action_send_payment()

    def _add_service_to_service_card(self):
        if self.x_barem_id:
            pass
        else:
            PosOrderLineObj = self.env['pos.order.line']
            PosPackProductionLotObj = self.env['pos.pack.operation.lot']
            service_card = self._get_service_card()
            argvs = {
                'product_id': service_card.product_id.id,
                'name': self.name,
                'price_unit': service_card.product_id.list_price,
                'qty': 1,
                'x_qty': 1,
                'discount': 0,
                'price_subtotal': service_card.product_id.list_price,
                'lot_name': service_card.name.upper().strip(),
                'order_id': self.id,
            }
            check_lot = PosOrderLineObj.search([('lot_name', '=', service_card.name.upper().strip())])
            if len(check_lot) != 0:
                raise except_orm('Cảnh báo!', (('Mã %s đang được gắn ở đơn hàng: ' + str(
                    check_lot[0].order_id.name)) % service_card.name.upper().strip()))
            line_id = PosOrderLineObj.create(argvs)
            argvs_lot = {
                'pos_order_line_id': line_id.id,
                'lot_name': service_card.name.upper().strip(),
            }
            PosPackProductionLotObj.create(argvs_lot)

    def check_therapy_record(self):
        if self.x_barem_id:
            return True
        else:
            return False

    def _product_order(self):
        products_order = []
        for order_line in self.lines:
            if order_line.product_id.default_code not in COMBO_MAXTHIN: raise except_orm("Thông báo",
                                                                                         "Dịch vụ %s chưa được cấu hình sản phẩm đi kèm!" % (
                                                                                             str(
                                                                                                 order_line.product_id.default_code)))
            product = self.env['product.product'].search(
                [('default_code', '=', COMBO_MAXTHIN[order_line.product_id.default_code])], limit=1)
            if not product: raise except_orm("Thông báo", "Không tìm thấy sản phẩm có mã %s" % (
                str(COMBO_MAXTHIN[order_line.product_id.default_code])))
            products_order.append({
                'product_id': product.id,
                'uom_id': product.uom_id.id,
                'qty': order_line.qty,
                'body_area_ids': order_line.x_body_area_ids.ids,
            })
        # Lấy sản phẩm trong sản phẩm bổ trợ vào chi tiết gói
        for order_complement in self.x_pos_order_complement_ids:
            products_order.append({
                'product_id': order_complement.product_id.id,
                'uom_id': order_complement.product_id.uom_id.id,
                'qty': order_complement.qty
            })
        return products_order

    def _create_bundle_therapy(self):
        # Tạo gói liệu trình
        bundle_therapy_line_ids = []
        products_order = self._product_order()
        for product_order in products_order:
            bundle_therapy_line_ids.append((0, 0, product_order))
            if product_order.get('body_area_ids', False):
                print(product_order['body_area_ids'])
                body_area_ids = product_order['body_area_ids']
                product_order['body_area_ids'] = []
                product_order['body_area_ids'].append((6, 0, body_area_ids))
                print(product_order['body_area_ids'])
        bundle_therapy = {
            'order_id': self.id,
            'amount_total': self.amount_total,
            'therapy_record_id': self.x_therapy_record_id.id,
            'bundle_therapy_line_ids': bundle_therapy_line_ids,
        }
        self.env['bundle.therapy'].create(bundle_therapy)

    def _update_product_therapy(self):
        products_order = self._product_order()
        new_product_order = []
        # if self.x_therapy_record_id.product_therapy_ids:
        '''for product_order in products_order:
            for product_therapy in self.x_therapy_record_id.product_therapy_ids:
                if product_order['product_id'] == product_therapy.product_id.id:
                    product_therapy.qty_max = product_therapy.qty_max + product_order['qty']
                else:
                    new_product_order.append(product_order)
                    # self.env['product.therapy'].create({
                    #     'therapy_record_id': self.x_therapy_record_id.id,
                    #     'product_id': product_order['product_id'],
                    #     'uom_id': product_order['uom_id'],
                    #     'qty_used': 0,
                    #     'qty_max': product_order['qty'],
                    # })
                    # break'''
        for product_order in products_order:
            check = True
            if self.x_therapy_record_id.product_therapy_ids:
                for product_therapy in self.x_therapy_record_id.product_therapy_ids:
                    if product_order['product_id'] == product_therapy.product_id.id:
                        check = False
                        product_therapy.qty_max = product_therapy.qty_max + product_order['qty']
                        break
            if check:
                self.env['product.therapy'].create({
                    'therapy_record_id': self.x_therapy_record_id.id,
                    'product_id': product_order['product_id'],
                    'uom_id': product_order['uom_id'],
                    'qty_used': 0,
                    'qty_max': product_order['qty'],
                })
        # else:
        #     for product_order in products_order:
        #         self.env['product.therapy'].create({
        #             'therapy_record_id': self.x_therapy_record_id.id,
        #             'product_id': product_order['product_id'],
        #             'uom_id': product_order['uom_id'],
        #             'qty_used': 0,
        #             'qty_max': product_order['qty'],
        #         })

    @api.multi
    def action_order_confirm(self):
        if self.x_barem_id:
            self._create_bundle_therapy()# Tạo gói liệu trình
            self._update_product_therapy()#  Đổ sản phẩm vào danh mục sản phẩm tồn trên hồ sơ trị liệu
        return super(PosOrder, self).action_order_confirm()


class PosOrderLine(models.Model):
    _inherit = 'pos.order.line'

    x_body_area_ids = fields.Many2many('body.area', string='Body Area')


class PosOrderComplement(models.Model):
    _name = 'pos.order.complement'

    name = fields.Char(string='Pos Order Complement')
    product_id = fields.Many2one('product.product', string='Product')
    uom_id = fields.Many2one('product.uom', related='product_id.uom_id', string='Unit of  Measure', readonly=True)
    qty = fields.Integer(string='Qty')
    qty_max = fields.Integer(string='Qty max')
    note = fields.Char(string='Note')
    pos_order_id = fields.Many2one('pos.order', string='Pos Order')


class ProductProduct(models.Model):
    _inherit = 'product.product'

    @api.model
    def name_search(self, name='', args=None, operator='ilike', limit=100):
        products = super(ProductProduct, self).name_search(name, args, operator, limit)
        categ_id = self._context.get('categ_id', False)
        if categ_id:
            products = self.env['product.product'].search([('categ_id', '=', self._context['categ_id']), ('available_in_pos', '=', True)]).name_get()

        return products