# -*- coding: utf-8 -*-

from odoo import models, fields, api,_
from datetime import datetime
from odoo.exceptions import except_orm



class izi_in_out_warehouse(models.TransientModel):
    _name = 'izi.in.out.warehouse'


    name = fields.Char(string='General account of input - output')
    all = fields.Boolean('All')
    warehouse_id = fields.Many2many('stock.warehouse',string='Warehouse')
    from_date = fields.Date('From date', default=fields.Datetime.now)
    to_date = fields.Date('To date',  default=fields.Datetime.now)


    def open_table(self):
        self.ensure_one()
        if self.all == True:
            warehouse_ids = self.env['stock.warehouse'].search([('user_ids','=', self.env.user.id)])
        else:
            warehouse_ids = self.warehouse_id

        for warehouse_id in warehouse_ids:
            view_location_id = warehouse_id.view_location_id.id
            location_ids = self.env['stock.location'].search(
                [('usage', '=', 'internal'), ('location_id', '=', view_location_id)])

            for location_id in location_ids:
                if location_id.id == warehouse_id.x_wh_transfer_loc_id:
                    continue
                parent_left = location_id.parent_left

                sql = "INSERT INTO izi_in_out_warehouse_line(izi_in_out_warehouse_id, warehouse_id, product_id, categ_id, date_inventory, purchase_quantity,sale_refund, sale_quantity, purchase_refund, out_transfer, in_transfer, out_inventory, in_inventory)" \
                    " SELECT "\
                        " %d as izi_in_out_warehouse_id,"\
                        " (select sw.id from stock_warehouse sw, stock_location sl where sw.view_location_id = sl.id and sl.parent_left <= %d and sl.parent_right >= %d LIMIT 1) warehouse_id, "\
                        " sm.product_id as product_id,"\
                        " (select pt.categ_id from product_template pt, product_product pp where pt.id = pp.product_tmpl_id AND pp.id = sm.product_id) categ_id, "\
                        " sm.date_expected::DATE as date_inventory, "\
                        " sum(CASE WHEN (spt.code = 'incoming' and sm.to_refund = FALSE) THEN sm.product_uom_qty ELSE 0 END) purchase_quantity, "\
                        " sum(CASE WHEN (spt.code = 'incoming' and sm.to_refund = TRUE) THEN sm.product_uom_qty ELSE 0 END) sale_refund, "\
                        " sum(CASE WHEN (spt.code = 'outgoing' and sm.to_refund = FALSE) THEN sm.product_uom_qty ELSE 0 END) sale_quantity, "\
                        " sum(CASE WHEN (spt.code = 'outgoing' and sm.to_refund = TRUE) THEN sm.product_uom_qty ELSE 0 END) purchase_refund, "\
                        " sum(CASE WHEN (spt.code = 'internal' and sm.location_id = %d) THEN sm.product_uom_qty ELSE 0 END) out_transfer, "\
                        " sum(CASE WHEN (spt.code = 'internal' and sm.location_dest_id = %d) THEN sm.product_uom_qty ELSE 0 END) in_transfer, "\
                        " sum(CASE WHEN (sm.inventory_id > 0 and sm.location_id = %d) THEN sm.product_uom_qty ELSE 0 END) out_inventory, "\
                        " sum(CASE WHEN (sm.inventory_id > 0 and sm.location_dest_id = %d) THEN sm.product_uom_qty ELSE 0 END) in_inventory "\
                    " FROM "\
                        " stock_move sm LEFT JOIN stock_picking_type spt ON sm.picking_type_id = spt.id "\
                    " WHERE "\
                        " sm.date_expected >= to_date('%s', 'YYYY-MM-DD') AND "\
                        " sm.date_expected <= to_date('%s', 'YYYY-MM-DD') + interval '1 day' AND "\
                        " sm.state = 'done' AND "\
                        " (sm.location_dest_id = %d or sm.location_id = %d) "\
                    " GROUP BY sm.product_id,date_inventory,sm.id,spt.id "\
                    " ORDER BY date_inventory "
                self._cr.execute(sql % (self.id, parent_left,parent_left,location_id.id, location_id.id, location_id.id, location_id.id, self.from_date, self.to_date, location_id.id, location_id.id))

        pivot_view_id = self.env.ref('izi_stock_report.izi_in_out_warehouse_line_pivot').id

        action = {
            'type': 'ir.actions.act_window',
            'view_mode': 'pivot',
            'name': _('General account of input - output'),
            'res_id': False,
            'res_model': 'izi.in.out.warehouse.line',
            'views' : [(pivot_view_id, 'pivot')],
            'context': dict(self.env.context),
            'domain': [('izi_in_out_warehouse_id','=', self.id)],
        }
        return action



class izi_in_out_warehouse_line(models.TransientModel):
    _name = 'izi.in.out.warehouse.line'


    izi_in_out_warehouse_id = fields.Many2one('izi.in.out.warehouse', 'In out warehouse')
    warehouse_id = fields.Many2one('stock.warehouse', 'Warehouse')
    product_id = fields.Many2one('product.product','Product')
    categ_id = fields.Many2one('product.category','Category')
    company_id = fields.Many2one('res.company', 'Company')
    lot_id = fields.Many2one('stock.production.lot', 'Lot/Serial')
    purchase_quantity = fields.Float('Purchase quantity')
    sale_quantity = fields.Float('Sale quantity')
    sale_refund = fields.Float('Sale refund')
    purchase_refund = fields.Float('Purchare refund')
    out_transfer = fields.Float('Out transfer')
    in_transfer = fields.Float('In transfer')
    out_inventory = fields.Float('Out inventory')
    in_inventory = fields.Float('In inventory')
    date_inventory = fields.Date('Date')

