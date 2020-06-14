# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import except_orm, ValidationError, UserError

class DepositLine(models.Model):
    _inherit = 'pos.customer.deposit.line'

    @api.multi
    def action_print(self):
        return {
            'type': 'ir.actions.act_url',
            'url': 'report/pdf/pos_customer_deposit.report_template_deposit_view/%s' % (self.id),
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
