# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.tools.float_utils import float_compare, float_is_zero, float_round
from odoo.exceptions import UserError, AccessError, except_orm
from odoo.osv import osv
import xlrd
import base64


class izi_stock_transfer(models.Model):
    _name = 'izi.stock.transfer'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char('Transfer Code', track_visibility='onchange', default=lambda self: _('New'))
    warehouse_id = fields.Many2one('stock.warehouse', 'Source Warehouse', track_visibility='onchange')
    dest_warehouse_id = fields.Many2one('stock.warehouse', 'Destination Warehouse', track_visibility='onchange')
    scheduled_date = fields.Datetime('Scheduled Date', track_visibility='onchange', default=fields.Datetime.now)
    origin = fields.Char('Source document', track_visibility='onchange')
    owner_id = fields.Many2one('res.partner', 'Owner', track_visibility='onchange')
    company_id = fields.Many2one('res.company', 'Company',
                                 default=lambda self: self.env['res.company']._company_default_get('izi.stock.transfer'),
                                 index=True, required=True)
    stock_picking_type = fields.Many2one('stock.picking.type', 'Operation Type', track_visibility='onchange')

    stock_picking_type_in = fields.Many2one('stock.picking.type', 'Operation Type', track_visibility='onchange')

    location_id = fields.Many2one('stock.location', 'Source Location', )
    dest_location_id = fields.Many2one('stock.location', 'Destination Location', track_visibility='onchange')
    transfer_line = fields.One2many('izi.stock.transfer.line', 'izi_stock_transfer_id', 'Operations', track_visibility='onchange')

    state = fields.Selection([('draft', 'Draft'), ('waiting', 'Waiting Another Operation'), ('confirmed', 'Waiting'),
                              ('assigned', 'Ready'), ('transfer', 'Transfering'), ('done', 'Done'), ('cancel', 'Cancel')], 'State',
                             track_visibility='onchange',
                             default="draft")
    date_receive = fields.Datetime('Received Date')
    stock_picking_from = fields.Many2one('stock.picking', 'Stock picking from')
    stock_picking_to = fields.Many2one('stock.picking', 'Stock picking to')

    move_lines_from = fields.One2many('stock.move', 'x_transfer_from_id', 'Operations', track_visibility='onchange')
    move_lines_to = fields.One2many('stock.move', 'x_transfer_to_id', 'Operations', track_visibility='onchange')
    field_binary_import = fields.Binary(string="Field Binary Import")
    field_binary_name = fields.Char(string="Field Binary Name")

    show_check_availability = fields.Boolean(
        compute='_compute_show_check_availability',
        help='Technical field used to compute whether the check availability button should be shown.')

    @api.multi
    def _compute_show_check_availability(self):
        for picking in self.stock_picking_from:
            self.show_check_availability = picking.show_check_availability

    @api.multi
    def action_confirm(self):
        if len(self.transfer_line) == 0:
            raise UserError(_('Không có dữ liệu chi tiết'))

        if self.stock_picking_type.default_location_src_id.id == False:
            raise UserError(_("Chưa cấu hình địa điểm xuất trong kho. Xin hãy liên hệ với người quản trị"))
        self.location_id = self.stock_picking_type.default_location_src_id.id
        for line in self.transfer_line:
            if line.quantity_from == 0:
                raise UserError(_('Bạn chưa nhập số lượng cần xuất'))
            total_availability = self.env['stock.quant']._get_available_quantity(line.product_id, self.stock_picking_type.default_location_src_id)
            if line.quantity_from > total_availability:
                raise UserError(_(
                    'Sản phẩm %s hiện không đủ hàng. Vui lòng dịch chuyển %s SLDV sản phẩm này đến kho %s' % (str(line.product_id.name),str(line.quantity_from - total_availability),str(self.stock_picking_type.default_location_src_id.name))))
        if self.stock_picking_type_in.default_location_dest_id.id == False:
            raise UserError(_("Chưa cấu hình địa điểm nhận trong kho. Xin hãy liên hệ với người quản trị"))

        if self.dest_warehouse_id.x_wh_transfer_loc_id.id == False:
            raise UserError(_("Chưa cấu hình địa điểm trung chuyển hàng hóa trong kho. Xin hãy liên hệ với người quản trị"))

        self.dest_location_id = self.stock_picking_type_in.default_location_dest_id.id

        if self.stock_picking_from.id == False or self.stock_picking_from.state == 'cancel':
            picking_id = self._create_picking(self.stock_picking_type.id, self.dest_warehouse_id.x_wh_transfer_loc_id.id, self.location_id.id)
            if picking_id.id == False:
                raise UserError(_("Không xác nhận được phiếu chuyển kho. Xin hãy liên hệ với người quản trị"))
            self.update({'stock_picking_from': picking_id.id})
            # Xác nhận picking
            picking_id.action_confirm()
        else:
            self.stock_picking_from.action_confirm()
        self._get_reserved()
        self.state = 'confirmed'

    @api.multi
    def action_assign(self):
        self.ensure_one()
        if self.state != 'waiting':
            for line in self.stock_picking_from.move_lines:
                line.product_uom_qty = line.x_transfer_line_id.quantity_from
        self.stock_picking_from.action_assign()
        self._get_reserved()
        self.state = self._check_ready()

    @api.multi
    def _create_picking(self, picking_type_id, location_dest_id, location_id, check_transfer=True):
        StockPicking = self.env['stock.picking']
        for transfer in self:
            if any([ptype in ['product', 'consu'] for ptype in transfer.transfer_line.mapped('product_id.type')]):
                res = transfer._prepare_picking(picking_type_id, location_dest_id, location_id)
                picking = StockPicking.create(res)
                moves = transfer.transfer_line._create_stock_moves(picking, check_transfer)
                picking.message_post_with_view('mail.message_origin_link',
                                               values={'self': picking, 'origin': transfer},
                                               subtype_id=self.env.ref('mail.mt_note').id)
        return picking

    @api.model
    def _prepare_picking(self, picking_type_id, location_dest_id, location_id):
        return {
            'picking_type_id': picking_type_id,
            'date': self.scheduled_date,
            'origin': self.name,
            'location_dest_id': location_dest_id,
            'location_id': location_id,
            'company_id': self.company_id.id,
        }

    @api.multi
    def action_cancel(self):
        self.stock_picking_from.action_cancel()
        self.state = self.stock_picking_from.state

    def _check_ready(self):
        if self.stock_picking_from.state == 'assigned':
            if self.show_check_availability:
                return self.stock_picking_from.state
            else:
                return 'waiting'
        else:
            return 'waiting'

    def _get_reserved(self):
        self.ensure_one()
        for line in self.stock_picking_from.move_lines:
            line.x_transfer_line_id.reserved_availability = line.reserved_availability
            line.product_uom_qty = line.x_transfer_line_id.quantity_from

    @api.multi
    def action_transfer(self):
        if self.state == 'transfer':
            return True
        for line in self.stock_picking_from.move_lines:
            if len(line.move_line_ids) != 0:
                for m_line in line.move_line_ids:
                    if m_line.qty_done == 0:
                        m_line.qty_done = m_line.product_uom_qty
            line.product_uom_qty = line.x_transfer_line_id.quantity_from

        self.stock_picking_from.button_validate()
        if self.stock_picking_from.state == 'done':
            picking_id = self._create_picking(self.stock_picking_type_in.id, self.dest_location_id.id, self.dest_warehouse_id.x_wh_transfer_loc_id.id,
                                              False)
            if picking_id.id == False:
                raise UserError(_("Không xác nhận được phiếu chuyển kho. Xin hãy liên hệ với người quản trị"))
            self.update({'stock_picking_to': picking_id.id})
            picking_id.action_assign()
            self.state = 'transfer'

    @api.multi
    def action_receive(self):
        for line in self.move_lines_to:
            if line.quantity_done == 0:
                raise except_orm(_('Thông báo'), _('Bạn chưa nhập số lượng hàng nhập về!'))
        if self.stock_picking_to.state == 'done':
            self.state = self.stock_picking_to.state
        else:
            self.stock_picking_to.action_assign()
            self.stock_picking_to.button_validate()
            if self.stock_picking_to.state == 'done':
                self.state = self.stock_picking_to.state
            else:
                args_backorder = {
                    'pick_ids': [(6, 0, self.stock_picking_to.ids)]
                }
                backorder_id = self.env['stock.backorder.confirmation'].create(args_backorder)
                backorder_id.process_cancel_backorder()
                self.state = self.stock_picking_to.state

    @api.model
    def create(self, vals):
        if vals.get('name', _('New')) == _('New'):
            if 'company_id' in vals:
                vals['name'] = self.env['ir.sequence'].with_context(force_company=vals['company_id']).next_by_code('izi.stock.transfer') or _('New')
            else:
                vals['name'] = self.env['ir.sequence'].next_by_code('izi.stock.transfer') or _('New')
        return super(izi_stock_transfer, self).create(vals)

    @api.multi
    def unlink(self):
        if self.state == 'draft':
            return super(izi_stock_transfer, self).unlink()
        raise UserError(_('Thông báo'), _('Bạn chỉ có thể xóa khi ở trạng thái Nháp'))

    @api.multi
    def write(self, vals):
        if len(vals) > 0:
            self.create_log(vals)
        return super(izi_stock_transfer, self).write(vals)

    @api.multi
    def action_back(self):
        if self.state != 'draft':
            self.state = 'draft'
        if self.stock_picking_from.id != False:
            self.stock_picking_from.action_cancel()
            self.stock_picking_from.state = 'draft'
            for line_move in self.stock_picking_from.move_lines:
                line_move.state = 'draft'
            self.stock_picking_from.unlink()

    @api.multi
    def create_log(self, vals):
        mail_message_obj = self.env['mail.message']
        id = self.id
        user = self.env['res.users'].browse([self._uid])
        partner_id = user.partner_id
        subtype_id = 2
        subtype = self.env['mail.message.subtype'].browse([subtype_id])
        if len(subtype) == 0:
            subtype = self.env['mail.message.subtype'].search([('name', '=', 'Note')])
            if len(subtype) > 0:
                subtype_id = subtype[0].id
            else:
                subtype_id = 0
        body = ""
        for val in vals:
            if val == 'state':
                a = ''
                b = ''
                if self.state == 'draft':
                    a = 'Bản thảo'
                if self.state == 'waiting':
                    a = 'Kiểm tồn'
                if self.state == 'confirmed':
                    a = 'Xác nhận'
                if self.state == 'assigned':
                    a = 'Giao hàng'
                if self.state == 'transfer':
                    a = 'Đang dịch chuyển'
                if self.state == 'done':
                    a = 'Hoàn thành'
                if self.state == 'cancel':
                    a = 'Hủy'

                if vals.get('state') == 'draft':
                    b = 'Bản thảo'
                if vals.get('state') == 'waiting':
                    b = 'Kiểm tồn'
                if vals.get('state') == 'confirmed':
                    b = 'Xác nhận'
                if vals.get('state') == 'assigned':
                    b = 'Giao hàng'
                if vals.get('state') == 'transfer':
                    b = 'Đang dịch chuyển'
                if vals.get('state') == 'done':
                    b = 'Hoàn thành'
                if vals.get('state') == 'cancel':
                    b = 'Hủy'
                bd = "<p>Chuyển trạng thái " + a + " -> " + b + "</p>"
                body = body + bd
        if len(body) > 0:
            bd = "<p>Thời gian " + str(fields.Datetime.now()) + " </p>"
            body = body + bd
            vals_mail_message = {
                'model': 'izi.stock.transfer',
                'email_from': partner_id.name or '' + ' <' + partner_id.email or '' + '>',
                'reply_to': partner_id.name or '' + ' <' + partner_id.email or '' + '>',
                'message_type': 'notification',
                'date': fields.Datetime.now(),
                'res_id': id,
                'subtype_id': subtype_id,
                'record_name': self.name or 'no_message',
                'author_id': partner_id.id,
                'body': body
            }
            parent = mail_message_obj.search(
                [('model', '=', 'izi.stock.transfer'), ('res_id', '=', self.id), ('parent_id', '=', False)],
                limit=1)
            if len(parent) > 0:
                vals_mail_message['parent_id'] = parent[0].id
            mail_id = mail_message_obj.create(vals_mail_message)

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
                    product_lot_id = self.env['stock.production.lot'].search([('name', '=', product_code.upper())], limit=1)
                    if product_lot_id.id != False:
                        product_id = product_lot_id.product_id.id
                        uom_id = product_lot_id.product_id.product_tmpl_id.uom_id.id
                    else:
                        raise except_orm('Cảnh báo!',
                                         ("Không tồn tại sản phẩm có mã " + str(
                                             product_code) + ". Vui lòng kiểm tra lại dòng " + str(
                                             index + 1)))
                else:
                    product_id = product_obj[0].id
                    uom_id = product_obj[0].product_tmpl_id.uom_id.id
                qty = sheet.cell(index, 4).value
                note = sheet.cell(index, 5).value
                argvs = {
                    'product_id': product_id,
                    'product_uom': uom_id,
                    'quantity_from': qty,
                    'note': note,
                    'izi_stock_transfer_id': self.id
                }
                lines.append(argvs)
                index = index + 1
            self.transfer_line = lines
            self.field_binary_import = None
            self.field_binary_name = None
        except ValueError as e:
            raise osv.except_osv("Warning!",
                                 (e))

    @api.multi
    def download_template(self):
        return {
            "type": "ir.actions.act_url",
            "url": '/izi_stock_transfer/static/template/import_izi_stock_transfer.xlsx',
            "target": "_parent",
        }

    @api.onchange('warehouse_id')
    def _onchange_warehouse_id(self):
        for line in self:
            if line.warehouse_id.id != False:
                line.stock_picking_type = line.warehouse_id.x_int_type_id.id

    @api.onchange('dest_warehouse_id')
    def _onchange_dest_warehouse_id(self):
        for line in self:
            if line.dest_warehouse_id.id != False:
                line.stock_picking_type_in = line.dest_warehouse_id.x_int_type_id.id

