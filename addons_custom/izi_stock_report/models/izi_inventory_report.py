# -*- coding: utf-8 -*-

from odoo import models, fields, api,_
from datetime import datetime
from odoo.exceptions import except_orm



class IZIInventoryReport(models.TransientModel):
    _name = 'izi.inventory.report'

    name = fields.Char(default='Báo cáo tồn kho')
    compute_at_date = fields.Selection([
        (0, 'Current Inventory')
    ], string="Compute", help="Choose to analyze the current inventory or from a specific date in the past.")
    date = fields.Date('Inventory at Date', help="Choose a date to get the inventory at that date", default=fields.Datetime.now)
    all = fields.Boolean('All')
    warehouse_id = fields.Many2many('stock.warehouse',string='Warehouse')
    inventory_line = fields.One2many('izi.inventory.line','inventory_id', 'Lines')


    def open_table(self):
        self.ensure_one()
        today = datetime.today().strftime('%Y-%m-%d')
        if self.all == True:
            warehouse_ids = self.env['stock.warehouse'].search([('user_ids','=', self.env.user.id)])
            if len(warehouse_ids) < 1:
                raise except_orm(_('Thông báo'),_('Bạn không được phân quyền kho'))
            if len(warehouse_ids) == 1:
                for warehouse_id in warehouse_ids:
                    _warehouse_ids = warehouse_id.id
            else:
                wh_ids = []
                for warehouse_id in warehouse_ids:
                    wh_ids.append(warehouse_id.id)
                _warehouse_ids = tuple(wh_ids)
        else:
            if len(self.warehouse_id) == 1:
                for warehouse_id in self.warehouse_id:
                    _warehouse_ids = warehouse_id.id
            else:
                warehouse_ids = []
                for warehouse_id in self.warehouse_id:
                    warehouse_ids.append(warehouse_id.id)
                _warehouse_ids = tuple(warehouse_ids)

        if self.compute_at_date == 0 or self.date == today:
            self.update({
                'name': 'Báo cáo tồn kho ngày ' + today
            })
            sql = " INSERT INTO izi_inventory_line(inventory_id,product_id,categ_id,company_id,lot_id, warehouse_id,quantity,uom_id, create_date, create_uid,write_uid,write_date)"\
                "  SELECT"\
                    " (%d) as inventory_id,"\
                    " pp.id as product_id,"\
                    " pt.categ_id as categ_id,"\
                    " co.id as company_id,"\
                    " spl.id as lot_id,"\
                    " sw.id as warehouse_id,"\
                    " SUM(quantity) as quantity,"\
                    " u.id as uom_id,"\
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
                    " INNER JOIN res_company co ON sw.company_id = co.id"\
                " WHERE quant.location_id != sw.x_wh_transfer_loc_id "
            if isinstance(_warehouse_ids, int) == False:
                sql += " AND sw.id in %s"
            else:
                sql += " AND sw.id = %d"
            sql += " GROUP BY pp.id,co.id,spl.id,sw.id,u.id, pt.categ_id"\
            " ORDER BY pp.id"
            self._cr.execute(sql % (self.id, self.env.user.id,self.env.user.id, _warehouse_ids))
        else:
            if self.date == False:
                raise except_orm(_('Thông báo'), _('Bạn chưa chọn ngày!'))

            self.update({
                'name': 'Báo cáo tồn kho ngày ' + self.date
            })

            sql = " INSERT INTO izi_inventory_line(inventory_id,product_id,categ_id,company_id,lot_id, warehouse_id,quantity,uom_id, create_date, create_uid,write_uid,write_date)"\
                "  SELECT"\
                    " (%d) as inventory_id,"\
                    " pp.id as product_id,"\
                    " pt.categ_id as categ_id,"\
                    " co.id as company_id,"\
                    " data_wh.lot_id as lot_id,"\
                    " sw.id as warehouse_id,"\
                    " SUM(data_wh.closing_stock) as quantity,"\
                    " pt.uom_id as uom_id,"\
                    " now() as create_date,"\
                    " (%d) as create_uid,"\
                    " (%d) as write_uid,"\
                    " now() as write_date"\
                " FROM izi_data_warehouse_day data_wh"\
                    " JOIN product_product pp ON data_wh.product_id = pp.id"\
                    " JOIN product_template pt ON pp.product_tmpl_id = pt.id"\
                    " INNER JOIN stock_warehouse sw ON data_wh.warehouse_id = sw.id"\
                    " INNER JOIN res_company co ON sw.company_id = co.id"\
                " WHERE data_wh.location_id != sw.x_wh_transfer_loc_id AND data_wh.date_inventory = '%s'"
            if isinstance(_warehouse_ids, int) == False:
                sql += " AND sw.id in %s"
            else:
                sql += " AND sw.id = %d"
            sql += " GROUP BY pp.id,co.id,data_wh.lot_id,sw.id,pt.uom_id, pt.categ_id"\
            " ORDER BY pp.id"

            self._cr.execute(sql % (self.id, self.env.user.id,self.env.user.id,self.date, _warehouse_ids))



        pivot_view_id = self.env.ref('izi_stock_report.view_inventory_report_pivot').id

        action = {
            'type': 'ir.actions.act_window',
            'view_mode': 'pivot',
            'name': _('Inventory'),
            'res_id': False,
            'res_model': 'izi.inventory.line',
            'views' : [(pivot_view_id, 'pivot')],
            'context': dict(self.env.context),
            'domain': [('inventory_id','=', self.id)],
        }
        return action


class IZIInventoryLine(models.TransientModel):
    _name = 'izi.inventory.line'

    inventory_id = fields.Many2one('izi.inventory.report','Inventory')
    product_id = fields.Many2one('product.product','Product')
    categ_id = fields.Many2one('product.category','Category')
    warehouse_id = fields.Many2one('stock.warehouse', 'Warehouse')
    quantity = fields.Float('Quantity')
    uom_id = fields.Many2one('product.uom', "Product Uom")
    company_id = fields.Many2one('res.company', 'Company')
    lot_id = fields.Many2one('stock.production.lot', 'Lot/Serial')

