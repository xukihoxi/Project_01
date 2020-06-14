# -*- coding: utf-8 -*-

from odoo import models, fields, api,_
from datetime import datetime
from odoo.exceptions import except_orm


class izi_in_out_inventory_report(models.TransientModel):
    _name = 'izi.in.out.inventory.report'


    name = fields.Char(string='General account of input - output - inventory')
    all = fields.Boolean('All')
    warehouse_id = fields.Many2many('stock.warehouse',string='Warehouse')

    from_date = fields.Date('From date', default=fields.Datetime.now)
    to_date = fields.Date('To date',  default=fields.Datetime.now)
    get_product_transaction = fields.Boolean('Get only product with the transaction', default=False)
    by_day = fields.Boolean('By date', default=False)


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

        if self.from_date > self.to_date:
            raise except_orm(_('Thông báo'), _('Bạn đang chọn điều kiện ngày không đúng.'))
        today = datetime.today().strftime('%Y-%m-%d')
        to_date = self.to_date
        from_date = self.from_date
        if self.to_date > today:
            to_date = today
        if self.from_date > today:
            from_date = today

        sql = "INSERT INTO izi_in_out_inventory_line_report(in_out_inventory_id,warehouse_id,product_id,lot_id,opening_stock,closing_stock,purchase_quantity,sale_quantity,sale_refund,purchase_refund,out_transfer" \
              ",in_transfer,out_inventory,in_inventory,create_date, create_uid,write_uid,write_date) " \
              "SELECT "\
                    "%d as in_out_inventory_id,"\
	                "wh_day.warehouse_id,"\
	                "wh_day.product_id,"\
                    "wh_day.lot_id,"\
	                "(SELECT sum(opening_stock) FROM izi_data_warehouse_day WHERE location_id <> (select sw.x_wh_transfer_loc_id from stock_warehouse sw where sw.id = wh_day.warehouse_id) and warehouse_id = wh_day.warehouse_id and product_id = wh_day.product_id "\
                        "and lot_id = wh_day.lot_id and date_inventory = '%s' GROUP BY product_id,warehouse_id) as opening_stock, "\
	                "(SELECT sum(closing_stock) FROM izi_data_warehouse_day WHERE location_id <> (select sw.x_wh_transfer_loc_id from stock_warehouse sw where sw.id = wh_day.warehouse_id) and warehouse_id = wh_day.warehouse_id and product_id = wh_day.product_id "\
		                "and lot_id = wh_day.lot_id and date_inventory = '%s' GROUP BY product_id,warehouse_id) as closing_stock, "\
                    "sum(wh_day.purchase_quantity) as purchase_quantity, "\
                    "sum(wh_day.sale_quantity) as sale_quantity, "\
                    "sum(wh_day.sale_refund) as sale_refund, "\
                    "sum(wh_day.purchase_refund) as purchase_refund, "\
                    "sum(wh_day.out_transfer) as out_transfer, "\
                    "sum(wh_day.in_transfer) as in_transfer, "\
                    "sum(wh_day.out_inventory) as out_inventory, "\
                    "sum(wh_day.in_inventory) as in_inventory, "\
                    " now() as create_date,"\
                    " (%d) as create_uid,"\
                    " (%d) as write_uid,"\
                    " now() as write_date "\
              "FROM "\
	                "izi_data_warehouse_day wh_day "\
              "WHERE "\
	                "wh_day.location_id <> (select sw.x_wh_transfer_loc_id from stock_warehouse sw where sw.id = wh_day.warehouse_id) AND "\
	                "wh_day.date_inventory >= '%s' AND "\
	                "wh_day.date_inventory <= '%s' "

        if isinstance(_warehouse_ids, int) == False:
            sql += " AND wh_day.warehouse_id in %s"
        else:
            sql += " AND wh_day.warehouse_id = %d"
        sql += " GROUP BY wh_day.warehouse_id,wh_day.product_id, wh_day.lot_id"

        self._cr.execute(sql % (self.id,from_date,to_date, self.env.user.id,self.env.user.id, from_date,to_date,_warehouse_ids))

        tree_view_id = self.env.ref('izi_stock_report.izi_in_out_inventory_report_tree').id

        action = {
            'type': 'ir.actions.act_window',
            'view_mode': 'tree',
            'name': _('General account of input - output - inventory'),
            'res_id': False,
            'res_model': 'izi.in.out.inventory.line.report',
            'views' : [(tree_view_id, 'tree')],
            'context': dict(self.env.context),
            'domain': [('in_out_inventory_id','=', self.id)],
        }
        return action



class izi_in_out_inventory_line_report(models.TransientModel):
    _name = 'izi.in.out.inventory.line.report'

    in_out_inventory_id = fields.Many2one('izi.in.out.inventory.report','In out inventory')
    warehouse_id = fields.Many2one('stock.warehouse','Warehouse')
    product_id = fields.Many2one('product.product', string='Product')
    lot_id = fields.Many2one('stock.production.lot', string='Lot/Serial')
    opening_stock = fields.Float('Opening stock', default=0)
    closing_stock = fields.Float('Closing stock',default=0)
    purchase_quantity = fields.Float('Purchase quantity',default=0)
    sale_quantity = fields.Float('Sale quantity',default=0)
    sale_refund = fields.Float('Sale refund',default=0)
    purchase_refund = fields.Float('Purchare refund',default=0)
    out_transfer = fields.Float('Out transfer',default=0)
    in_transfer = fields.Float('In transfer',default=0)
    out_inventory = fields.Float('Out inventory',default=0)
    in_inventory = fields.Float('In inventory',default=0)


    # @api.model
    # def read_group(self, domain, fields, groupby, offset=0, limit=None, orderby=False, lazy=True):
    #     res = super(izi_in_out_inventory_line_report, self).read_group(domain,fields,groupby,offset,limit,orderby,lazy)
    #     if 'opening_stock' in fields:
    #         for line in res:
    #             if '__domain' in line:
    #                 lines = self.search(line['__domain'])
    #                 pending_value = 0.0
    #                 for current_account in self.browse(lines):
    #                     pending_value += current_account.opening_stock
    #                 line['opening_stock'] = pending_value
    #     if 'closing_stock' in fields:
    #         for line in res:
    #             if '__domain' in line:
    #                 lines = self.search(line['__domain'])
    #                 payed_value = 0.0
    #                 for current_account in self.browse(lines):
    #                     payed_value += current_account.closing_stock
    #                 line['closing_stock'] = payed_value
    #     return res