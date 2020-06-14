# -*- coding: utf-8 -*-

from odoo import models, fields, api
from datetime import datetime, timedelta

class ScanBarcodeServiceCardUsingLine(models.TransientModel):
    _name = 'scan.barcode.izi.service.card.using.line'

    name = fields.Char(string="Name")
    message = fields.Text(string="Message")

    @api.onchange('name')
    def onchange_name(self):
        if self.name:
            try:
                using_line_id = int(self.name)
                if using_line_id < -2147483648 or using_line_id > 2147483647:  # kiểm tra dữ liệu nhập có lớn hơn giá trị tối đa của int4
                    return {
                        'value': {
                            'name': False,
                            'message': 'Mã nhập không hợp lệ, liên hệ Admin! [%s]' % (str(self.name))
                        }
                    }
                ObjUsingLine = self.env['izi.service.card.using.line']
                using_line = ObjUsingLine.search([('id', '=', int(self.name))])
                if using_line:
                    str_service = '[%s]%s' % (str(using_line.service_id.default_code), str(using_line.service_id.name))
                    str_customer = str(using_line.using_id.customer_id.name)
                    str_bed = ''
                    for bed in using_line.bed_ids:
                        str_bed += '[%s]%s, ' % (str(bed.room_id.name), str(bed.name))
                    str_employee = ''
                    for employee in using_line.employee_ids:
                        str_employee += '%s, ' % (str(employee.name))

                    if using_line.state == 'new':
                        message = 'Bắt đầu làm dịch vụ!\n' \
                                  'Dịch vụ: %s\n' \
                                  'Khách hàng: %s\n' \
                                  'Giường: %s\n' \
                                  'Nhân viên làm: %s' % (str(str_service), str(str_customer), str(str_bed), str(str_employee))
                        using_line.action_confirm_bed()
                    elif using_line.state == 'working':
                        message = 'Hoàn thành làm dịch vụ!\n' \
                                  'Dịch vụ: %s\n' \
                                  'Khách hàng: %s\n' \
                                  'Giường: %s\n' \
                                  'Nhân viên làm: %s' % (str(str_service), str(str_customer), str(str_bed), str(str_employee))
                        using_line.action_done()
                    elif using_line.state == 'done':
                        message = 'Công việc này đã hoàn thành, vui lòng không quét mã!\n' \
                                  'Dịch vụ: %s\n' \
                                  'Khách hàng: %s\n' \
                                  'Giường: %s\n' \
                                  'Nhân viên làm: %s' % (str(str_service), str(str_customer), str(str_bed), str(str_employee))
                    else:
                        message = 'Trạng thái của công việc: %s' % (str(using_line.state))
                else:
                    message = 'Không tìm thấy công việc có mã %s. Để nhanh chóng vui lòng liên hệ quầy để xác nhận công việc, hoặc kiểm tra lại quy trình in phiếu!' % (str(self.name))
                return {
                    'value': {
                        'name': False,
                        'message': message
                    }
                }
            except ValueError:
                return {
                    'value': {
                        'name': False,
                        'message': 'Chỉ nhập mã là chữ số!'
                    }
                }

        else:
            pass
