# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo import time
from odoo.exceptions import except_orm
from odoo.osv import osv
import xlrd
import base64


class IziStockRequest(models.Model):
    _name = 'izi.stock.request'
    _order = 'date ASC'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char('Number', default=lambda self: _('New'))
    date = fields.Date('Date', default=lambda *a: time.strftime('%Y-%m-%d'))
    warehouse_id = fields.Many2one('stock.warehouse', string='Source warehouse')
    location_id = fields.Many2one('stock.location', string='Source location')
    des_warehouse_id = fields.Many2one('stock.warehouse', string='Destination warehouse')
    des_location_id = fields.Many2one('stock.location', string='Destination location')
    type = fields.Selection([('coordinator', 'Coordinator'), ('request', 'Request'), ])
    type_request = fields.Selection([('other', 'Other warehouses'), ('total', 'Total warehouse'), ], default='other')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('checked_inventory', 'Checked inventory'),
        ('ready', 'Ready'),
        ('done', 'done'),
        ('cancel', 'Cancel'),
    ], copy=False, store=True, default='draft')
    total_request = fields.Float('Total request', compute='_compute_total', store=True)
    total_confirm = fields.Float('Total confirm', compute='_compute_total', store=True)
    transfer_id = fields.Many2one('izi.stock.transfer',string='Transfer')
    note = fields.Text('Note')

    line_id = fields.One2many('izi.stock.request.line', 'request_id', string='Infomation')

    field_binary_import = fields.Binary(string="Field Binary Import")
    field_binary_name = fields.Char(string="Field Binary Name")

    @api.onchange('warehouse_id')
    def _onchange_wh(self):
        list= []
        if self.warehouse_id:
            locations = self.env['stock.location'].search([('location_id','=',self.warehouse_id.view_location_id.id),('usage','=','internal')])
            for location_id in locations:
                list.append(location_id.id)
        return {
            'domain': {'location_id': [('id', 'in', list)]}
        }

    @api.onchange('des_warehouse_id')
    def _onchange_wh_des(self):
        list = []
        if self.des_warehouse_id:
            locations = self.env['stock.location'].search(
                [('location_id', '=', self.des_warehouse_id.view_location_id.id), ('usage', '=', 'internal')])
            for location_id in locations:
                list.append(location_id.id)
        return {
            'domain': {'des_location_id': [('id', 'in', list)]}
        }

    @api.depends('line_id.qty', 'line_id.qty_confirm')
    def _compute_total(self):
        for s in self:
            total_request = total_confirm = 0.0
            for line in s.line_id:
                total_request += line.qty
                total_confirm += line.qty_confirm
            s.total_request = total_request
            s.total_confirm = total_confirm

    @api.multi
    def action_send(self):
        if not self.line_id:
            raise except_orm('Cảnh báo!', (
                "Không có sản phẩm yêu cầu"))
        if self.state == 'draft':
            for line in self.line_id:
                if line.qty == 0:
                    raise except_orm('Cảnh báo!', (
                        "Bạn chưa nhập số lượng yêu cầu."))
            self.state = 'checked_inventory'
        else:
            return True

    @api.multi
    def action_assign(self):
        self.action_send()
        check = 0
        for line in self.line_id:
            if line.product_id.type == 'service':
                raise except_orm('Cảnh báo!', (
                        "Sản phẩm %s là dịch vụ." % line.product_id.product_tmpl_id.name))
            total_availability = self.env['stock.quant']._get_available_quantity(line.product_id, self.location_id)
            line.reserved_availability = total_availability
            if line.reserved_availability > 0:
                check += 1
        if check == len(self.line_id):
            for line in self.line_id:
                line.qty_confirm = line.qty
            self.state = 'ready'
        else:
            return True

    @api.multi
    def action_back(self):
        for line in self.line_id:
            line.qty_confirm = 0
            line.reserved_availability = 0
        self.state = 'checked_inventory'

    @api.multi
    def action_transfer(self):
        for line in self.line_id:
            if line.qty_confirm == 0:
                raise except_orm('Cảnh báo!', (
                    "Bạn chưa nhập số lượng phê duyệt."))
        transfer_obj = self.env['izi.stock.transfer']
        transfer_line_obj = self.env['izi.stock.transfer.line']
        picking_id = self.env['stock.picking.type'].search(
            [('code', '=', 'internal'), ('default_location_src_id', '=', self.location_id.id),
             ('default_location_dest_id', '=', self.location_id.id)], limit=1).id
        picking_id_in = self.env['stock.picking.type'].search(
            [('code', '=', 'internal'), ('default_location_src_id', '=', self.des_location_id.id),
             ('default_location_dest_id', '=', self.des_location_id.id)], limit=1).id
        if picking_id == False :
            raise except_orm('Cảnh báo!', (
                "Xin hãy cấu hình loại điều chuyển kho xuất"))
        if picking_id_in == False:
            raise except_orm('Cảnh báo!', (
                "Xin hãy cấu hình loại điều chuyển kho nhập"))
        vals = {
            'warehouse_id': self.warehouse_id.id,
            'dest_warehouse_id': self.des_warehouse_id.id,
            'scheduled_date': self.date,
            'origin': self.name,
            'stock_picking_type': picking_id,
            'stock_picking_type_in': picking_id_in,
            'state': 'draft'
        }
        transfer_id = transfer_obj.create(vals)
        for line in self.line_id:
            if line.qty_confirm != 0:
                vals_line = {
                    'izi_stock_transfer_id': transfer_id.id,
                    'product_id': line.product_id.id,
                    'product_uom': line.uom_id.id,
                    'quantity_from': line.qty_confirm,
                    'state': 'draft',
                }
                transfer_line_id = transfer_line_obj.create(vals_line)
        self.transfer_id = transfer_id.id
        self.state = 'done'

    @api.multi
    def action_cancel(self):
        self.state = 'cancel'

    @api.multi
    def unlink(self):
        for line in self:
            if line.state != 'draft':
                raise except_orm('Thông báo!', (
                    "Không thể xóa bản ghi ở trạng thái khác bản thảo"))
        return super(IziStockRequest, self).unlink()

    @api.model
    def create(self, vals):
        if vals.get('name', _('New')) == _('New'):
            vals['name'] = self.env['ir.sequence'].next_by_code('izi.stock.request') or _('New')
        return super(IziStockRequest, self).create(vals)


    def _check_format_excel(self, file_name):
        if file_name == False:
            return False
        if file_name.endswith('.xls') == False and file_name.endswith('.xlsx') == False:
            return False
        return True

    @api.multi
    def action_import_line(self):
        try:
            if not self._check_format_excel(self.field_binary_name):
                raise osv.except_osv("Cảnh báo!",
                                     (
                                         "File không được tìm thấy hoặc không đúng định dạng. Vui lòng kiểm tra lại định dạng file .xls hoặc .xlsx"))
            data = base64.decodestring(self.field_binary_import)
            excel = xlrd.open_workbook(file_contents=data)
            sheet = excel.sheet_by_index(0)
            index = 3
            lines = []
            while index < sheet.nrows:
                product_code = sheet.cell(index, 1).value
                product_obj = self.env['product.product'].search([('default_code', '=', product_code)])
                if product_obj.id == False:
                    raise except_orm('Cảnh báo!',
                                     ("Không tồn tại sản phẩm có mã " + str(
                                         product_code) + ". Vui lòng kiểm tra lại dòng " + str(
                                         index + 1)))
                else:
                    product_id = product_obj[0].id
                    uom_id = product_obj[0].product_tmpl_id.uom_id.id
                qty = sheet.cell(index, 4).value
                note = sheet.cell(index, 5).value
                argvs_request = {
                    'product_id': product_id,
                    'uom_id': uom_id,
                    'qty': qty,
                    'note': note,
                    'request_id': self.id
                }
                argvs_coordinator = {
                    'product_id': product_id,
                    'uom_id': uom_id,
                    'qty_confirm': qty,
                    'note': note,
                    'request_id': self.id
                }
                if self.type == 'coordinator':
                    lines.append(argvs_coordinator)
                else:
                    lines.append(argvs_request)
                index = index + 1
            self.line_id = lines
            self.field_binary_import = None
            self.field_binary_name = None
        except ValueError as e:
            raise osv.except_osv("Warning!",
                                 (e))

    @api.multi
    def download_template(self):
        return {
            "type": "ir.actions.act_url",
            "url": '/izi_stock_request/static/template/import_izi_stock_request.xlsx',
            "target": "_parent",
        }
