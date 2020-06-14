# -*- coding: utf-8 -*-

from odoo import models, fields, api,_
from datetime import datetime
from odoo.exceptions import except_orm



class izi_data_warehouse_day(models.Model):
    _name = 'izi.data.warehouse.day'


    warehouse_id = fields.Many2one('stock.warehouse',string='Warehouse', index=True)
    location_id = fields.Many2one('stock.location', string='Location', index=True)
    product_id = fields.Many2one('product.product', string='Product', index=True)
    lot_id = fields.Many2one('stock.production.lot', string='Lot/Serial')
    opening_stock = fields.Float('Opening stock')
    closing_stock = fields.Float('Closing stock')
    purchase_quantity = fields.Float('Purchase quantity')
    sale_quantity = fields.Float('Sale quantity')
    sale_refund = fields.Float('Sale refund')
    purchase_refund = fields.Float('Purchare refund')
    out_transfer = fields.Float('Out transfer')
    in_transfer = fields.Float('In transfer')
    out_inventory = fields.Float('Out inventory')
    in_inventory = fields.Float('In inventory')
    date_inventory = fields.Date('Date')
    states = fields.Selection([('process','Process'),('close','Close')], default='process', string='State')


    @api.model
    def auto_summary_data_store(self):
        today = datetime.today().strftime('%Y-%m-%d')

        warehouse_today_id = self.search([('date_inventory', '=', today)])
        if len(warehouse_today_id) > 1:
            return
        warehouse_ids = self.env['stock.warehouse'].search([('active','=', True)])
        wh_ids = 0
        if len(warehouse_ids) == 1:
            for wh_id in warehouse_ids:
                wh_ids = wh_id.id
        else:
            array_wh = []
            for wh_id in warehouse_ids:
                array_wh.append(wh_id.id)
            wh_ids = tuple(array_wh)


        sql = " INSERT INTO izi_data_warehouse_day(warehouse_id,location_id,product_id,lot_id,opening_stock,closing_stock,date_inventory,states,create_date, create_uid,write_uid,write_date)"\
            "  SELECT"\
                " sw.id as warehouse_id,"\
                " d.id as location_id,"\
                " pp.id as product_id,"\
                " spl.id as lot_id,"\
                " SUM(quantity) as opening_stock,"\
                " SUM(quantity) as closing_stock,"\
                " ('%s') as date_inventory,"\
                " 'process' as states,"\
                " now() as create_date,"\
                " (%d) as create_uid,"\
                " (%d) as write_uid,"\
                " now() as write_date"\
            " FROM stock_quant quant"\
                " JOIN product_product pp ON quant.product_id = pp.id"\
                " JOIN product_template pt ON pp.product_tmpl_id = pt.id"\
                " JOIN product_uom u ON u.id = pt.uom_id"\
                " LEFT JOIN stock_production_lot spl ON spl.id = quant.lot_id"\
                " INNER JOIN stock_location d ON quant.location_id = d.id"\
                " INNER JOIN stock_warehouse sw ON d.location_id = sw.view_location_id"\
            " WHERE quant.location_id != sw.x_wh_transfer_loc_id"
        if isinstance(wh_ids, int) == False:
            sql += " AND sw.id in %s"
        else:
            sql += " AND sw.id = %d"
        sql += " GROUP BY sw.id,d.id,pp.id,spl.id"
        self._cr.execute(sql % (today, self.env.user.id,self.env.user.id,wh_ids))



    @api.multi
    def get_data_data_warehouse_day(self, warehouse_id, location_id, product_id, lot_id, date_inventory):
        warehouse_day_id = self.env['izi.data.warehouse.day'].search([('warehouse_id','=', warehouse_id),
                                                                      ('location_id','=', location_id),
                                                                      ('product_id', '=', product_id),
                                                                      ('lot_id','=', lot_id),
                                                                      ('date_inventory', '=', date_inventory)], limit=1)

        if warehouse_day_id.id != False:
            return warehouse_day_id
        else:
            quantity = self.get_current_quantity_by_lot(location_id, product_id, lot_id)
            res = self.create({
                'warehouse_id': warehouse_id,
                'location_id': location_id,
                'product_id': product_id,
                'lot_id': lot_id,
                'date_inventory': date_inventory,
                'opening_stock': quantity,
                'closing_stock': quantity,
                'states': 'process'
            })
        return res

    @api.multi
    def get_current_quantity_by_lot(self, location_id, product_id, lot_id = False):
        if lot_id != False:
            sql = " SELECT sum(quantity)" \
                    " FROM stock_quant"\
                    " WHERE location_id = %d AND product_id = %d"\
                    " AND lot_id = %d"
            self._cr.execute(sql % (location_id, product_id, lot_id))
        else:
            sql = " SELECT sum(quantity)" \
                    " FROM stock_quant"\
                    " WHERE location_id = %d AND product_id = %d"
            self._cr.execute(sql % (location_id, product_id))

        res = self._cr.fetchall()[0][0]
        if res != None:
            res = int(res)
        else:
            res = 0
        return res





class IZIDataWareHouseMonth(models.Model):
    _name = 'izi.data.warehouse.month'

    warehouse_id = fields.Many2one('stock.warehouse',string='Warehouse', index=True)
    location_id = fields.Many2one('stock.location', string='Location', index=True)
    product_id = fields.Many2one('product.product', string='Product', index=True)
    lot_id = fields.Many2one('stock.production.lot', string='Lot/Serial')
    opening_stock = fields.Float('Opening stock')
    closing_stock = fields.Float('Closing stock')
    purchase_quantity = fields.Float('Purchase quantity')
    sale_quantity = fields.Float('Sale quantity')
    sale_refund = fields.Float('Sale refund')
    purchase_refund = fields.Float('Purchare refund')
    out_transfer = fields.Float('Out transfer')
    in_transfer = fields.Float('In transfer')
    month = fields.Date('Date')
    states = fields.Selection([('process','Process'),('close','Close')], default='process', string='State')



class stock_move(models.Model):
    _inherit = 'stock.move'


    def _action_done(self):
        res_action_done = super(stock_move, self)._action_done()
        for super_action_done in res_action_done:
            if super_action_done.state != 'done':
                continue
            #Nhap mua NCC
            if super_action_done.picking_code == 'incoming' and super_action_done.to_refund == False:
                if super_action_done.show_details_visible == False:
                    warehouse_day_id = self.env['izi.data.warehouse.day'].get_data_data_warehouse_day(super_action_done.warehouse_id.id,super_action_done.location_dest_id.id,super_action_done.product_id.id, False, super_action_done.date)
                    warehouse_day_id.update({
                        'purchase_quantity': warehouse_day_id.purchase_quantity + super_action_done.quantity_done,
                        'closing_stock': warehouse_day_id.closing_stock + super_action_done.quantity_done
                    })
                else:
                    for line in super_action_done.move_line_ids:
                        warehouse_day_id = self.env['izi.data.warehouse.day'].get_data_data_warehouse_day(super_action_done.warehouse_id.id,super_action_done.location_dest_id.id,super_action_done.product_id.id, line.lot_id.id, super_action_done.date)
                        warehouse_day_id.update({
                            'purchase_quantity': warehouse_day_id.purchase_quantity + line.qty_done,
                            'closing_stock': warehouse_day_id.closing_stock + line.qty_done
                        })
            #Nhap lai hang ban
            if super_action_done.picking_code == 'incoming' and super_action_done.to_refund == True:
                if super_action_done.show_details_visible == False:
                    warehouse_day_id = self.env['izi.data.warehouse.day'].get_data_data_warehouse_day(super_action_done.warehouse_id.id,super_action_done.location_dest_id.id,super_action_done.product_id.id, False, super_action_done.date)
                    warehouse_day_id.update({
                        'sale_refund': warehouse_day_id.sale_refund + super_action_done.quantity_done,
                        'closing_stock': warehouse_day_id.closing_stock + super_action_done.quantity_done
                    })
                else:
                    for line in super_action_done.move_line_ids:
                        warehouse_day_id = self.env['izi.data.warehouse.day'].get_data_data_warehouse_day(super_action_done.warehouse_id.id,super_action_done.location_dest_id.id,super_action_done.product_id.id, line.lot_id.id, super_action_done.date)
                        warehouse_day_id.update({
                            'purchase_quantity': warehouse_day_id.purchase_quantity + line.qty_done,
                            'closing_stock': warehouse_day_id.closing_stock + line.qty_done
                        })

            #Tra lai hang NCC
            if super_action_done.picking_code == 'outgoing' and super_action_done.to_refund == True:
                if super_action_done.show_details_visible == False:
                    warehouse_day_id = self.env['izi.data.warehouse.day'].get_data_data_warehouse_day(super_action_done.warehouse_id.id,super_action_done.location_id.id,super_action_done.product_id.id, False, super_action_done.date)
                    warehouse_day_id.update({
                        'purchase_refund': warehouse_day_id.purchase_refund + super_action_done.quantity_done,
                        'closing_stock': warehouse_day_id.closing_stock - super_action_done.quantity_done
                    })
                else:
                    for line in super_action_done.move_line_ids:
                        warehouse_day_id = self.env['izi.data.warehouse.day'].get_data_data_warehouse_day(super_action_done.warehouse_id.id,super_action_done.location_id.id,super_action_done.product_id.id, line.lot_id.id, super_action_done.date)
                        warehouse_day_id.update({
                            'purchase_refund': warehouse_day_id.purchase_refund + line.qty_done,
                            'closing_stock': warehouse_day_id.closing_stock - line.qty_done
                        })
            #Xuat ban
            if super_action_done.picking_code == 'outgoing' and super_action_done.to_refund == False:
                if super_action_done.show_details_visible == False:
                    warehouse_id = super_action_done.location_id.get_warehouse()
                    warehouse_day_id = self.env['izi.data.warehouse.day'].get_data_data_warehouse_day(warehouse_id.id,super_action_done.location_id.id,super_action_done.product_id.id, False, super_action_done.date)
                    warehouse_day_id.update({
                        'sale_quantity': warehouse_day_id.sale_quantity + super_action_done.quantity_done,
                        'closing_stock': warehouse_day_id.closing_stock - super_action_done.quantity_done
                    })

                    warehouse_dest_id = super_action_done.location_dest_id.get_warehouse()
                    warehouse_dest_day_id = self.env['izi.data.warehouse.day'].get_data_data_warehouse_day(warehouse_dest_id.id,super_action_done.location_dest_id.id,super_action_done.product_id.id, False, super_action_done.date)
                    warehouse_dest_day_id.update({
                        'sale_refund': warehouse_dest_day_id.sale_refund + super_action_done.quantity_done,
                        'closing_stock': warehouse_dest_day_id.closing_stock + super_action_done.quantity_done
                    })
                else:
                    for line in super_action_done.move_line_ids:
                        warehouse_id = super_action_done.location_id.get_warehouse()
                        warehouse_day_id = self.env['izi.data.warehouse.day'].get_data_data_warehouse_day(warehouse_id.id,super_action_done.location_id.id,super_action_done.product_id.id, line.lot_id.id, super_action_done.date)
                        warehouse_day_id.update({
                            'sale_quantity': warehouse_day_id.sale_quantity + line.qty_done,
                            'closing_stock': warehouse_day_id.closing_stock - line.qty_done
                        })


                        warehouse_dest_id = super_action_done.location_dest_id.get_warehouse()
                        warehouse_dest_day_id = self.env['izi.data.warehouse.day'].get_data_data_warehouse_day(warehouse_dest_id.id,super_action_done.location_dest_id.id,super_action_done.product_id.id, line.lot_id.id, super_action_done.date)
                        warehouse_dest_day_id.update({
                            'sale_refund': warehouse_dest_day_id.sale_refund + line.qty_done,
                            'closing_stock': warehouse_dest_day_id.closing_stock + line.qty_done
                        })



            if super_action_done.picking_code == 'internal':
                if super_action_done.show_details_visible == False:
                    warehouse_id = super_action_done.location_id.get_warehouse()
                    warehouse_day_id = self.env['izi.data.warehouse.day'].get_data_data_warehouse_day(warehouse_id.id,super_action_done.location_id.id,super_action_done.product_id.id, False, super_action_done.date)
                    warehouse_day_id.update({
                        'out_transfer': warehouse_day_id.out_transfer + super_action_done.quantity_done,
                        'closing_stock': warehouse_day_id.closing_stock - super_action_done.quantity_done
                    })

                    warehouse_dest_id = super_action_done.location_dest_id.get_warehouse()
                    warehouse_dest_day_id = self.env['izi.data.warehouse.day'].get_data_data_warehouse_day(warehouse_dest_id.id,super_action_done.location_dest_id.id,super_action_done.product_id.id, False, super_action_done.date)
                    warehouse_dest_day_id.update({
                        'in_transfer': warehouse_dest_day_id.in_transfer + super_action_done.quantity_done,
                        'closing_stock': warehouse_dest_day_id.closing_stock + super_action_done.quantity_done
                    })
                else:
                    for line in super_action_done.move_line_ids:
                        warehouse_id = super_action_done.location_id.get_warehouse()
                        warehouse_day_id = self.env['izi.data.warehouse.day'].get_data_data_warehouse_day(warehouse_id.id,super_action_done.location_id.id,super_action_done.product_id.id, line.lot_id.id, super_action_done.date)
                        warehouse_day_id.update({
                            'out_transfer': warehouse_day_id.out_transfer + line.qty_done,
                            'closing_stock': warehouse_day_id.closing_stock - line.qty_done
                        })
                        warehouse_dest_id = super_action_done.location_dest_id.get_warehouse()
                        warehouse_dest_day_id = self.env['izi.data.warehouse.day'].get_data_data_warehouse_day(warehouse_dest_id.id,super_action_done.location_id.id,super_action_done.product_id.id, line.lot_id.id, super_action_done.date)
                        warehouse_dest_day_id.update({
                            'in_transfer': warehouse_dest_day_id.in_transfer + line.qty_done,
                            'closing_stock': warehouse_dest_day_id.closing_stock + line.qty_done
                        })

            #Kiem kho
            if super_action_done.picking_code == False and super_action_done.inventory_id.id != False:
                if super_action_done.show_details_visible == False:
                    if super_action_done.location_dest_id.id == super_action_done.inventory_id.location_id.id:
                        warehouse_id = super_action_done.location_dest_id.get_warehouse()
                        warehouse_day_id = self.env['izi.data.warehouse.day'].get_data_data_warehouse_day(warehouse_id.id,super_action_done.location_dest_id.id,super_action_done.product_id.id, False, super_action_done.date)
                        warehouse_day_id.update({
                            'in_inventory': warehouse_day_id.in_inventory + super_action_done.quantity_done,
                            'closing_stock': super_action_done.quantity_done
                        })
                    else:
                        warehouse_id = super_action_done.location_id.get_warehouse()
                        warehouse_day_id = self.env['izi.data.warehouse.day'].get_data_data_warehouse_day(warehouse_id.id,super_action_done.location_id.id,super_action_done.product_id.id, False, super_action_done.date)
                        warehouse_day_id.update({
                            'out_inventory': warehouse_day_id.out_inventory + super_action_done.quantity_done,
                            'closing_stock': super_action_done.quantity_done
                        })
                else:
                    if super_action_done.location_dest_id.id == super_action_done.inventory_id.location_id.id:
                        warehouse_id = super_action_done.location_dest_id.get_warehouse()
                        for line in super_action_done.move_line_ids:
                            warehouse_day_id = self.env['izi.data.warehouse.day'].get_data_data_warehouse_day(warehouse_id.id,super_action_done.location_dest_id.id,super_action_done.product_id.id, line.lot_id.id, super_action_done.date)
                            warehouse_day_id.update({
                                'in_inventory': warehouse_day_id.in_inventory + line.qty_done,
                                'closing_stock': line.qty_done
                            })
                    else:
                        warehouse_id = super_action_done.location_id.get_warehouse()
                        for line in super_action_done.move_line_ids:
                            warehouse_day_id = self.env['izi.data.warehouse.day'].get_data_data_warehouse_day(warehouse_id.id,super_action_done.location_id.id,super_action_done.product_id.id, line.lot_id.id, super_action_done.date)
                            warehouse_day_id.update({
                                'out_inventory': warehouse_day_id.out_inventory + line.qty_done,
                                'closing_stock': line.qty_done
                            })

        return res_action_done


