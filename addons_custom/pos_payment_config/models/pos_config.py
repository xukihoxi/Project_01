# -*- coding: utf-8 -*-
from odoo import fields, models


class PosConfig(models.Model):
    _inherit = 'pos.config'

    # Phương thức thanh toán ghi nợ
    journal_debt_id = fields.Many2one('account.journal', 'Thanh toán ghi nợ', help='Phương thức thanh toán Ghi nợ')
    # Phương thức thanh toán thẻ tiền
    journal_vm_id = fields.Many2one('account.journal', 'Phương thức thẻ tiền', help='Phương thức thanh toán Thẻ tiền')
    # Các phương thức thanh toán được phép sử dụng khi mua thẻ tiền
    journal_vm_ids = fields.Many2many('account.journal', 'journal_vm_rel', string='Thanh toán thẻ tiền',
                                      domain=[('journal_user', '=', True)],
                                      help='Các phương thức thanh toán được phép sử dụng khi mua thẻ tiền')
    # Các phương thức thanh toán được tính doanh thu
    journal_loyal_ids = fields.Many2many('account.journal', 'journal_loyal_rel', string='Ghi nhận doanh thu',
                                         domain=[('journal_user', '=', True)],
                                         help='Các phương thức thanh toán được tính doanh thu')
    # dat coc
    journal_deposit_ids = fields.Many2many('account.journal', 'pos_config_journal_deposit_rel', 'pos_config_id',
                                           'journal_deposit_id',
                                           domain="[('journal_user', '=', True ), ('type', 'in', ['bank', 'cash'])]",
                                           string='Phương thức đặt cọc',
                                           help='Các phương thức được phép sử dụng khi đặt cọc')

    journal_deposit_id = fields.Many2one('account.journal', 'Phương thức ghi nhận đặt cọc')
    # Các phương thức chiết khấu ngoại lệ
    journal_exception_ids = fields.Many2many('account.journal', 'journal_exception_rel', string="Journal Exxeption", domain=[('journal_user', '=', True)], help='Payment method exception')
    x_charge_refund_id = fields.Many2one('product.product', "Charge Refund")

    # Các phương thức thanh toán công nợ được cho phép
    journal_pay_debt_ids = fields.Many2many('account.journal', 'pos_config_journal_pay_debt_rel', 'config_id',
                                           'journal_id',
                                           domain="[('journal_user', '=', True )]",
                                           string='Phương thức thanh toán nợ',
                                           help='Các phương thức được phép sử dụng khi thanh toán công nợ')
    # Cấu hình các dịch vụ được phép sửa giá như phí ship phí bệnh viên
    product_edit_price_ids = fields.Many2many('product.product', 'product_product_pos_config_rel', 'config_id', 'product_id',
                                          doamin="[('type', '=', 'service')]",
                                          string='Các chi phí khác như ship,..',
                                          help='Các chi phí khácn như phí ship')

