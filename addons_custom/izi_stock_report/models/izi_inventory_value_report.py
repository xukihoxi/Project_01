# -*- coding: utf-8 -*-

from odoo import models, fields, api,_
from odoo.exceptions import except_orm



class IZIInventoryValueReport(models.TransientModel):
    _name = 'izi.inventory.value.report'

    name = fields.Char(default='Báo cáo giá trị hàng tồn')

    all = fields.Boolean('All')
    warehouse_id = fields.Many2many('stock.warehouse',string='Warehouse')
    inventory_line = fields.One2many('izi.inventory.value.line','inventory_id', 'Lines')


    def open_table(self):
        self.ensure_one()
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

        sql = " INSERT INTO izi_inventory_value_line(inventory_id,product_id,categ_id,company_id, warehouse_id,quantity,uom_id, create_date, create_uid,write_uid,write_date,total_value)"\
            "  SELECT"\
                " (%d) as inventory_id,"\
                " pp.id as product_id,"\
                " pt.categ_id as categ_id,"\
                " co.id as company_id,"\
                " sw.id as warehouse_id,"\
                " SUM(quantity) as quantity,"\
                " u.id as uom_id,"\
                " now() as create_date,"\
                " (%d) as create_uid,"\
                " (%d) as write_uid,"\
                " now() as write_date,"\
                " (case when("\
		            "(select ir_p.value_text from ir_property ir_p where ir_p.name = 'property_cost_method' and ir_p.res_id like concat('product.category,', pt.categ_id) limit 1) <> 'fifo'"\
	                ") THEN ((SELECT ir_p.value_float from ir_property ir_p where ir_p.name = 'standard_price' and ir_p.res_id like concat('product.product,', pp.id)) * sum(quantity))"\
	                "ELSE (select sum(sm.remaining_value) from stock_move sm where sm.location_dest_id = d.id and sm.product_id = pp.id GROUP BY sm.product_id) END) as total_value"\
            " FROM stock_quant quant"\
                " JOIN product_product pp ON quant.product_id = pp.id"\
                " JOIN product_template pt ON pp.product_tmpl_id = pt.id"\
                " JOIN product_uom u ON u.id = pt.uom_id"\
                " INNER JOIN stock_location d ON quant.location_id = d.id"\
                " INNER JOIN stock_warehouse sw ON d.location_id = sw.view_location_id"\
                " INNER JOIN res_company co ON sw.company_id = co.id"\
            " WHERE quant.location_id != sw.x_wh_transfer_loc_id "
        if isinstance(_warehouse_ids, int) == False:
            sql += " AND sw.id in %s"
        else:
            sql += " AND sw.id = %d"
        sql += " GROUP BY pp.id,co.id,sw.id,u.id, pt.categ_id,d.id"\
        " ORDER BY pp.id"

        self._cr.execute(sql % (self.id, self.env.user.id,self.env.user.id, _warehouse_ids))

        pivot_view_id = self.env.ref('izi_stock_report.view_inventory_value_report_pivot').id

        action = {
            'type': 'ir.actions.act_window',
            'view_mode': 'pivot',
            'name': _('Inventory value report'),
            'res_id': False,
            'res_model': 'izi.inventory.value.line',
            'views' : [(pivot_view_id, 'pivot')],
            'context': dict(self.env.context),
            'domain': [('inventory_id','=', self.id)],
        }
        return action


class IZIInventoryValueLine(models.TransientModel):
    _name = 'izi.inventory.value.line'

    inventory_id = fields.Many2one('izi.inventory.value.report','Inventory')
    product_id = fields.Many2one('product.product','Product')
    categ_id = fields.Many2one('product.category','Category')
    warehouse_id = fields.Many2one('stock.warehouse', 'Warehouse')
    quantity = fields.Float('Quantity')
    total_value = fields.Float('Value total')
    uom_id = fields.Many2one('product.uom', "Product Uom")
    company_id = fields.Many2one('res.company', 'Company')
