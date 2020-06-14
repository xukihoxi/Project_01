# -*- coding: utf-8 -*-


from odoo import models, fields, api, _
from datetime import date, datetime, timedelta
import logging
from odoo.tools.translate import _
import calendar
import os
from odoo.exceptions import MissingError, ValidationError ,except_orm
from odoo.models import BaseModel
try:
    import cStringIO as stringIOModule
except ImportError:
    try:
        import StringIO as stringIOModule
    except ImportError:
        import io as stringIOModule
import base64
import xlwt

logger = logging.getLogger(__name__)


class ScStockCard(models.TransientModel):
    _name = 'scstock.card'


    name = fields.Char("Description", default="Stock card")
    product_uom = fields.Many2one('product.uom', "Unit of measurement", relate='product_id.product_tmpl_id.uom_id')
    location_id = fields.Many2one('stock.location', "Location", required=True, domain=[('usage', '=', 'internal')])
    from_date = fields.Date("From date", required=True)
    to_date = fields.Date("To date", required=True, default=datetime.now())
    product_id = fields.Many2one('product.product', "Product", required=True)
    opening_stock = fields.Float("Opening stock")  # Ton dau ky
    closing_stock = fields.Float("Closing stock")
    move_lines = fields.One2many('scstock.card.line', 'stock_card_id')
    state = fields.Selection(selection=(('temp', 'Temp'), ('generated', 'Generated')),copy=False)

    # Lưu trữ giá trị cộng dồn khi tính tồn kho đến từng dòng nhập/xuất
    temp_inventory = fields.Float("Temporary inventory")

    _defaults = {
        'from_date': lambda *a: date.today().strftime('%Y-%m-01'),
    }

    @api.onchange('to_date','from_date')
    def _onchange_to_date(self):
        if self.to_date:
            if self.to_date > str(datetime.now()):
                raise except_orm('Cảnh báo!', ('Ngày kết thúc không được lớn hơn ngày hiện tại.'))
            if self.from_date:
                if self.to_date < self.from_date:
                    raise except_orm('Cảnh báo!', ('Ngày bắt đầu không được lớn hơn ngày kết thúc.'))

    @api.multi
    def generate_card(self):
        self.ensure_one()
        query = "SELECT id FROM scstock_card WHERE product_id = %s and location_id = %s and write_uid = %s"
        self._cr.execute(query, (self.product_id.id, self.location_id.id, self._uid))
        res = self._cr.dictfetchall()
        if res:
            for r in res:
                a = r['id']
                # query = "Delete FROM scstock_card WHERE id = %s and id != %s"
                # self._cr.execute(query, (a,self.id))
                query_line = "Delete FROM scstock_card_line WHERE stock_card_id = %s"
                self._cr.execute(query_line, (self.id,))
        self.opening_stock = self.calculate_opening_stock()
        self.write({'product_uom': self.product_id.product_tmpl_id.uom_id.id})

        self.generate_card_lines()

        self.state = 'generated'

    def calculate_opening_stock(self):
        '''
        Lấy tổng nhập đến đầu kỳ trừ đi tổng xuất đến đầu kỳ  --> ra số lượng tồn đầu kì
        :return:
        '''
        stock_move_obj = self.env['stock.move']
        quantity_in = 0.0
        quantity_out = 0.0

        query_quant_in = "select SUM(product_qty) as sum_in from stock_move " \
                         "WHERE location_dest_id = %s AND state='done' AND product_id = %s AND (date::timestamp + INTERVAL '7 hours')::date < %s::date"
        self._cr.execute(query_quant_in, (self.location_id.id, self.product_id.id, str(self.from_date)))
        res_sum_in = self._cr.dictfetchone()
        # logger.info('res_sum_in: ' + str(res_sum_in))
        if 'sum_in' in res_sum_in:
            quantity_in = res_sum_in['sum_in']

        if quantity_in is None:
            quantity_in = 0.0

        query_quant_out = "select SUM(product_qty) as sum_out from stock_move " \
                          "where location_id = %s AND state='done'  AND product_id = %s AND (date::timestamp + INTERVAL '7 hours')::date < %s::date"
        self._cr.execute(query_quant_out, (self.location_id.id, self.product_id.id, str(self.from_date)))
        res_sum_out = self._cr.dictfetchone()
        if 'sum_out' in res_sum_out:
            quantity_out = res_sum_out['sum_out']
        # logger.info("Quantity in: " + str(quantity_in))
        # logger.info("Quantity out: " + str(quantity_out))

        if quantity_out is None:
            quantity_out = 0.0
        ret = 0.0
        if quantity_in is not None and quantity_out is not None:
            ret = quantity_in - quantity_out
        return ret

    def generate_card_lines(self):
        '''
        Tìm các stock.move trong khoảng thời gian >= from_date và <= to_date
        sau đó sinh ra các card.line
        :return:
        '''
        query_period_moves = '''
            SELECT sm.id as move_id, sm.location_id, sm.location_dest_id, sm.date,
                sm.product_uom_qty, sp.name as pick_name, sm.product_qty, sp.id as picking_id,
                coalesce(sm.origin, sm.name) origin, sm.note
            FROM stock_move as sm
            LEFT JOIN stock_picking as sp ON sm.picking_id = sp.id
            WHERE
                product_id = %s
                AND (sm.location_id = %s OR sm.location_dest_id = %s)
                AND (sm.date::timestamp + INTERVAL '7 hours')::date >= %s::date
                AND (sm.date::timestamp + INTERVAL '7 hours')::date < (%s::date + '1 day'::interval)
                AND sm.state = 'done'
            ORDER BY (sm.date::timestamp + INTERVAL '7 hours')::date, sm.create_date;
        '''
        self._cr.execute(query_period_moves,
                         (self.product_id.id, self.location_id.id, self.location_id.id, self.from_date, self.to_date))
        res_period_moves = self._cr.dictfetchall()
        card_line_obj = self.env['scstock.card.line']
        stock_move = self.env['stock.move']

        self.temp_inventory = self.opening_stock
        for row in res_period_moves:
            quant_in = 0.0
            quant_out = 0.0

            if row['location_id'] == self.location_id.id:
                quant_out = row['product_qty']
            else:
                quant_in = row['product_qty']

            self.temp_inventory = self.temp_inventory + quant_in - quant_out
            inventory = self.temp_inventory
            note = row['note']
            origin = row['origin']
            move_id = row['move_id']
            the_move = stock_move.sudo().search([('id', '=', move_id)])
            tmp_date = datetime.strptime(the_move.date, "%Y-%m-%d %H:%M:%S") + timedelta(hours=7)
            date_move  = tmp_date.date()
            args = {
                'stock_card_id': self.id,
                'date_time':date_move,
                'move_id': row['move_id'],
                'reference': origin or "-",
                'note': note or "--",
                'quant_in': quant_in,
                'quant_out': quant_out,
                'inventory': inventory,
            }
            card_line_obj.create(args)
        self.closing_stock = self.temp_inventory
        self.write({'closing_stock': self.closing_stock})

    @api.multi
    def action_print(self):
        if len(self.move_lines) == 0:
            self.generate_card()

        wb = xlwt.Workbook(encoding="UTF-8")
        ws = wb.add_sheet(self.location_id.name)
        editable = xlwt.easyxf("protection: cell_locked false;")
        read_only = xlwt.easyxf("")

        ws.col(0).width = 10 * 500
        ws.col(1).width = 10 * 1000
        ws.col(2).width = 10 * 500
        ws.col(3).width = 10 * 500
        ws.col(4).width = 10 * 500
        ws.col(5).width = 10 * 500
        ws.write(0, 0, u'Mã SP')
        ws.write(0, 1, u'Tên SP')
        ws.write(0, 2, u'Đầu kỳ')
        ws.write(1, 0, self.product_id.default_code, editable)
        ws.write(1, 1, self.product_id.name, editable)
        ws.write(1, 2, self.opening_stock, editable)
        ws.write(2, 0, u'Ngày')
        ws.write(2, 1, u'Tham chiếu')
        ws.write(2, 2, u"Ghi chú")
        ws.write(2, 3, u"SL nhập")
        ws.write(2, 4, u"SL xuất")
        ws.write(2, 5, u"Tồn kho")

        style_content = xlwt.easyxf("align: horiz left, vert top")
        style_head_po = xlwt.easyxf('align: wrap on')
        style = xlwt.XFStyle()
        style.num_format_str = '#,##0'
        index = 3
        for line in self.move_lines:
            if line:
                ws.write(index, 0, line.date_time, editable)
                ws.write(index, 1, line.reference, editable)
                ws.write(index, 2, line.note, editable)
                ws.write(index, 3, line.quant_in, style)
                ws.write(index, 4, line.quant_out, style)
                ws.write(index, 5, line.inventory, style)
                index += 1

        stream = stringIOModule.BytesIO()
        wb.save(stream)
        xls = stream.getvalue()
        vals = {
            'name': 'TK ' + self.location_id.name + '.xls',
            'datas': base64.b64encode(xls),
            'datas_fname': 'TK ' + self.location_id.name + 'Từ ngày ' + self.from_date + ' đến ngày' + self.to_date + '.xls',
            'type': 'binary',
            'res_model': 'scstock.card',
            'res_id': self.id,
        }
        file_xls = self.env['ir.attachment'].create(vals)
        return {
            'type': 'ir.actions.act_url',
            'url': '/web/content/' + str(file_xls.id) + '?download=true',
            'target': 'new',
        }
