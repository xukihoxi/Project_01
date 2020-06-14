# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import except_orm


class PosOrderQweb(models.Model):
    _inherit = 'pos.order'

    x_discount_exception = fields.Float('Exception discount', compute='_compute_journal_exception', store=True)
    x_payment_voucher = fields.Float("Payment Voucher", compute='_compute_journal_voucher', store=True)
    x_payment_coin = fields.Float("Payment Coin", compute='_compute_journal_coin' , store=True)
    x_payment_deposit = fields.Float("Payment Depossit", compute='_compute_journal_deposit', store=True)
    x_debit = fields.Many2one('account.journal', "Debit")

    @api.multi
    def action_print(self):
        if self.branch_id.brand_id.code in ['AMIA']:#AMIA
            return {
                'type': 'ir.actions.act_url',
                'url': 'report/pdf/report_qweb.report_template_invoice_view_amia/%s' %(self.id),
                'target': 'new',
                'res_id': self.id,
            }
        else:
            raise except_orm('Thông báo', 'Chưa cấu hình phiếu in cho thương hiệu %s vui lòng liên hệ Admin để được giải quyết!' % (str(self.branch_id.brand_id.name)))

    @api.multi
    def action_print_virual_money(self):
        return {
            'type': 'ir.actions.act_url',
            'url': 'report/pdf/report_qweb.report_template_invoice_virual_money_view/%s' % (self.id),
            'target': 'new',
            'res_id': self.id,
        }
    # chietkhaungoaile
    @api.depends('statement_ids')
    def _compute_journal_exception(self):
        for order in self:
            amount_payment = 0
            for journal_exception_id in order.config_id.journal_exception_ids:
                for statement in order.statement_ids:
                    if statement.journal_id.id == journal_exception_id.id:
                        amount_payment += statement.amount
            order.x_discount_exception = amount_payment

    # Tong tien thanh toan bang Voucher
    @api.depends('statement_ids')
    def _compute_journal_voucher(self):
        for order in self:
            amount_payment = 0
            for statement in order.statement_ids:
                if statement.journal_id.code == 'VC':
                    amount_payment += statement.amount
            order.x_payment_voucher = amount_payment

    @api.depends('statement_ids')
    def _compute_journal_coin(self):
        for order in self:
            amount_payment = 0
            for statement in order.statement_ids:
                if statement.journal_id.code == 'VM':
                    amount_payment += statement.amount
            order.x_payment_coin = amount_payment

    @api.depends('statement_ids')
    def _compute_journal_deposit(self):
        for order in self:
            amount_payment = 0
            for journal_deposit in order.config_id.journal_deposit_id:
                for statement in order.statement_ids:
                    if statement.journal_id.id == journal_deposit.id:
                        amount_payment += statement.amount
            order.x_payment_deposit = amount_payment

    @api.multi
    def get_name_print_product(self, product):
        # TDE: this could be cleaned a bit I think
        # product = self.env['product.product'].search([('id', '=', product_id)])

        def _name_get(d):
            name = d.get('name', '')
            code = self._context.get('display_default_code', True) and d.get('default_code', False) or False
            if code:
                name = '[%s] %s' % (code, name)
            return name

        # partner_id = self._context.get('partner_id')
        # if partner_id:
        #     partner_ids = [partner_id, self.env['res.partner'].browse(partner_id).commercial_partner_id.id]
        # else:
        #     partner_ids = []
        #
        # # all user don't have access to seller and partner
        # # check access and use superuser
        # self.check_access_rights("read")
        # self.check_access_rule("read")

        result = []
        for product in product:
            # display only the attributes with multiple possible values on the template
            variable_attributes = product.attribute_line_ids.filtered(lambda l: len(l.value_ids) > 1).mapped(
                'attribute_id')
            variant = product.attribute_value_ids._variant_name(variable_attributes)

            name = variant and "%s (%s)" % (product.name, variant) or product.name
            # sellers = []
            # if partner_ids:
            #     sellers = [x for x in product.seller_ids if (x.name.id in partner_ids) and (x.product_id == product)]
            #     if not sellers:
            #         sellers = [x for x in product.seller_ids if (x.name.id in partner_ids) and not x.product_id]
            # if sellers:
            #     for s in sellers:
            #         seller_variant = s.product_name and (
            #                 variant and "%s (%s)" % (s.product_name, variant) or s.product_name
            #         ) or False
            #         mydict = {
            #             'id': product.id,
            #             'name': seller_variant or name,
            #             'default_code': s.product_code or product.default_code,
            #         }
            #         temp = _name_get(mydict)
            #         if temp not in result:
            #             result.append(temp)
            # else:
            mydict = {
                'id': product.id,
                'name': name,
                'default_code': product.default_code,
            }

        return _name_get(mydict)

    @api.multi
    def convert_numbers_to_text(self, numbers):
        result = ""
        numbers = int(abs(numbers))
        numbers_str = str(int(numbers))
        max_len = len(numbers_str)
        res = []
        surplus = max_len % 3
        if surplus != 0:
            sub_str = numbers_str[0:surplus]
            res.append(sub_str)
        decimal_number = max_len / 3
        for i in range(0, int(decimal_number)):
            num = surplus
            index = num + 3
            sub_str = numbers_str[num:index]
            res.append(sub_str)
            surplus = index
        result = ""
        is_first = True
        for i in range(0, len(res)):
            result = result + " " + self.get_text_from_number_multi(len(res) - i, res[i], is_first)
            is_first = False
        # if result.find("Việt Nam Đồng") == -1:
        #     result = result + " VNĐ"
        return result

    def get_text_from_number_multi(self, index, str_number, is_first):
        result = ""
        if self.check_after_number_is_zero(str_number):
            return " "
        if len(str_number) == 1:
            return self.get_text_from_number_t1(str_number[0]) + " " + self.get_text_uom(index)

        if len(str_number) == 2:
            if str_number[0] == '1':
                if str_number[1] == '0':
                    return "Mười " + self.get_text_uom(index)
                else:
                    return "Mười " + self.get_text_from_number(str_number[1]) + " " + self.get_text_uom(index)
            if str_number[1] == '0':
                return self.get_text_from_number_t1(str_number[0]) + " mươi " + self.get_text_uom(index)
            else:
                return self.get_text_from_number_t1(str_number[0]) + " mươi " + self.get_text_from_number(
                    str_number[1]) + " " + self.get_text_uom(index)

        if len(str_number) == 3:
            if is_first:
                if str_number[0] == '0':
                    if str_number[1] == '0':
                        return self.get_text_from_number(str_number[2]) + " " + self.get_text_uom(index)
                    if str_number[1] == '1':
                        if str_number[2] == '0':
                            return "không trăm mười " + self.get_text_uom(index)
                        else:
                            return "không trăm mười " + self.get_text_from_number(
                                str_number[2]) + " " + self.get_text_uom(
                                index)
                    else:
                        if str_number[2] == '0':
                            return "không trăm " + self.get_text_from_number(
                                str_number[1]) + " mươi " + self.get_text_uom(
                                index)
                        else:
                            return "không trăm " + self.get_text_from_number(
                                str_number[1]) + " mươi " + self.get_text_from_number(
                                str_number[2]) + " " + self.get_text_uom(index)
                else:
                    if str_number[1] == '0':
                        if str_number[2] == '0':
                            return self.get_text_from_number_t1(str_number[0]) + " trăm " + self.get_text_uom(index)
                        else:
                            return self.get_text_from_number_t1(
                                str_number[0]) + " trăm lẻ " + self.get_text_from_number(
                                str_number[2]) + " " + self.get_text_uom(index)
                    if str_number[1] == '1':
                        if str_number[2] == '0':
                            return self.get_text_from_number_t1(str_number[0]) + " trăm mười " + self.get_text_uom(
                                index)
                        else:
                            return self.get_text_from_number_t1(
                                str_number[0]) + " trăm mười " + self.get_text_from_number(
                                str_number[2]) + " " + self.get_text_uom(index)
                    else:
                        if str_number[2] == '0':
                            return self.get_text_from_number_t1(str_number[0]) + " trăm " + self.get_text_from_number(
                                str_number[1]) + " mươi " + self.get_text_uom(index)
                        else:
                            return self.get_text_from_number_t1(str_number[0]) + " trăm " + self.get_text_from_number(
                                str_number[1]) + " mươi " + self.get_text_from_number(
                                str_number[2]) + " " + self.get_text_uom(index)

            else:
                if str_number[0] == '0':
                    if str_number[1] == '0':
                        return self.get_text_from_number(str_number[2]) + " " + self.get_text_uom(index)
                    if str_number[1] == '1':
                        if str_number[2] == '0':
                            return "không trăm mười " + self.get_text_uom(index)
                        else:
                            return "không trăm mười " + self.get_text_from_number(
                                str_number[2]) + " " + self.get_text_uom(
                                index)
                    else:
                        if str_number[2] == '0':
                            return "không trăm " + self.get_text_from_number(
                                str_number[1]) + " mươi " + self.get_text_uom(
                                index)
                        else:
                            return "không trăm " + self.get_text_from_number(
                                str_number[1]) + " mươi " + self.get_text_from_number(
                                str_number[2]) + " " + self.get_text_uom(index)
                else:
                    if str_number[1] == '0':
                        if str_number[2] == '0':
                            return self.get_text_from_number(str_number[0]) + " trăm " + self.get_text_uom(index)
                        else:
                            return self.get_text_from_number(str_number[0]) + " trăm lẻ " + self.get_text_from_number(
                                str_number[2]) + " " + self.get_text_uom(index)
                    if str_number[1] == '1':
                        if str_number[2] == '0':
                            return self.get_text_from_number(str_number[0]) + " trăm mười " + self.get_text_uom(index)
                        else:
                            return self.get_text_from_number(str_number[0]) + " trăm mười " + self.get_text_from_number(
                                str_number[2]) + " " + self.get_text_uom(index)
                    else:
                        if str_number[2] == '0':
                            return self.get_text_from_number(str_number[0]) + " trăm " + self.get_text_from_number(
                                str_number[1]) + " mươi " + self.get_text_uom(index)
                        else:
                            return self.get_text_from_number(str_number[0]) + " trăm " + self.get_text_from_number(
                                str_number[1]) + " mươi " + self.get_text_from_number(
                                str_number[2]) + " " + self.get_text_uom(index)

    def check_after_number_is_zero(self, number_str):
        len_str = len(number_str)
        for i in range(0, len_str):
            if number_str[i] != '0':
                return False
        return True

    def get_text_from_number(self, number):
        options = {
            '0': 'không',
            '1': 'một',
            '2': 'hai',
            '3': 'ba',
            '4': 'bốn',
            '5': 'năm',
            '6': 'sáu',
            '7': 'bảy',
            '8': 'tám',
            '9': 'chín'
        }

        return options[number]

    def get_text_from_number_t1(self, number):
        options = {
            '0': 'Không',
            '1': 'Một',
            '2': 'Hai',
            '3': 'Ba',
            '4': 'Bốn',
            '5': 'Năm',
            '6': 'Sáu',
            '7': 'Bảy',
            '8': 'Tám',
            '9': 'Chín'
        }

        return options[number]

    def get_text_uom(self, index):
        options = {
            1: '',
            2: 'nghìn',
            3: 'triệu',
            4: 'tỉ',  # Ti dong
            5: 'nghìn tỉ',  # Nghin tỉ đồng
            6: 'triệu tỉ'  # Triệu tỉ đồng
        }
        return options[index]


class AccountInvoice(models.Model):
    _inherit = "account.invoice"

    @api.multi
    def action_in_invoice_payment(self):
        return {
            'type': 'ir.actions.act_url',
            'url': 'report/pdf/report_qweb.report_template_invoice_payment_view/%s' % (self.id),
            'target': 'new',
            'res_id': self.id,
        }


    @api.multi
    def invoice_print(self):
        return {
            'type': 'ir.actions.act_url',
            'url': 'report/pdf/report_qweb.report_template_invoice_payment_view/%s' % (self.id),
            'target': 'new',
            'res_id': self.id,
        }


class AccountPayment(models.Model):
    _inherit = 'account.payment'

    statement_line_ids = fields.One2many('account.bank.statement.line', 'x_payment_id', "Statement")

    @api.multi
    def action_in_account_payment(self):
        return {
            'type': 'ir.actions.act_url',
            'url': 'report/pdf/report_qweb.report_template_account_payment_view/%s' % (self.id),
            'target': 'new',
            'res_id': self.id,
        }

    @api.multi
    def convert_numbers_to_text(self, numbers):
        result = ""
        numbers = int(abs(numbers))
        numbers_str = str(int(numbers))
        max_len = len(numbers_str)
        res = []
        surplus = max_len % 3
        if surplus != 0:
            sub_str = numbers_str[0:surplus]
            res.append(sub_str)
        decimal_number = max_len / 3
        for i in range(0, int(decimal_number)):
            num = surplus
            index = num + 3
            sub_str = numbers_str[num:index]
            res.append(sub_str)
            surplus = index
        result = ""
        is_first = True
        for i in range(0, len(res)):
            result = result + " " + self.get_text_from_number_multi(len(res) - i, res[i], is_first)
            is_first = False
        return result

    def get_text_from_number_multi(self, index, str_number, is_first):
        result = ""
        if self.check_after_number_is_zero(str_number):
            return " "
        if len(str_number) == 1:
            return self.get_text_from_number_t1(str_number[0]) + " " + self.get_text_uom(index)

        if len(str_number) == 2:
            if str_number[0] == '1':
                if str_number[1] == '0':
                    return "Mười " + self.get_text_uom(index)
                else:
                    return "Mười " + self.get_text_from_number(str_number[1]) + " " + self.get_text_uom(index)
            if str_number[1] == '0':
                return self.get_text_from_number_t1(str_number[0]) + " mươi " + self.get_text_uom(index)
            else:
                return self.get_text_from_number_t1(str_number[0]) + " mươi " + self.get_text_from_number(
                    str_number[1]) + " " + self.get_text_uom(index)

        if len(str_number) == 3:
            if is_first:
                if str_number[0] == '0':
                    if str_number[1] == '0':
                        return self.get_text_from_number(str_number[2]) + " " + self.get_text_uom(index)
                    if str_number[1] == '1':
                        if str_number[2] == '0':
                            return "không trăm mười " + self.get_text_uom(index)
                        else:
                            return "không trăm mười " + self.get_text_from_number(
                                str_number[2]) + " " + self.get_text_uom(
                                index)
                    else:
                        if str_number[2] == '0':
                            return "không trăm " + self.get_text_from_number(
                                str_number[1]) + " mươi " + self.get_text_uom(
                                index)
                        else:
                            return "không trăm " + self.get_text_from_number(
                                str_number[1]) + " mươi " + self.get_text_from_number(
                                str_number[2]) + " " + self.get_text_uom(index)
                else:
                    if str_number[1] == '0':
                        if str_number[2] == '0':
                            return self.get_text_from_number_t1(str_number[0]) + " trăm " + self.get_text_uom(index)
                        else:
                            return self.get_text_from_number_t1(
                                str_number[0]) + " trăm lẻ " + self.get_text_from_number(
                                str_number[2]) + " " + self.get_text_uom(index)
                    if str_number[1] == '1':
                        if str_number[2] == '0':
                            return self.get_text_from_number_t1(str_number[0]) + " trăm mười " + self.get_text_uom(
                                index)
                        else:
                            return self.get_text_from_number_t1(
                                str_number[0]) + " trăm mười " + self.get_text_from_number(
                                str_number[2]) + " " + self.get_text_uom(index)
                    else:
                        if str_number[2] == '0':
                            return self.get_text_from_number_t1(str_number[0]) + " trăm " + self.get_text_from_number(
                                str_number[1]) + " mươi " + self.get_text_uom(index)
                        else:
                            return self.get_text_from_number_t1(str_number[0]) + " trăm " + self.get_text_from_number(
                                str_number[1]) + " mươi " + self.get_text_from_number(
                                str_number[2]) + " " + self.get_text_uom(index)

            else:
                if str_number[0] == '0':
                    if str_number[1] == '0':
                        return self.get_text_from_number(str_number[2]) + " " + self.get_text_uom(index)
                    if str_number[1] == '1':
                        if str_number[2] == '0':
                            return "không trăm mười " + self.get_text_uom(index)
                        else:
                            return "không trăm mười " + self.get_text_from_number(
                                str_number[2]) + " " + self.get_text_uom(
                                index)
                    else:
                        if str_number[2] == '0':
                            return "không trăm " + self.get_text_from_number(
                                str_number[1]) + " mươi " + self.get_text_uom(
                                index)
                        else:
                            return "không trăm " + self.get_text_from_number(
                                str_number[1]) + " mươi " + self.get_text_from_number(
                                str_number[2]) + " " + self.get_text_uom(index)
                else:
                    if str_number[1] == '0':
                        if str_number[2] == '0':
                            return self.get_text_from_number(str_number[0]) + " trăm " + self.get_text_uom(index)
                        else:
                            return self.get_text_from_number(str_number[0]) + " trăm lẻ " + self.get_text_from_number(
                                str_number[2]) + " " + self.get_text_uom(index)
                    if str_number[1] == '1':
                        if str_number[2] == '0':
                            return self.get_text_from_number(str_number[0]) + " trăm mười " + self.get_text_uom(index)
                        else:
                            return self.get_text_from_number(str_number[0]) + " trăm mười " + self.get_text_from_number(
                                str_number[2]) + " " + self.get_text_uom(index)
                    else:
                        if str_number[2] == '0':
                            return self.get_text_from_number(str_number[0]) + " trăm " + self.get_text_from_number(
                                str_number[1]) + " mươi " + self.get_text_uom(index)
                        else:
                            return self.get_text_from_number(str_number[0]) + " trăm " + self.get_text_from_number(
                                str_number[1]) + " mươi " + self.get_text_from_number(
                                str_number[2]) + " " + self.get_text_uom(index)

    def check_after_number_is_zero(self, number_str):
        len_str = len(number_str)
        for i in range(0, len_str):
            if number_str[i] != '0':
                return False
        return True

    def get_text_from_number(self, number):
        options = {
            '0': 'không',
            '1': 'một',
            '2': 'hai',
            '3': 'ba',
            '4': 'bốn',
            '5': 'năm',
            '6': 'sáu',
            '7': 'bảy',
            '8': 'tám',
            '9': 'chín'
        }

        return options[number]

    def get_text_from_number_t1(self, number):
        options = {
            '0': 'Không',
            '1': 'Một',
            '2': 'Hai',
            '3': 'Ba',
            '4': 'Bốn',
            '5': 'Năm',
            '6': 'Sáu',
            '7': 'Bảy',
            '8': 'Tám',
            '9': 'Chín'
        }

        return options[number]

    def get_text_uom(self, index):
        options = {
            1: '',
            2: 'nghìn',
            3: 'triệu',
            4: 'tỉ',  # Ti dong
            5: 'nghìn tỉ',  # Nghin tỉ đồng
            6: 'triệu tỉ'  # Triệu tỉ đồng
        }
        return options[index]

    @api.multi
    def get_name_print_nvtv(self, payment_id):
        bank_statement_obj = self.env['account.bank.statement.line'].search([('x_payment_id', '=',payment_id)])
        order_name = bank_statement_obj.ref.split('PAID_')
        order_obj = self.env['pos.order'].search([('name','=', order_name)])

        return order_obj.x_user_id