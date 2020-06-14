# -*- coding: utf-8 -*-


from odoo import models, fields, api
from odoo.tools.float_utils import float_compare, float_is_zero, float_round
from odoo.exceptions import ValidationError, except_orm
from odoo.addons import decimal_precision as dp
from odoo.exceptions import UserError


class izi_stock_transfer_line(models.Model):
    _name = 'izi.stock.transfer.line'


    product_id = fields.Many2one('product.product','Product',domain=[('type', 'in', ['product', 'consu'])],index=True, required=True)
    name = fields.Char('Product name')
    quantity_from = fields.Float('Qty From', digits=dp.get_precision('Product Unit of Measure'))
    quantity_to = fields.Float('Qty to', digits=dp.get_precision('Product Unit of Measure'))
    product_uom = fields.Many2one('product.uom', 'Unit of Measure', required=True)
    izi_stock_transfer_id = fields.Many2one('izi.stock.transfer','Stock transfer')
    company_id = fields.Many2one('res.company','Company', default=lambda self: self.env['res.company']._company_default_get('izi.stock.transfer.line'),
                                index=True)
    state = fields.Selection([('draft','Draft'),('waiting','Waiting Another Operation'),('confirmed','Waiting'),
                              ('assigned','Ready'),('done','Done'),('cancel','Cancel')],'State', default="draft")
    note = fields.Char('Note')

    stock_transfer_lines = fields.One2many('stock.move','x_transfer_line_id')

    @api.onchange('product_id')
    def onchange_product_id(self):
        product = self.product_id.with_context(lang=self.env.user.lang)
        self.name = product.partner_ref
        self.product_uom = product.uom_id.id
        return {'domain': {'product_uom': [('category_id', '=', product.uom_id.category_id.id)]}}


    @api.multi
    def _create_stock_moves(self, picking, transfer = True):
        moves = self.env['stock.move']
        done = self.env['stock.move'].browse()
        for line in self:
            for val in line._prepare_stock_moves(picking, transfer):
                done += moves.create(val)
        return done

    @api.multi
    def _prepare_stock_moves(self, picking, transfer = True):
        """ Prepare the stock moves data for one order line. This function returns a list of
        dictionary ready to be used in stock.move's create()
        """
        self.ensure_one()
        res = []
        if self.product_id.type not in ['product', 'consu']:
            return res
        template = {
            'name': self.name or '',
            'product_id': self.product_id.id,
            'product_uom': self.product_uom.id,
            'product_uom_qty': self.quantity_from,
            'date': self.izi_stock_transfer_id.scheduled_date,
            'date_expected': self.izi_stock_transfer_id.scheduled_date,
            'location_id': picking.location_id.id,
            'location_dest_id': picking.location_dest_id.id,
            'picking_id': picking.id,
            'x_transfer_from_id':self.izi_stock_transfer_id.id if transfer else False,
            'x_transfer_to_id': self.izi_stock_transfer_id.id if not transfer else False,
            'state': 'draft',
            'x_transfer_line_id': self.id,
            'company_id': self.izi_stock_transfer_id.company_id.id,
            'picking_type_id': self.izi_stock_transfer_id.stock_picking_type.id if transfer else self.izi_stock_transfer_id.stock_picking_type_in.id,
            'origin': self.izi_stock_transfer_id.name,
            'route_ids': self.izi_stock_transfer_id.stock_picking_type.warehouse_id and [(6, 0, [x.id for x in self.izi_stock_transfer_id.stock_picking_type.warehouse_id.route_ids])] or [],
            'warehouse_id': self.izi_stock_transfer_id.stock_picking_type.warehouse_id.id,
        }
        res.append(template)
        return res

    def _get_transfer_lines(self):
        self.ensure_one()
        return self.stock_transfer_lines
