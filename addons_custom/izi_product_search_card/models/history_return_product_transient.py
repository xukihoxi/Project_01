from odoo import models, fields, api
from datetime import datetime
from odoo.exceptions import UserError, MissingError, ValidationError
from datetime import date, datetime
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT


class ReturnProductHistory(models.TransientModel):
    _name = 'return.product.transient'
    _description = u'Lịch sử trả nợ hàng'
    _order = 'create_date desc'

    x_search_id = fields.Many2one('izi.product.search.card')
    picking_id = fields.Many2one('stock.picking', String = "Picking")
    debit_good_id = fields.Many2one('pos.debit.good', String = 'Debit Good')

#     Sangla thêm ngay5/3/2019
# Thêm chi tiết lích sử trả hàng cho khách hàng
    product_id = fields.Many2one('product.product', "Product")
    quantity_done = fields.Float("Quantity Done")
    product_uom = fields.Many2one('product.uom', "Product Uom")
    scheduled_date = fields.Datetime("Scheduled Date")
