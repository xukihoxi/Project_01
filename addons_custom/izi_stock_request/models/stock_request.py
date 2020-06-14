# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo import time
from odoo.exceptions import except_orm
from odoo.osv import osv
import xlrd
import base64


class StockRequest(models.Model):
    _name = 'stock.request'
    _order = 'date ASC'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char('Number', default=lambda self: _('New'))
    date = fields.Date('Date', default=fields.Date.today(), track_visibility='onchange')
    date_confirm = fields.Date('Date confirm', track_visibility='onchange')
    branch_id = fields.Many2one('res.branch', string='Source Branch', track_visibility='onchange')
    warehouse_id = fields.Many2one('stock.warehouse', string='Source warehouse', track_visibility='onchange')
    location_id = fields.Many2one('stock.location', string='Source location', track_visibility='onchange')
    dest_branch_id = fields.Many2one('res.branch', string='Destination Branch', track_visibility='onchange')
    dest_warehouse_id = fields.Many2one('stock.warehouse', string='Destination warehouse', track_visibility='onchange')
    dest_location_id = fields.Many2one('stock.location', string='Destination location', track_visibility='onchange')
    type = fields.Selection([('coordinator', 'Coordinator'), ('request', 'Request')])
    state = fields.Selection([
        ('draft', 'Draft'),
        ('wait_confirm', 'Wait Confirm'),
        ('checked_inventory', 'Checked inventory'),
        ('ready', 'Ready'),
        ('done', 'done'),
        ('cancel', 'Cancel'),
    ], copy=False, store=True, default='draft')
    transfer_id = fields.Many2one('stock.transfer',string='Transfer', track_visibility='onchange')
    note = fields.Text('Note', track_visibility='onchange')
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.user.company_id)
    line_ids = fields.One2many('stock.request.line', 'request_id', string='Infomation')

    field_binary_import = fields.Binary(string="Field Binary Import")
    field_binary_name = fields.Char(string="Field Binary Name")

    @api.onchange('warehouse_id')
    def _onchange_warehouse_id(self):
        if self.warehouse_id:
            self.branch_id = self.warehouse_id.branch_id.id

    @api.onchange('dest_warehouse_id')
    def _onchange_dest_warehouse_id(self):
        if self.dest_warehouse_id:
            self.dest_branch_id = self.dest_warehouse_id.branch_id.id

    @api.multi
    def action_send(self):
        if self.state != 'draft':
            return True
        if not self.line_ids:
            raise except_orm('Cảnh báo!', (
                "Không có sản phẩm yêu cầu"))
        for line in self.line_ids:
            if line.qty == 0:
                raise except_orm('Cảnh báo!', (
                    "Bạn chưa nhập số lượng yêu cầu."))
        if self.warehouse_id.id == self.dest_warehouse_id.id:
            raise except_orm('Cảnh báo!', (
                "Vui lòng chọn 2 kho khác nhau"))
        self.state = 'wait_confirm'

    @api.multi
    def action_confirm(self):
        if self.state != 'wait_confirm':
            return True
        self.state = 'checked_inventory'

    @api.multi
    def action_assign(self):
        if self.state != 'checked_inventory':
            return True
        for line in self.line_ids:
            total_availability = self.env['stock.quant']._get_available_quantity(line.product_id, self.location_id)
            line.reserved_availability = total_availability
        if all([x.reserved_availability >= x.qty for x in self.line_ids]):
            for line in self.line_ids:
                line.qty_confirm = line.qty
            self.state = 'ready'
        else:
            raise except_orm('Thông báo', 'Không đủ sản phẩm trong kho hàng')

    @api.multi
    def action_back(self):
        if self.state == 'wait_confirm':
            self.state = 'draft'
        else:
            for line in self.line_ids:
                line.qty_confirm = 0
            self.state = 'checked_inventory'

    @api.multi
    def action_transfer(self):
        if self.state != 'ready':
            return True
        if all([x.qty_confirm <= 0 for x in self.line_ids]):
            raise except_orm('Cảnh báo!', ("Vui lòng nhập số lượng cho sản phẩm phê duyệt."))
        self.update({'date_confirm': fields.Date.today()})
        transfer_obj = self.env['stock.transfer']
        transfer_line_obj = self.env['stock.transfer.line']
        vals = {
            'branch_id': self.branch_id.id,
            'warehouse_id': self.warehouse_id.id,
            'dest_branch_id': self.dest_branch_id.id,
            'dest_warehouse_id': self.dest_warehouse_id.id,
            'location_id': self.location_id.id,
            'dest_location_id': self.dest_location_id.id,
            'scheduled_date': self.date_confirm,
            'origin': self.name,
            'state': 'draft'
        }
        transfer_id = transfer_obj.create(vals)
        for line in self.line_ids:
            if line.qty_confirm > 0:
                vals_line = {
                    'stock_transfer_id': transfer_id.id,
                    'product_id': line.product_id.id,
                    'product_uom': line.uom_id.id,
                    'qty': line.qty_confirm,
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
        return super(StockRequest, self).unlink()

    @api.model
    def create(self, vals):
        if vals.get('name', _('New')) == _('New'):
            vals['name'] = self.env['ir.sequence'].next_by_code('stock.request') or _('New')
        return super(StockRequest, self).create(vals)


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
            self.line_ids = lines
            self.field_binary_import = None
            self.field_binary_name = None
        except ValueError as e:
            raise osv.except_osv("Warning!",
                                 (e))

    @api.multi
    def download_template(self):
        return {
            "type": "ir.actions.act_url",
            "url": '/izi_stock_request/static/template/import_stock_request.xlsx',
            "target": "_parent",
        }
