# -*- coding: utf-8 -*-
from odoo import models, api, fields , _
from odoo.exceptions import except_orm
from odoo.osv import expression
from odoo import sys, os
import base64, time
from os.path import  join
from datetime import datetime, timedelta
import logging

class ResPartnerCustom(models.Model):
    _inherit = 'res.partner'

    @api.model
    def get_card_detail_customer(self, partner_id):
        # print(1)
        card_details = []
        if partner_id:
            use_card_line_obj = self.env['izi.service.card.using'].sudo().search(
                [('customer_id', '=', partner_id), ('type', '!=', 'card')], order='id desc')
            for use_card_line_ids in use_card_line_obj:
                for use_card_line_id in use_card_line_ids.service_card1_ids:
                    employee = ''
                    for x in use_card_line_id.employee_ids:
                        employee = employee + ', ' + str(x.name)
                    for y in use_card_line_id.doctor_ids:
                        employee = employee + ', ' + str(y.name)
                    vals3 = {
                        'order_name': use_card_line_ids.pos_order_id.name if use_card_line_ids.pos_order_id else '',
                        'redeem_date': datetime.strptime(use_card_line_id.using_id.redeem_date, '%Y-%m-%d %H:%M:%S') + timedelta(hours=7),
                        'service_name': use_card_line_id.service_id.name,
                        'quantity': use_card_line_id.quantity,
                        'uom_name': use_card_line_id.uom_id.name,
                        'employee': employee[1:] if employee else '',
                        'using_name': use_card_line_id.using_id.name,
                        'serial_name': use_card_line_id.serial_id.name if use_card_line_id.serial_id else '',
                        'price_unit': int(use_card_line_id.price_unit),
                        'state': use_card_line_ids.state,
                        'customer_sign': use_card_line_id.using_id.signature_image,
                        'note': use_card_line_id.note if use_card_line_id.note else '',
                        'type': use_card_line_id.using_id.type,
                        'using_id': use_card_line_ids.id,
                    }
                    card_details.append(vals3)
            lot = self.env['stock.production.lot'].sudo().search([('x_customer_id', '=', partner_id)], order='id desc')
            for index in lot:
                for line in index:
                    use_card_line_obj = self.env['izi.service.card.using.line'].sudo().search(
                        [('serial_id', '=', line.id)], order='id desc')
                    for use_card_line_id in use_card_line_obj:
                        employee = ''
                        for x in use_card_line_id.employee_ids:
                            employee = employee + ', ' + str(x.name)
                        for y in use_card_line_id.doctor_ids:
                            employee = employee + ', ' + str(y.name)
                        vals3 = {
                            'redeem_date': datetime.strptime(use_card_line_id.using_id.redeem_date, '%Y-%m-%d %H:%M:%S') + timedelta(hours=7),
                            'service_name': use_card_line_id.service_id.name,
                            'quantity': use_card_line_id.quantity,
                            'uom_name': use_card_line_id.uom_id.name,
                            'employee': employee[1:] if employee else '',
                            'using_name': use_card_line_id.using_id.name,
                            'serial_name': use_card_line_id.serial_id.name if use_card_line_id.serial_id else '',
                            'price_unit': int(use_card_line_id.price_unit),
                            'state': use_card_line_id.using_id.state,
                            'customer_sign': use_card_line_id.using_id.signature_image,
                            'note': use_card_line_id.note if use_card_line_id.note else '',
                            'type': 'card',
                            'using_id': use_card_line_id.using_id.id,
                        }
                        card_details.append(vals3)

        def custom_sort(elem):
            return elem['using_id']

        card_details.sort(key=custom_sort,reverse=True)
        return card_details