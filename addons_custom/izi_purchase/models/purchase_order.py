# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError, AccessError, except_orm


class purchase_order(models.Model):
    _inherit = 'purchase.order'

    READONLY_STATES = {
        'purchase': [('readonly', True)],
        'done': [('readonly', True)],
        'cancel': [('readonly', True)],
    }

    @api.model
    def _default_picking_type(self):
        type_obj = self.env['stock.picking.type']
        Warehouse = self.env['stock.warehouse']
        branch = self.env.user.branch_id
        # if not branch: raise except_orm('ngadv', 'ngadv')
        if not branch: raise except_orm('Thông báo', 'Tài khoản người dùng của bạn chưa chọn chi nhánh, không thể mua hàng.')

        warehouses = Warehouse.search([('branch_id', '=', branch.id)])
        if len(warehouses) > 1:
            str_warehouses = ''
            for warehouse in warehouses:
                str_warehouses += '%s,' % (str(warehouse.name))
            raise except_orm('Thông báo', 'Tài khoản người dùng của bạn đang chịu tránh nhiệm chi nhánh %s, '
                             'chi nhánh này đang tham chiếu đến %s kho (%s), '
                             'vui lòng kiểm tra lại' % (str(branch.name), str(len(warehouses), str(str_warehouses))))
        if not warehouses:
            raise except_orm('Thông báo', 'Tài khoản người dùng của bạn đang chịu trách nhiệm chi nhánh %s, chi nhánh đó đang không tham chiếu đến kho nào!' % (str(branch.name)))
        return warehouses.in_type_id

    picking_type_id = fields.Many2one('stock.picking.type', 'Deliver To', states=READONLY_STATES, required=True, default=_default_picking_type, help="This will determine operation type of incoming shipment")