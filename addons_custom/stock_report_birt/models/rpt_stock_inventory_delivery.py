# -*- coding: utf-8 -*-

from odoo import models, fields, api,_
from datetime import datetime
from odoo.exceptions import ValidationError, except_orm


class RptStockInventoryDelivery(models.TransientModel):
    _name = 'rpt.stock.inventory.delivery'

    from_date = fields.Date("From Date")
    to_date = fields.Date("To Date")
    select_all_partner = fields.Boolean('All Partner')
    partner_ids = fields.Many2many('res.partner', string="Partner")
    select_all_delivery_reason = fields.Boolean("All Reason")
    delivery_reason_ids = fields.Many2many('stock.picking.reason', string="Delivery Reason")
    type = fields.Selection([('in', "IN"), ('out', "Out")], default='out')
    select_all_location = fields.Boolean("All Location")
    location_ids = fields.Many2many('stock.location', string="Location")

    @api.onchange('select_all_partner')
    def _onchange_select_all_partner(self):
        if self.select_all_partner:
            user_obj = self.env['res.users']
            TeamObj = self.env['crm.team']
            PartnerObj = self.env['res.partner']
            EmployeeObj = self.env['hr.employee']
            partner_ids = []
            user = user_obj.search([('id', '=', self._uid)])
            if not user.branch_ids: raise except_orm('Thông báo', 'Người dùng %s chưa chọn chi nhánh cho phép. Vui lòng liên hệ quản trị để được giải quyết' % (
                                                           str(user.name)))
            for branch in user.branch_ids:
                if not branch: raise except_orm('Thông báo', 'Chi nhánh %s chưa chọn thương hiệu. Vui lòng liên hệ quản trị để được giải quyết' % (
                                                                        str(branch.name)))
            branch_ids = [user.branch_id and user.branch_id.id or 0]
            for branch in user.branch_ids:
                branch_ids.append(branch.id)

            team_ids = TeamObj.get_team_ids_by_branches(branch_ids)
            # brand_ids = BrandObj.get_brand_ids_by_branches(branch_ids)
            # - Lấy các partner của các người dùng mà được gắn vào nhân viên là bác sĩ
            employees = EmployeeObj.search([('job_id.x_code', '=', 'BS')])
            for employee in employees:
                partner_ids.append(employee.user_id.partner_id.id)
            # - Lấy các partner của các người dùng có chọn chi nhánh thuộc chi nhánh cho phép của người đăng nhập
            users_in_branches = user_obj.search([('branch_id', 'in', branch_ids)])
            for u in users_in_branches:
                partner_ids.append(u.partner_id.id)
            # - Lấy các partner có nhóm bán hàng có chi nhánh thuộc các chi nhánh cho phép của người đăng nhập
            partners = PartnerObj.search([('x_crm_team_id', 'in', team_ids)])
            for partner in partners:
                partner_ids.append(partner.id)
            self.partner_ids = PartnerObj.search([('id', 'in', partner_ids)])
        else:
            self.partner_ids = False

    @api.onchange('select_all_delivery_reason')
    def _onchange_select_all_delivery_reason(self):
        if self.select_all_delivery_reason:
            self.delivery_reason_ids = self.env['stock.picking.reason'].search([])
        else:
            self.delivery_reason_ids = False

    @api.onchange('select_all_location')
    def _onchange_select_all_location(self):
        if self.select_all_delivery_reason:
            self.location_ids = self.env['stock.location'].search([('user_ids', 'child_of', [self._uid]), ('usage', '=', 'internal')])
        else:
            self.location_ids = False
    # @api.onchange('location_ids')
    # def onchange_location(self):
    #     if self._uid != 1:
    #         list = []
    #         user_obj = self.env['res.users'].search([('id', '=', self._uid)])
    #         locations = self.env['stock.location'].search(
    #             [('branch_id', 'in', user_obj.branch_ids.ids), ('usage', '=', 'internal')])
    #         for location_id in locations:
    #             list.append(location_id.id)
    #         return {
    #             'domain': {'location_ids': [('id', 'in', list)]}
    #         }

    @api.multi
    def create_report(self):
        param_obj = self.env['ir.config_parameter']
        url = param_obj.get_param('birt_url')
        if not url:
            raise ValidationError(_(u"Bạn phải cấu hình birt_url"))
        report_name = "rpt_girft_to_customer.rptdesign"
        param_str1 = "&from_date=" + self.from_date + "&to_date=" + self.to_date
        param_str3 = "&partner_id="
        param_str4 = "&delivery_reason="
        param_str5 = "&type=" + self.type
        param_str6 = "&location_id="
        # if (self.select_all_partner == True):
        #     param_str3 += str(0)
        # else:
        str_list_partner = ''
        for loc_id in self.partner_ids:
            str_list_partner += ',' + str(loc_id.id)
        param_str3 += (str_list_partner[1:])
        # if self.select_all_delivery_reason == True:
        #     param_str4 += str(0)
        # else:
        str_list_delivery_reason = ''
        for loc_id in self.delivery_reason_ids:
            str_list_delivery_reason += ',' + str(loc_id.id)
            param_str4 += (str_list_delivery_reason[1:])
        # if self.select_all_location == True:
        #     param_str6 += str(0)
        # else:
        str_list_location = ''
        for loc_id in self.location_ids:
            str_list_location += ',' + str(loc_id.id)
            param_str6 += (str_list_location[1:])
        param_str = param_str1 + param_str3 + param_str4 + param_str5 + param_str6
        return {
            'type': 'ir.actions.act_url',
            'url': url + "/report/frameset?__report=report_amia/" + report_name + param_str,
            'target': 'new',
        }

    @api.multi
    def create_report_excel(self):
        param_obj = self.env['ir.config_parameter']
        url = param_obj.get_param('birt_url')
        if not url:
            raise ValidationError(_(u"Bạn phải cấu hình birt_url"))
        report_name = "rpt_girft_to_customer.rptdesign"
        param_str1 = "&from_date=" + self.from_date + "&to_date=" + self.to_date
        param_str3 = "&partner_id="
        param_str4 = "&delivery_reason="
        param_str5 = "&type=" + self.type
        param_str6 = "&location_id="
        # if (self.select_all_partner == True):
        #     param_str3 += str(0)
        # else:
        str_list_partner = ''
        for loc_id in self.partner_ids:
            str_list_partner += ',' + str(loc_id.id)
        param_str3 += (str_list_partner[1:])
        # if self.select_all_delivery_reason == True:
        #     param_str4 += str(0)
        # else:
        str_list_delivery_reason = ''
        for loc_id in self.delivery_reason_ids:
            str_list_delivery_reason += ',' + str(loc_id.id)
            param_str4 += (str_list_delivery_reason[1:])
        # if self.select_all_location == True:
        #     param_str6 += str(0)
        # else:
        str_list_location = ''
        for loc_id in self.location_ids:
            str_list_location += ',' + str(loc_id.id)
            param_str6 += (str_list_location[1:])
        param_str = param_str1 + param_str3 + param_str4 + param_str5 + param_str6
        return {
            'type': 'ir.actions.act_url',
            'url': url + "/report/frameset?__report=report_amia/" + report_name + param_str + '&__format=xlsx',
            'target': 'new',
        }

