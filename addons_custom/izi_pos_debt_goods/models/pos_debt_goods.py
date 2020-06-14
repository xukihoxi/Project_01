# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.tools import float_is_zero
from odoo.exceptions import except_orm
from dateutil.relativedelta import relativedelta
from datetime import datetime


class PosCredit(models.Model):
    _inherit = 'pos.order'

    picking_id = fields.Many2many('stock.picking', string='Picking', readonly=True, copy=False)

    def create_picking(self):
        if self._context.get('xxx', False):
            return True
        """Create a picking for each order and validate it."""
        Picking = self.env['stock.picking']
        Move = self.env['stock.move']
        StockWarehouse = self.env['stock.warehouse']
        for order in self:
            if not order.lines.filtered(lambda l: l.product_id.type in ['product', 'consu']):
                continue
            address = order.partner_id.address_get(['delivery']) or {}
            if not order.picking_type_id or not order.session_id.config_id.x_card_picking_type_id:
                raise except_orm('Cảnh báo!', ('Chưa cấu hình loại điều chuyển kho cho điểm bán hàng của bạn!'))
            picking_type = order.picking_type_id
            # tiennq picking kho hang ban
            card_picking_type = order.session_id.config_id.x_card_picking_type_id

            return_pick_type = order.picking_type_id.return_picking_type_id or order.picking_type_id
            order_picking = Picking
            return_picking = Picking
            moves = Move
            location_id = order.location_id.id
            if order.partner_id:
                destination_id = order.partner_id.property_stock_customer.id
            else:
                if (not picking_type) or (not picking_type.default_location_dest_id):
                    customerloc, supplierloc = StockWarehouse._get_partner_locations()
                    destination_id = customerloc.id
                else:
                    destination_id = picking_type.default_location_dest_id.id

            if picking_type:
                message = _(
                    "This transfer has been created from the point of sale session: <a href=# data-oe-model=pos.order data-oe-id=%d>%s</a>") % (
                              order.id, order.name)
                picking_vals = {
                    'origin': order.name,
                    'partner_id': address.get('delivery', False),
                    'date_done': order.date_order,
                    'picking_type_id': picking_type.id,
                    'company_id': order.company_id.id,
                    'move_type': 'direct',
                    'note': order.note or "",
                    'location_id': location_id,
                    'location_dest_id': destination_id,
                }
                pos_qty = any([x.qty > 0 for x in order.lines if x.product_id.type in ['product', 'consu']])
                if pos_qty:
                    order_picking = Picking.create(picking_vals.copy())
                    order_picking.message_post(body=message)
                neg_qty = any([x.qty < 0 for x in order.lines if x.product_id.type in ['product', 'consu']])
                if neg_qty:
                    return_vals = picking_vals.copy()
                    return_vals.update({
                        'location_id': destination_id,
                        'location_dest_id': return_pick_type != picking_type and return_pick_type.default_location_dest_id.id or location_id,
                        'picking_type_id': return_pick_type.id
                    })
                    return_picking = Picking.create(return_vals)
                    return_picking.message_post(body=message)
            for line in order.lines.filtered(
                    lambda l: l.product_id.type in ['product', 'consu'] and not float_is_zero(l.qty,
                                                                                              precision_rounding=l.product_id.uom_id.rounding)):
                if line.product_id.x_type_card == 'none':
                    move = Move.create({
                        'name': line.name,
                        'product_uom': line.product_id.uom_id.id,
                        'picking_id': order_picking.id if line.qty >= 0 else return_picking.id,
                        'picking_type_id': picking_type.id if line.qty >= 0 else return_pick_type.id,
                        'product_id': line.product_id.id,
                        'product_uom_qty': abs(line.qty),
                        'quantity_done': line.x_qty,
                        'state': 'draft',
                        'location_id': location_id if line.qty >= 0 else destination_id,
                        'location_dest_id': destination_id if line.qty >= 0 else return_pick_type != picking_type and return_pick_type.default_location_dest_id.id or location_id,
                    })
                if line.product_id.x_type_card != 'none' and line.qty > 0:
                    card_vals = {
                        'origin': order.name,
                        'partner_id': address.get('delivery', False),
                        'date_done': order.date_order,
                        'picking_type_id': card_picking_type.id,
                        'company_id': order.company_id.id,
                        'move_type': 'direct',
                        'note': order.note or "",
                        'location_id': card_picking_type.default_location_src_id.id,
                        'location_dest_id': card_picking_type.default_location_dest_id.id,
                    }
                    card_picking = Picking.create(card_vals)
                    moves |= Move.create({
                        'name': line.name,
                        'product_uom': line.product_id.uom_id.id,
                        'picking_id': card_picking.id,
                        'picking_type_id': card_picking_type.id,
                        'product_id': line.product_id.id,
                        'product_uom_qty': 1,
                        'state': 'draft',
                        'location_id': card_picking_type.default_location_src_id.id,
                        'location_dest_id': card_picking_type.default_location_dest_id.id,
                    })
                    if card_picking:
                        order._force_picking_done(card_picking)

                    # when the pos.config has no picking_type_id set only the moves will be created
                    if moves and not card_picking:
                        moves._action_assign()
                        moves.filtered(lambda m: m.state in ['confirmed', 'waiting'])._force_assign()
                        moves.filtered(lambda m: m.product_id.tracking == 'none')._action_done()
                    order.write({'picking_id': [(4, card_picking.id,)]})

            # prefer associating the regular order picking, not the return
            if len(order_picking.move_lines) != 0:
                order_picking.action_confirm()
                order.write({'picking_id': [(4, order_picking.id,)]})
            else:
                order_picking.unlink()
            if len(return_picking.move_lines) != 0:
                return_picking.action_confirm()
                order.write({'picking_id': [(4, return_picking.id)]})
            else:
                return_picking.unlink()
        return True
