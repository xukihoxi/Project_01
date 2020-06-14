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


class RptInvoice(models.TransientModel):
    _name = 'rpt.invoice.excel'

    from_date = fields.Date("From Date")
    to_date = fields.Date("To Date")
    config_id = fields.Many2one('pos.config', "Config")
    all = fields.Boolean('All', default=False)
    brand_ids = fields.Many2many('res.brand', string="Brand")
    branch_ids = fields.Many2many('res.branch', string="Branch")

    @api.onchange('all')
    def _onchange_all(self):
        UserObj = self.env['res.users']
        BrandObj = self.env['res.brand']
        user = UserObj.search([('id', '=', self._uid)], limit=1)
        if not user.branch_ids: raise except_orm('Thông báo', 'Người dùng %s chưa chọn chi nhánh cho phép. Vui lòng liên hệ quản trị để được giải quyết' % (
                                                               str(user.name)))
        for branch in user.branch_ids:
            if not branch: raise except_orm('Thông báo', 'Chi nhánh %s chưa chọn thương hiệu. Vui lòng liên hệ quản trị để được giải quyết' % (
                                                                    str(branch.name)))
        branch_ids = [user.branch_id and user.branch_id.id or 0]
        for branch in user.branch_ids:
            branch_ids.append(branch.id)
        brand_ids = BrandObj.get_brand_ids_by_branches(branch_ids)
        if self.all:
            self.brand_ids = self.env['res.brand'].search([('id', 'in', brand_ids)])
        else:
            self.brand_ids = False

    @api.onchange('brand_ids')
    def _onchange_brand_ids(self):
        UserObj = self.env['res.users']
        BrandObj = self.env['res.brand']
        user = UserObj.search([('id', '=', self._uid)], limit=1)
        if not user.branch_ids: raise except_orm('Thông báo', 'Người dùng %s chưa chọn chi nhánh cho phép. Vui lòng liên hệ quản trị để được giải quyết' % (
                                                               str(user.name)))
        for branch in user.branch_ids:
            if not branch: raise except_orm('Thông báo', 'Chi nhánh %s chưa chọn thương hiệu. Vui lòng liên hệ quản trị để được giải quyết' % (
                                                                    str(branch.name)))
        branch_ids = [user.branch_id and user.branch_id.id or 0]
        for branch in user.branch_ids:
            branch_ids.append(branch.id)
        brand_ids = BrandObj.get_brand_ids_by_branches(branch_ids)
        branch_by_brand_ids = []
        if self.brand_ids:
            for brand in self.brand_ids:
                branches = self.env['res.branch'].search([('brand_id', '=', brand.id)])
                for branch in branches:
                    branch_by_brand_ids.append(branch.id)
        return {
            'domain': {
                'brand_ids': [('id', 'in', brand_ids)],
                'branch_ids': [('id', 'in', branch_by_brand_ids)]
            }
        }

    @api.multi
    def action_print(self):
        param_obj = self.env['ir.config_parameter']
        code = param_obj.get_param('default_account_journal_not_print_report')
        if not code:
            raise ValidationError(
                _(
                    u"Bạn chưa cấu hình thông số hệ thống cho mã nhóm xuất NVL là default_account_journal_not_print_report. Xin hãy liên hệ với người quản trị."))
        list = code.split(',')
        list_id = ''
        config_ids = []
        for x in self.branch_ids:
            config_id = self.env['pos.config'].search([('pos_branch_id', '=', x.id)])
            list_id += ',' + str(config_id.id)
            config_ids.append(config_id)

        # borders = xlwt.Borders()  # Create Borders
        # borders.left = xlwt.Borders.THIN  # May be: NO_LINE, THIN, MEDIUM, DASHED, DOTTED, THICK, DOUBLE, HAIR, MEDIUM_DASHED, THIN_DASH_DOTTED, MEDIUM_DASH_DOTTED, THIN_DASH_DOT_DOTTED, MEDIUM_DASH_DOT_DOTTED, SLANTED_MEDIUM_DASH_DOTTED, or 0x00 through 0x0D.
        # borders.right = xlwt.Borders.THIN
        # borders.top = xlwt.Borders.THIN
        # borders.bottom = xlwt.Borders.THIN
        # borders.left_colour = 0x40
        # borders.right_colour = 0x40
        # borders.top_colour = 0x40
        # borders.bottom_colour = 0x40
        font = xlwt.Font()  # Create the Font
        font.name = 'Times New Roman'
        style = xlwt.XFStyle()  # Create Style
        # style.borders = borders  # Add Borders to Style
        style.font = font
        str_from_date = datetime.strptime(self.from_date, "%Y-%m-%d").strftime("%d/%m/%Y")
        str_to_date = datetime.strptime(self.to_date, "%Y-%m-%d").strftime("%d/%m/%Y")
        wb = xlwt.Workbook(encoding="UTF-8")
        for config in config_ids:
            ws = wb.add_sheet(config.name, cell_overwrite_ok=True)
            # merge_format = wb.add_format({
            #     'bold': 1,
            #     'border': 1,
            #     'align': 'center',
            #     'valign': 'vcenter',
            #     'fg_color': 'yellow'})
            editable = xlwt.easyxf("protection: cell_locked false;")
            read_only = xlwt.easyxf("")
            col =0
            str_journal = {}
            journal_ids = self.env['account.journal'].search([('journal_user', '=', True), ('code', 'not in', list)])
            if journal_ids:
                col = len(journal_ids)
            ws.col(0).width = 10 * 500 #Ngay thang
            ws.col(1).width = 10 * 500  # Dich vu
            ws.col(2).width = 10 * 500 #order
            ws.col(3).width = 10 * 500 #so the
            ws.col(4).width = 10 * 1000 #Ten khach hang
            ws.col(5).width = 10 * 500 # Nhóm sản phẩm
            ws.col(6).width = 10 * 500  # Mã
            ws.col(7).width = 10 * 1000 #Dien gia
            ws.col(8).width = 10 * 500 # Don gia
            ws.col(9).width = 10 * 500  # So luong
            ws.col(10).width = 10 * 500  # Thanh tien
            ws.col(11).width = 10 * 500  # Chiet khau %
            ws.col(12).width = 10 * 500  # Chiet khau tien
            ws.col(13).width = 10 * 500  # So tien thanh toan
            # ws.col(12 + col).width = 10 * 500  # So no
            ws.col(14 + col).width = 10 * 500  # KTV
            # ws.col(15+ col).width = 10 * 500  # No
            ws.col(15 + col).width = 10 * 500  # TVDT
            ws.col(16 + col).width = 10 * 500  # Doctor
            a = 0
            for line in journal_ids:
                a += 1
                ws.col(13 + a).width = 10 * 500  # tien tren tung hinh thuc
                # str_journal['%s_%s' % (line.id, line.name)] = {'id': line.id, 'name': line.name,
                #                                                           'col': 11 + a}
            ws.write_merge(0, 0 , 0, 15 + col,'TK '+ config.name + 'Từ ngày ' + self.from_date + ' đến ngày' + self.to_date,style)
            ws.write(1, 0, u'Ngày tháng', style)
            ws.write(1, 1, u'Loại', style)
            ws.write(1, 2, u'Order', style)
            ws.write(1, 3, u"Số thẻ", style)
            ws.write(1, 4, u"Tên khách hàng", style)
            ws.write(1, 5, u"Nhóm sản phẩm", style)
            ws.write(1, 6, u"Mã", style)
            ws.write(1, 7, u"Diễn giải", style)
            ws.write(1, 8, u"Đơn giá", style)
            ws.write(1, 9, u"Số lượng", style)
            ws.write(1, 10, u"Thành tiền", style)
            ws.write(1, 11, u"Chiết khấu(%)", style)
            ws.write(1, 12, u"Chiết khấu(số tiền)", style)
            ws.write(1, 13, u"Số tiền thanh toán", style)
            # ws.write(1, 13 + col, u"Số nợ")
            ws.write(1, 14 + col, u"KTV", style)
            # ws.write(1, 15 + col, u"Nợ")
            ws.write(1, 15 + col, u"TVDT", style)
            ws.write(1, 16 + col, u"Bác Sĩ", style)
            b = 0
            for line in journal_ids:
                b += 1
                ws.write(1, 13 + b, line.name, style)
                str_journal['%s' % (line.id)] = 13 + b

            style_content = xlwt.easyxf("align: horiz left, vert top")
            style_head_po = xlwt.easyxf('align: wrap on')
            # style = xlwt.XFStyle()
            # style.num_format_str = '#,##0'
            index = 2
            session_id = self.env['pos.session'].search([('config_id', '=', self.config_id.id)])
            query = """select * from revenue_detail_report(%s,%s,%s)"""
            self._cr.execute(query,(str_from_date, str_to_date, str(config.id)))
            res = self._cr.dictfetchall()
            # if not res: raise except_orm('Thông báo',
            #                              'Không có dữ liệu trả về. Liên hệ admin')
            order_id = 0
            order_name = ''
            for r in res:
                if (order_id == 0 or r['order_id'] != order_id) and r['order_id'] != -999:
                    if r['order_id']:
                        sql = """select a.journal_id journal_id, b.name payment_name, sum(a.amount) as amount, sum(a.amount_currency) as amount_currency
                                    from account_bank_statement_line a, account_journal b
                                    where a.journal_id = b.id
                                    and a.pos_statement_id = %s
                                    GROUP BY a.journal_id, b.name;"""
                        payment_obj = self.env['account.bank.statement.line'].search([('pos_statement_id', '=', r['order_id'])])
                        total_payment = 0
                        journal_debt = self.env['account.journal'].search([('code', '=', "GN")])
                        for y in payment_obj:
                            if y.journal_id.id != journal_debt.id:
                                total_payment += y.amount
                        ws.write_merge(index, index + r['line_num'] - 1, 13, 13, total_payment,style)
                        c = 0
                        for q in journal_ids:
                            c += 1
                            ws.write_merge(index, index + r['line_num'] - 1, 11 + c, 11 + c,'', style)
                        self._cr.execute(sql, (r['order_id'],))
                        res = self._cr.dictfetchall()
                        for y in res:
                            for k, v in str_journal.items():
                                if str(y['journal_id']) == k:
                                    col1 = v
                            # if y['journal_id'] == k:
                            #     col1 = v
                        # for x in payment_obj:
                        #     for k, v in str_journal.items():
                        #         if str(x.journal_id.id) == k:
                        #             col1 = v
                            # if str(x.journal_id.id) in str_journal:
                            #     col = str_journal['%s_%s' % (x.journal_id.id, x.journal_id.name)]['col']
                                    ws.write_merge(index, index + r['line_num']-1, int(col1), int(col1), y['amount'],style)

                                    order_id = r['order_id']
                elif (order_name == '' or r['order_name'] != order_name) and r['order_id'] == -999:
                    if r['order_name']:
                        sql_oder_name = """select a.journal_id journal_id, b.name payment_name, sum(a.amount) as amount, sum(a.amount_currency) as amount_currency
                                    from account_bank_statement_line a, account_journal b
                                    where a.journal_id = b.id
                                    and a.ref = %s
                                    and a.date >= to_date(%s,'dd/mm/yyyy')
                                    and a.date <= to_date(%s,'dd/mm/yyyy')
                                    GROUP BY a.journal_id, b.name;"""
                        payment_obj = self.env['account.bank.statement.line'].search([('pos_statement_id', '=', r['order_id'])])
                        total_payment = 0
                        journal_debt = self.env['account.journal'].search([('code', '=', "GN")])
                        for y in payment_obj:
                            if y.journal_id.id != journal_debt.id:
                                total_payment += y.amount
                        ws.write_merge(index, index + r['line_num'] - 1, 13, 13, total_payment,style)
                        c = 0
                        for q in journal_ids:
                            c += 1
                            ws.write_merge(index, index + r['line_num'] - 1, 11 + c, 11 + c,'', style)
                        self._cr.execute(sql_oder_name, (r['order_name'],str_from_date,str_to_date))
                        res = self._cr.dictfetchall()
                        for y in res:
                            for k, v in str_journal.items():
                                if str(y['journal_id']) == k:
                                    col1 = v
                            # if y['journal_id'] == k:
                            #     col1 = v
                        # for x in payment_obj:
                        #     for k, v in str_journal.items():
                        #         if str(x.journal_id.id) == k:
                        #             col1 = v
                            # if str(x.journal_id.id) in str_journal:
                            #     col = str_journal['%s_%s' % (x.journal_id.id, x.journal_id.name)]['col']
                                    ws.write_merge(index, index + r['line_num']-1, int(col1), int(col1), y['amount'],style)

                                    order_name = r['order_name']
                else:
                    if r['order_id'] != -999:
                        order_id = r['order_id']
                    else:
                        order_name = r['order_name']
                ws.write(index, 0, r['date_order'], style)
                ws.write(index, 1, r['using_type_service'], style)
                ws.write(index, 2, r['order_name'], style)
                ws.write(index, 3, r['cus_code'], style)
                ws.write(index, 4, r['cus_name'], style)
                ws.write(index, 5, r['product_cate_name'], style)
                ws.write(index, 6, r['product_code'], style)
                ws.write(index, 7, r['product_name'], style)
                ws.write(index, 8, r['price_unit'], style)
                ws.write(index, 9, r['quantity'], style)
                ws.write(index, 10,
                         (r['price_unit'] - r['amount_discount'] / r['quantity']) * (1 - (r['percent_discount'] or 0.0) / 100.0) * r['quantity'], style)
                ws.write(index, 11, r['percent_discount'], style)
                ws.write(index, 12, r['amount_discount'], style)
                # ws.write(index, 11, r[''])
                # ws.write(index, 13 + col, u"Số nợ")
                # ws.write(index, 14 + col, u"")
                # ws.write(index, 15 + col, u"Nợ")
                ws.write(index, 14 + col, r['employee_name_ktv'], style)
                ws.write(index, 15 + col, r['employee_name_tv'], style)
                ws.write(index, 16 + col, r['doctor_name'], style)
                index += 1
            # Lấy ra đặt cọc điền vào
            sql = """select (b.date + INTERVAL '7' HOUR)::date as date,  b.name pdc_name,
                            h.x_code partner_code, h.name partner_name, 
                            (CASE
                            WHEN b.x_type = 'deposit' THEN b.amount
                            ELSE -b.amount
                            END) amount, b.journal_id, b.note,
                            (select string_agg(DISTINCT(t2.name), ', ') from pos_revenue_allocation_line t1, hr_employee t2 where t1.revenue_allocation_id = i.id and t1.employee_id = t2.id) tv_name
                    from pos_customer_deposit_line b 
                    JOIN pos_session d on d.id = b.session_id
                    JOIN pos_config e on e.id = d.config_id
                    JOIN res_partner h on b.partner_id = h.id 
                    LEFT JOIN pos_revenue_allocation i on i.id = b.revenue_id
                    where b.order_id is null and b.state =  'done' and d.id not in ('1','2','3','4','7','8')
                        and (b.date + INTERVAL '7' HOUR)::date >= to_date(%s,'dd/mm/yyyy')
                        and (b.date + INTERVAL '7' HOUR)::date <= to_date(%s,'dd/mm/yyyy')
                        and e.id = ANY( string_to_array(%s, ',')::integer[])"""
            self._cr.execute(sql,(str_from_date, str_to_date, str(config.id)))
            res = self._cr.dictfetchall()
            for r in res:
                for k, v in str_journal.items():
                    if str(r['journal_id']) == k:
                        ws.write(index, v, r['amount'], style)
                ws.write(index, 0, r['date'], style)
                ws.write(index, 2, r['pdc_name'], style)
                ws.write(index, 3, r['partner_code'], style)
                ws.write(index, 4, r['partner_name'], style)
                ws.write(index, 7, r['note'], style)
                ws.write(index, 15 + col, r['tv_name'], style)
                index += 1
    #         # Lấy ra cac hinh thuc thanh toán công nợ
    #         sql1 = """select (a.date + INTERVAL '7' HOUR)::date as date, a.ref pdc_name,
    #                                 h.x_code partner_code, h.name partner_name, a.amount, a.journal_id, a.name order_name
    #                 from account_bank_statement_line a
    #                 JOIN account_bank_statement b on a.statement_id = b.id
    #                 JOIN res_partner c on a.partner_id = c.id
    #                 JOIN pos_session d on d.id = b.pos_session_id
    #                 JOIN pos_config e on e.id = d.config_id
    #                 JOIN res_partner h on a.partner_id = h.id
    #                 where		a.name like %s and d.id not in ('1','2','3','4','7','8')
    #                 and (a.date + INTERVAL '7' HOUR)::date >= to_date(%s,'dd/mm/yyyy')
    #                 and (a.date + INTERVAL '7' HOUR)::date <= to_date(%s,'dd/mm/yyyy')
    #                 and e.id = ANY( string_to_array(%s, ',')::integer[])
    # """
    #         self._cr.execute(sql1,('INV/%',str_from_date, str_to_date, str(config.id)))
    #         res = self._cr.dictfetchall()
    #         for r in res:
    #             for k, v in str_journal.items():
    #                 if str(r['journal_id']) == k:
    #                     ws.write(index, v, r['amount'], style)
    #             ws.write(index, 0, r['date'], style)
    #             ws.write(index, 2, r['pdc_name'], style)
    #             ws.write(index, 3, r['partner_code'], style)
    #             ws.write(index, 4, r['partner_name'], style)
    #             ws.write(index, 7, r['order_name'], style)
    #             # ws.write(index, 15 + col, r['tv_name'], editable)
    #             index += 1
            # for line in session_id:
            #     digital_sig = self.env['pos.sum.digital.sign'].search([('session_id', '=', 39)])
            #     for tmp in digital_sig:
            #         for x in tmp.sign_order_line_ids:
            #             if x.order_id.x_type != '3':
            #                 if x.product_id.product_tmpl_id.x_type_card not in ('tdv', 'tbt', 'tdt'):
            #                     tvv = ''
            #                     if x.order_id.x_user_id:
            #                         tmp = 0
            #                         for tv in x.order_id.x_user_id:
            #                             tvv += str(tv.name) + ' + '
            #                             tmp += tmp
            #                     ws.write(index, 0, x.order_id.date_order, editable)
            #                     ws.write(index, 1, x.order_id.name, editable)
            #                     ws.write(index, 2, tmp.partner_id.x_code, editable)
            #                     ws.write(index, 3, tmp.partner_id.name, editable)
            #                     ws.write(index, 4, x.product_id.product_tmpl_id.uom_id.name)
            #                     ws.write(index, 5, x.product_id.product_tmpl_id.name)
            #                     ws.write(index, 6, x.price_unit)
            #                     ws.write(index, 7, x.qty)
            #                     ws.write(index, 8, (x.price_unit - x.x_discount / x.qty) * (1 - (x.discount or 0.0) / 100.0)* x.qty)
            #                     ws.write(index, 9, x.discount)
            #                     ws.write(index, 10, x.x_discount)
            #                     # ws.write(index, 11, 'so tien thanh toan')
            #                     # ws.write(index, 13 + col, u"Số nợ")
            #                     # ws.write(index, 14 + col, u"")
            #                     # ws.write(index, 15 + col, u"Nợ")
            #                     ws.write(index, 15 + col, tvv)
            #                     index += 1
            #         for x in tmp.sign_use_service_line_ids:
            #             ktv = ''
            #             if x.employee_ids:
            #                 for kt in x.employee_ids:
            #                     ktv += str(kt.name) + ' + '
            #             if x.doctor_ids:
            #                 for kt in x.doctor_ids:
            #                     ktv += str(kt.name) + ' + '
            #             if x.product_id.product_tmpl_id.x_type_card not in ('tdv', 'tbt', 'tdt'):
            #                 ws.write(index, 0, x.using_id.redeem_date, editable)
            #                 ws.write(index, 1, x.using_id.name, editable)
            #                 ws.write(index, 2, tmp.partner_id.x_code, editable)
            #                 ws.write(index, 3, tmp.partner_id.name, editable)
            #                 ws.write(index, 4, x.service_id.product_tmpl_id.uom_id.name)
            #                 ws.write(index, 5, x.service_id.product_tmpl_id.name)
            #                 ws.write(index, 6, x.price_unit)
            #                 ws.write(index, 7, x.quantity)
            #                 ws.write(index, 8, (x.price_unit - x.x_discount / x.quantity) * (1 - (x.discount or 0.0) / 100.0)* x.quantity)
            #                 ws.write(index, 9, x.discount)
            #                 ws.write(index, 10, x.x_discount)
            #                 # ws.write(index, 11, 'so tien thanh toan')
            #                 # ws.write(index, 13 + col, u"Số nợ")
            #                 # ws.write(index, 14 + col, u"")
            #                 # ws.write(index, 15 + col, u"Nợ")
            #                 ws.write(index, 14 + col, ktv)
            #                 index += 1
            #         # for x in tmp.sign_account_bank_statement_lines_ids:

        stream = stringIOModule.BytesIO()
        wb.save(stream)
        xls = stream.getvalue()
        vals = {
            'name': 'TK ' + '.xls',
            'datas': base64.b64encode(xls),
            'datas_fname': 'TK ' + 'Từ ngày ' + self.from_date + ' đến ngày' + self.to_date + '.xls',
            'type': 'binary',
            'res_model': 'rpt.invoice.excel',
            'res_id': self.id,
        }
        file_xls = self.env['ir.attachment'].create(vals)
        return {
            'type': 'ir.actions.act_url',
            'url': '/web/content/' + str(file_xls.id) + '?download=true',
            'target': '_blank',
        }
