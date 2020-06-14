# -*- coding: utf-8 -*-

from odoo import models, fields, api,_
from datetime import datetime
from odoo.exceptions import ValidationError, RedirectWarning, except_orm
from datetime import date, datetime
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from odoo.tools import mute_logger
import logging


_logger = logging.getLogger('base.partner.merge')
def get_sequence(cr, uid, code):
    env = api.Environment(cr, uid, {})
    ir_sequence = env['ir.sequence']
    today = date.today()
    this_month_str = today.strftime('%y%m')
    sequence_name = code + this_month_str
    sequence_value = ir_sequence.get(sequence_name)
    if not sequence_value:
        # _logger.info("Now create a new sequence")
        args = {
            'name': sequence_name,
            'code': sequence_name,
            'implementation': 'no_gap',
            'padding': 4
        }
        ir_sequence.create(args)
        sequence_value = ir_sequence.get(sequence_name)
    # else:
        # _logger.info("Oh I got a sequence value")

    # _logger.info("Sequence value = " +str(sequence_value))

    return sequence_name + '/' + sequence_value


class StockPickingReason(models.Model):
    _name = "stock.picking.reason"
    name = fields.Char(string="Value")
    code = fields.Integer(string="Code")
    description = fields.Char("Description")
    in_or_out = fields.Selection(selection=(
        ('internal_in', 'Internal receipt'), ('internal_out', 'Internal delivery'),
        ('external_out', 'Product delivery')),
        string="Type of transfer")
    # account = fields.Char(string="Account", size=6, help="Account")
    account = fields.Many2one('account.account', "Account")




class EvStockMove(models.Model):
    _inherit = 'stock.move'

    account_id = fields.Many2one('account.account', 'Account')
    promotion_id = fields.Many2one('sale.promotion.reason', 'Promotion reason')
    debit_owner_id = fields.Many2one('res.partner', 'Debit owner')

class ev_product_delivery(models.Model):
    _name = 'inventory.product.delivery'

    name = fields.Char("Name", default='/', readonly=True, copy=False)
    type = fields.Selection(string='Type', selection=[('in', 'Input'), ('out', 'Output')],
                            default='out', required=True)
    partner_id = fields.Many2one('res.partner', 'Receive unit', required=True)
    rec_partner_id = fields.Many2one('res.partner', 'Recipients')
    str_rec_partner = fields.Char('Recipients name')
    delivery_date = fields.Date("Inventory Date", required=True, default=fields.Date.context_today)
    location_id = fields.Many2one('stock.location', "Location", required=True, domain=[('x_code', '!=', '')])
    note = fields.Text("Note")
    delivery_lines = fields.One2many('product.delivery.line', 'transfer_id', copy=True)
    dest_location_id = fields.Many2one('stock.location', "Loss location", required=True,
                                       domain=[('usage', '!=', 'view'), ('x_code', '!=', 'NOCODE')])
    picking_id = fields.Many2one('stock.picking', "Stock picking", readonly=True, copy=False)
    is_loss = fields.Boolean('From/To loss', default=True)
    state = fields.Selection(selection=(('draft', 'Draft'),
                                        ('not_available', 'Not available'),
                                        ('partially_available', "Partially available"), ('confirm', 'Confirm'),
                                        ('ready', 'Ready to transfer'), ('done', 'Done')), default='draft', copy=False)

    _sql_constraints = [
        ('indx_inventory_product_delivery_unq', 'unique(name)', 'Mã phiếu xuất phải là duy nhất!')
    ]

    @api.model
    def get_loss_location(self):
        stock_location = self.env['stock.location']
        loss_location = stock_location.sudo().search([('x_code', '=', 'LOSS')])
        if not loss_location:
            _logger.info('Không tìm thấy kho Inventory loss (kho mất mát) trong hệ thống')
            # raise except_orm("LỖI CẤU HÌNH", "Không tìm thấy kho Inventory loss (kho mất mát) trong hệ thống.\n"
            #                                  "Xin hãy cấu hình 1 location với code = 'LOSS', type = 'inventory'")
        else:
            return loss_location[0].id

    _defaults = {
        'dest_location_id': get_loss_location,
    }

    @api.multi
    def action_confirm(self):
        if self.state == 'confirm':
            self.write({'state': 'ready'})

    @api.one
    def copy(self, default=None):
        default = dict(default or {})
        if default.get('type') == 'in':
            default.update({
                'state': 'ready',
            })
        return super(ev_product_delivery, self).copy(default)

    @api.model
    @api.returns('self', lambda value: value.id)
    def create(self, vals):
        if 'name' not in vals or vals['name'] == '/':
            dir_code = 'PXK'
            if vals.get('type') == 'in':
                dir_code = 'PNK'
                vals.update({
                    'is_loss': True,
                    'location_id': self.get_loss_location(),
                    'state': 'confirm',
                })
            else:
                vals.update({
                    'state': 'draft',
                })
            vals['name'] = get_sequence(self._cr, 1, dir_code)
        return super(ev_product_delivery, self).create(vals)

    @api.onchange('type')
    def _change_type(self):
        self.dest_location_id = False
        self.location_id = False
        if self.type == 'out':
            self.dest_location_id = self.get_loss_location()
            if self.partner_id:
                try:
                    location_obj = self.env['stock.location']
                    ids = location_obj.search(
                        [('partner_id', '=', self.partner_id.id), ('usage', '=', 'internal')])
                    if len(ids) > 0:
                        partner_location = location_obj.browse(ids[0])
                        if partner_location:
                            self.dest_location_id = partner_location.id
                            _logger.info('________________________________________________________ ')
                            _logger.info(partner_location)
                except(Warning, except_orm) as exc:
                    _logger.error(exc)
        elif self.type == 'in':
            self.location_id = self.get_loss_location()
            self.dest_location_id = False

    @api.onchange('is_loss')
    def _change_loss(self):
        if not self.is_loss:
            if self.type == 'out':
                self.dest_location_id = False
                if self.partner_id:
                    try:
                        location_obj = self.env['stock.location']
                        ids = location_obj.search(
                            [('partner_id', '=', self.partner_id.id), ('usage', '=', 'internal')])
                        if len(ids) > 0:
                            partner_location = location_obj.browse(ids[0])
                            if partner_location:
                                self.dest_location_id = partner_location.id
                                _logger.info('________________________________________________________ ')
                                _logger.info(partner_location)
                    except(Warning, except_orm) as exc:
                        _logger.error(exc)
            elif self.type == 'in':
                self.location_id = False
                self.dest_location_id = False
        else:
            if self.type == 'out':
                self.location_id = False
                self.dest_location_id = self.get_loss_location()
            else:
                self.location_id = self.get_loss_location()
                self.dest_location_id = False

    @api.onchange('rec_partner_id')
    def _onchange_rec_partner(self):
        if self.rec_partner_id and self.rec_partner_id.x_code == 'OTHER':
            self.str_rec_partner = False
        else:
            self.str_rec_partner = self.rec_partner_id.name

    @api.onchange('partner_id')
    def _onchange_partner(self):
        _logger.info('___________________ partner changed _____________________')
        if self.partner_id and not self.is_loss:
            try:
                location_obj = self.env['stock.location']
                ids = location_obj.search(
                    [('partner_id', '=', self.partner_id.id), ('usage', '=', 'internal')])
                if len(ids) > 0:
                    partner_location = location_obj.browse(ids[0])
                    if partner_location:
                        self.dest_location_id = partner_location.id
                        _logger.info('________________________________________________________ ')
                        _logger.info(partner_location)
            except(Warning, except_orm) as exc:
                _logger.error(exc)

    @api.multi
    def do_check_inventory(self):
        self.ensure_one()
        _logger.info('Do check inventory.................')
        if not self.delivery_lines or len(self.delivery_lines) == 0:
            raise except_orm("LỖI", "Xin hãy nhập ít nhất một sản phẩm để xử lý")
        state = 'available'
        for line in self.delivery_lines:
            line.state = 'ready'
            if self.type == 'out':
                line_state = line.check_availability()[0]
            else:
                line_state = 'available'
            _logger.info("Current state = " + str(state))
            _logger.info("line state = " + str(line_state))
            if line_state == 'not_available':
                if state == 'not_available':
                    _logger.info("Keep this state unchanged")
                elif state == 'partially_available':
                    _logger.info("Keep this state unchanged too")
                # state is currently 'available'
                else:
                    state = 'not_available'

            elif line_state == 'partially_available':
                if state == 'not_available':
                    state == line_state
                # if state == partially_available, no change is necessary
                elif state == 'available':
                    state = line_state

            elif line_state == 'available':
                _logger.info("Yeah, keep this state unchanged")

            _logger.info("==> now state = " + state + "\n")

        if state == 'available':
            state = 'confirm'
        self.state = state

    @api.multi
    def re_check_inventory(self):
        self.ensure_one()
        _logger.info('Do re check inventory.................')
        self.do_check_inventory()

    @api.multi
    def do_inventory_transfer(self):
        self.ensure_one()
        if not self.delivery_lines or len(self.delivery_lines) == 0:
            raise except_orm("LỖI", "Xin hãy nhập ít nhất một sản phẩm để xử lý")
        self.create_out_picking()
        self.state = 'done'

    # Xuất điều chỉnh
    def create_out_picking(self):
        cr, uid = self._cr, self._uid
        stock_picking_type = self.env['stock.picking.type']
        picking_reason = self.env['stock.picking.reason']
        stock_picking = self.env['stock.picking']

        if self.type == 'out':
            picking_type = stock_picking_type.sudo().search([('default_location_src_id', '=', self.location_id.id),
                                                             ('default_location_dest_id', '=', self.dest_location_id.id)])
            if len(picking_type)>0:
                picking_type = picking_type[0]
            else:
                picking_type = stock_picking_type.sudo().search([('default_location_src_id', '=', self.location_id.id)])
                if not picking_type or len(picking_type) == 0:
                    picking_type = stock_picking_type.create({'name': _('Xuất điều chỉnh kho: ') + _(self.location_id.name),
                                                              'sequence_id': 1361,
                                                              'default_location_dest_id': self.dest_location_id.id,
                                                              'default_location_src_id': self.location_id.id,
                                                              'warehouse_id': self.location_id.warehouse_id.id,
                                                              'active': True,
                                                              'code': 'outgoing'})
                else:
                    picking_type = picking_type[0]
        else:
            # Cập nhật lại giá vốn
            picking_type = stock_picking_type.sudo().search([('default_location_src_id', '=', self.location_id.id),
                                                             ('default_location_dest_id', '=', self.dest_location_id.id)])
            if len(picking_type)>0:
                picking_type = picking_type[0]
            else:
                picking_type = stock_picking_type.sudo().search([('default_location_dest_id', '=', self.dest_location_id.id)])
                if not picking_type or len(picking_type) == 0:
                    picking_type = stock_picking_type.create({'name': _('Nhập điều chỉnh kho: ') + _(self.dest_location_id.name),
                                                              'sequence_id': 1361,
                                                              'default_location_src_id': self.dest_location_id.id,
                                                              'default_location_dest_id': self.location_id.id,
                                                              'warehouse_id': self.location_id.warehouse_id.id,
                                                              'active': True,
                                                              'code': 'incomming'})
                else:
                    picking_type = picking_type[0]

        if self.location_id.id == self.dest_location_id.id:
            raise except_orm('Lỗi !', 'Kho xuất và kho nhập không được phép giống nhau, vui lòng kiểm tra lại !!!')

        reason_out = picking_reason.search([('code', '=', '0')])
        product_uom = self.pool.get('product.uom')
        move_lines = []
        for t_line in self.delivery_lines:
            note = _('Xuất chi phí - ') + _(self.name)
            if t_line.note:
                note = t_line.note
            elif self.note:
                note = self.note
            if self.type == 'out':
                if self.location_id.usage == self.dest_location_id.usage:
                    move_price = 0
                else:
                    if self.location_id.usage == 'inventory':
                        move_price = 0
                    else:
                        move_price = t_line.standard_price
            else:
                if self.location_id.usage != self.dest_location_id.usage:
                    move_price = t_line.standard_price
                else:
                    move_price = 0

            move_args = {
                'name': t_line.product_id.name,
                'product_id': t_line.product_id.id,
                'product_uom': t_line.product_uom_id.id,
                'product_uom_qty': t_line.product_uom_qty,
                'product_uos_qty': t_line.product_uom_qty,
                # 'product_qty': product_qty,
                'origin': self.name,
                'note': note,
                'location_id': self.location_id.id,
                'location_dest_id': self.dest_location_id.id,
                'debit_owner': self.partner_id.id,
                # 'price_unit': 0.0,
                'price_unit': move_price,
                'move_date': self.delivery_date,
                'account_id': t_line.account_id.id,
            }
            # _logger.error(move_args)
            move_lines.append([0, False, move_args])
        if len(move_lines) > 0:
            picking_args = {
                'location_dest_id':self.dest_location_id.id,
                'location_id':self.location_id.id,
                'picking_type_id': picking_type.id,
                'move_lines': move_lines,
                'x_reason': reason_out.id,
                'date_done': self.delivery_date,
                'origin': self.name,
                'partner_id': self.rec_partner_id.id,
            }

            ctx = dict(self._context or {})
            ctx.update({'type': self.type})
            ctx.update({'debit_owner': self.partner_id.id})
            ctx.update({'credit_owner': self.partner_id.id})
            ctx.update({'manual_update_price': True})
            new_picking = stock_picking.with_context().create(picking_args)
            if uid == 1:
                _logger.error("NOW START DO TRANSFER:____________________________")

                new_picking.do_transfer()
            self.picking_id = new_picking
            if uid == 1:
                _logger.error("DONE ALL DO TRANSFER: ___________________________")

    def recompute_standard_price(self, product, standard_price, qty):
        if round(standard_price, 5) != round(product.standard_price, 5):
            _logger.error('Khac nhau')
            cr = self._cr
            query_stock_quant_qty = '''
                SELECT sum(qty) sum_qty from stock_quant where product_id = %s
            '''
            cr.execute(query_stock_quant_qty, (product.id,))
            res = cr.dictfetchone()
            if res:
                if res['sum_qty']:
                    stock_quant_qty = res['sum_qty']
                else:
                    stock_quant_qty = 0
            else:
                stock_quant_qty = 0
            if stock_quant_qty + qty > 0:
                new_standard_price = (stock_quant_qty * product.standard_price + standard_price * qty) / (
                    stock_quant_qty + qty)
                product.write({'standard_price': new_standard_price})
            else:
                product.write({'standard_price': standard_price})

    def auto_complete_inventory_delivery(self, cr, uid):
        env = api.Environment(cr,uid,{})
        inventory_obj = env['inventory.product.delivery']
        delivery_ids = inventory_obj.search([('state', '=', 'ready'), ('delivery_date', '>=', '2018-04-01')])
        for delivery_id in delivery_ids:
            delivery_id.do_inventory_transfer()
            cr.commit()


class InventoryTransferLine(models.Model):
    _name = 'product.delivery.line'

    name = fields.Char("Name")
    transfer_id = fields.Many2one('inventory.product.delivery', "The transfer")
    product_id = fields.Many2one('product.product', "Product", required=True)
    product_uom_id = fields.Many2one('product.uom', "UoM", required=True)
    product_uom_qty = fields.Float("Quantity", required=True)
    delivery_reason = fields.Many2one('stock.picking.reason', 'Reason', required=True,
                                      domain=[('in_or_out', '=', 'external_out')])
    standard_price = fields.Float(string='Standard price', default=0.0)
    account_id = fields.Many2one('account.account', 'Account', required=True)
    note = fields.Text("Note")
    state = fields.Selection(
        selection=(('ready', 'Ready'), ('available', 'Available'), ('partially_available', 'Partially available'),
                   ('not_available', 'Not available')))
    state_text = fields.Char("Status", default="/", copy=False)
    partner_id = fields.Many2one('res.partner', related='transfer_id.partner_id', store=True)

    @api.model
    def create(self, vals):
        parent = self.env['inventory.product.delivery'].browse(vals.get('transfer_id', False))
        if parent.type == 'in':
            vals.update({'state': 'available', 'state_text': 'Available'})
        return super(InventoryTransferLine, self).create(vals)

    @api.onchange('product_id')
    def onchange_product_id(self):
        tmp = 'product.product,' + str(self.product_id.id)
        self.product_uom_id = self.product_id.product_tmpl_id.uom_id
        self.product_uom_qty = 1.0
        object = self.env['ir.property'].search([('name','=','standard_price'),('res_id','=',tmp)])
        if len(object) > 0:
            self.standard_price = object.value_float
        else:
            self.standard_price = self.product_id.product_tmpl_id.standard_price

    @api.onchange('delivery_reason')
    def _change_reason(self):
        if self.delivery_reason and self.delivery_reason.code == '0':
            _logger.info('Khác')
            self.account_id = False
        elif self.delivery_reason:
            self.account_id = self.delivery_reason.account.id

    def _get_qty_from_quant(self, product_id, location_id):
        cr, uid = self._cr, self._uid
        sql = "select sum(quantity) qty_ from stock_quant a where a.product_id = %s and a.location_id = %s"
        param = (product_id, location_id)
        cr.execute(sql, param)
        res = cr.dictfetchone()
        if res['qty_']:
            return res['qty_']
        else:
            return 0

    def _get_balance_by_date(self, location_id, product_id, date):
        cr, uid = self._cr, self._uid
        sql = """
            select sum(t.sum_in) - sum(t.sum_out) sl_ton
            from(
            select
                    case when location_id = %s then SUM(product_qty) end sum_out,
                    case when location_dest_id = %s then SUM(product_qty) end sum_in
            from stock_move
            where 1 = 1
                    AND state='done'
                    AND product_id = %s
                    AND move_date < %s::date
            group by location_id, location_dest_id
            ) t
        """
        param = (location_id, location_id, product_id, date)
        cr.execute(sql, param)
        res = cr.dictfetchone()
        if res:
            return res['sl_ton']
        else:
            return 0

    @api.one
    def check_availability(self):
        self.ensure_one()
        location = self.transfer_id.location_id
        context = self._context.copy() or {}
        context['location'] = location.id
        product = self.product_id.with_context(context)
        qty = self._get_qty_from_quant(self.product_id.id, location.id)
        ret = ''
        if qty <= 0:
            ret = 'not_available'
            self.state_text = _("Không sẵn sàng  (%s)" % str(qty))
        elif qty < self.product_uom_qty:
            ret = 'partially_available'
            self.state_text = _("Chỉ %s sẵn sàng " % str(qty))
        else:
            ret = 'available'
            self.state_text = "Sẵn sàng "

        self.state = ret
        return ret

    @api.one
    def force_available(self):
        self.state = 'available'
        self.state_text = _("Sẵn sàng")


