# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError, AccessError,except_orm
from odoo.osv import osv
import xlrd
import base64


class StockInventoryCustom(models.Model):
    _inherit = 'stock.inventory'

    @api.model
    def _default_warehouse_id(self):
        company_user = self.env.user.company_id
        warehouse = self.env['stock.warehouse'].search([('company_id', '=', company_user.id)], limit=1)
        if warehouse:
            return warehouse.id
        else:
            raise UserError(_('You must define a warehouse for the company: %s.') % (company_user.name,))

    warehouse_id = fields.Many2one('stock.warehouse', string="Warehouse",default=_default_warehouse_id)
    field_binary_import = fields.Binary(string="Field Binary Import")
    field_binary_name = fields.Char(string="Field Binary Name")

    def _check_format_excel(self, file_name):
        if file_name == False:
            return False
        if file_name.endswith('.xls') == False and file_name.endswith('.xlsx') == False:
            return False
        return True

    @api.onchange('warehouse_id')
    def _onchange_location(self):
        kip = []
        if self.warehouse_id:
            view_location_id = self.warehouse_id.view_location_id.id
            location_id = self.env['stock.location'].search(
                [('usage', '=', 'internal'), ('location_id', '=', view_location_id)])
            for locat in location_id:
                kip.append(locat.id)
            self.location_id = location_id[0].id
        return {
            'domain': {'location_id': [('id', 'in', kip)]}
        }

    @api.multi
    def action_import_line(self):
        if self.field_binary_name is None:
            raise except_orm('Cảnh báo', 'Không tìm thấy file import. Vui lòng chọn lại file import.')
        try:
            if not self._check_format_excel(self.field_binary_name):
                raise osv.except_osv("Cảnh báo!",
                                     (
                                         "File không được tìm thấy hoặc không đúng định dạng. Vui lòng kiểm tra lại định dạng file .xls hoặc .xlsx"))
            data = base64.decodestring(self.field_binary_import)
            excel = xlrd.open_workbook(file_contents=data)
            sheet = excel.sheet_by_index(0)
            index = 4
            lines = []
            stock_inventory_line_obj = self.env['stock.inventory.line']
            while index < sheet.nrows:
                product_code = sheet.cell(index, 0).value
                product_obj = self.env['product.product'].search([('default_code', '=', product_code)])
                if product_obj.id == False:
                    raise except_orm('Cảnh báo!',
                                     ("Không tồn tại sản phẩm có mã " + str(
                                         product_code) + ". Vui lòng kiểm tra lại dòng " + str(
                                         index + 1)))
                else:
                    if product_obj[0].type == 'service':
                        raise except_orm('Cảnh báo!',
                                         ("Sản phẩm có " + str(
                                             product_code) + " là dịch vụ. Vui lòng kiểm tra lại dòng " + str(
                                             index + 1)))
                    product_id = product_obj[0].id
                    uom_id = product_obj[0].product_tmpl_id.uom_id.id
                product_qty = sheet.cell(index, 4).value
                theoretical_qty = sheet.cell(index, 3).value
                note = sheet.cell(index, 5).value
                # lot_name = str(sheet.cell(index, 3).value.split())
                # if len(lot_name) or lot_name != '' or lot_name != False:
                #     inventory_line_id = stock_inventory_line_obj.search([('inventory_id','=',self.id),('product_id','=',product_id),('product_uom_id','=',uom_id),
                #                                                             ('prod_lot_id.name','=',lot_name),('location_id','=',self.location_id.id)])
                # else:
                inventory_line_id = stock_inventory_line_obj.search(
                    [('inventory_id', '=', self.id), ('product_id', '=', product_id),
                     ('product_uom_id', '=', uom_id),('location_id', '=', self.location_id.id)])
                if len(inventory_line_id) == 0:
                    # if len(lot_name) or lot_name != '' or lot_name != False:
                    #     lot = self.env['stock.production.lot'].search([('name','=',lot_name),('product_id','=',product_id)])
                    #     if lot.id == False:
                    #         lot_id = self.env['stock.production.lot'].create({'name': lot_name, 'product_id': product_id})
                    #     else:
                    #         lot_id = lot
                    #     argvs = {
                    #         'product_id': product_id,
                    #         'product_uom_id': uom_id,
                    #         'location_id': self.location_id.id,
                    #         'prod_lot_id': lot_id.id,
                    #         'product_qty': product_qty,
                    #         'inventory_id': self.id
                    #     }
                    #     stock_inventory_line_obj.create(argvs)
                    # else:
                    argvs = {
                        'product_id': product_id,
                        'product_uom_id': uom_id,
                        'location_id': self.location_id.id,
                        'product_qty': product_qty,
                        'inventory_id': self.id,
                        'x_note': note,
                    }
                    stock_inventory_line_obj.create(argvs)
                else:
                    inventory_line_id = inventory_line_id[0]
                    inventory_line_id.update({
                        'product_qty': product_qty,
                        'x_note': note,
                    })
                index = index + 1
            self.field_binary_import = None
            self.field_binary_name = None
        except ValueError as e:
            raise osv.except_osv("Warning!",
                                 (e))

    @api.multi
    def download_template(self):
        return {
            "type": "ir.actions.act_url",
            "url": '/izi_stock_check_inventory/static/template/import_izi_stock_inventory.xlsx',
            "target": "_parent",
        }
