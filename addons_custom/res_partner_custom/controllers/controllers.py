# -*- coding: utf-8 -*-

from odoo import http
import logging
from odoo.exceptions import except_orm
import odoo.addons.web.controllers.main as base_main

_logger = logging.getLogger(__name__)


class DataSet(base_main.DataSet):
    def do_search_read(self, model, fields=False, offset=0, limit=False, domain=None, sort=None, context=None):
        uid = http.request.env.uid
        cr = http.request.cr
        UserObj = http.request.env['res.users']
        TeamObj = http.request.env['crm.team']
        BrandObj = http.request.env['res.brand']
        ObjPartner = http.request.env['res.partner']
        user = UserObj.sudo().search([('id', '=', uid)], limit=1)

        #Các hàm tính năng
        def _get_teams_of_user(uid):
            team_ids = []
            query = ''' SELECT a.id FROM crm_team a LEFT JOIN crm_team_res_users_rel b ON b.crm_team_id = a.id WHERE b.res_users_id = %s '''
            cr.execute(query, (uid, ))
            res = cr.dictfetchall()
            if not res: raise except_orm('Thông báo', 'Tài khoản người dùng %s không thuộc nhóm bán hàng nào. Liên hệ quản trị viên để được giải quyết' % ())
            for r in res:
                team_ids.append(r['id'])

            return team_ids

        if domain == None:
            domain = []
        if model == 'res.partner':
            group_leader_shop = UserObj.has_group('izi_res_permissions.group_leader_shop')
            group_consultant = UserObj.has_group('izi_res_permissions.group_consultant')
            group_inventory_accounting = UserObj.has_group('izi_res_permissions.group_inventory_accounting')
            group_cashier = UserObj.has_group('izi_res_permissions.group_cashier')
            group_therapist = UserObj.has_group('izi_res_permissions.group_therapist')
            group_receptionist = UserObj.has_group('izi_res_permissions.group_receptionist')
            group_member_uid_telesales = UserObj.has_group('izi_res_permissions.group_member_uid_telesales')

            group_revenue_control = UserObj.has_group('izi_res_permissions.group_revenue_control')
            group_business_manager = UserObj.has_group('izi_res_permissions.group_business_manager')
            group_revenue_accountant = UserObj.has_group('izi_res_permissions.group_revenue_accountant')
            group_cost_accountant = UserObj.has_group('izi_res_permissions.group_cost_accountant')

            if not user.branch_ids: raise except_orm('Thông báo', 'Người dùng %s chưa chọn chi nhánh cho phép. Vui lòng liên hệ quản trị để được giải quyết' % (
                                                               str(user.name)))
            for branch in user.branch_ids:
                if not branch: raise except_orm('Thông báo', 'Chi nhánh %s chưa chọn thương hiệu. Vui lòng liên hệ quản trị để được giải quyết' % (
                                                                        str(branch.name)))
            branch_ids = [user.branch_id and user.branch_id.id or 0]
            for branch in user.branch_ids:
                branch_ids.append(branch.id)
            team_ids = TeamObj.get_team_ids_by_branches(branch_ids)
            brand_ids = BrandObj.get_brand_ids_by_branches(branch_ids)

            if not (uid == 1):
                if group_revenue_control:
                    domain = domain
                elif group_cost_accountant or group_revenue_accountant or group_business_manager or group_receptionist or group_cashier or group_leader_shop or group_inventory_accounting or group_member_uid_telesales:
                    phone = ''
                    for item in domain:
                        if phone: break
                        if type(item) is list:
                            for attr in item:
                                if attr == 'phone':
                                    phone = item[2]
                                    break
                    if phone:
                        partner = ObjPartner.search(['|', ('phone', '=', phone), ('mobile', '=', phone), ('x_brand_id', 'in', brand_ids)], limit=1)
                        if partner:
                            domain = [('id', '=', partner.id)]
                        else:
                            domain += [('x_crm_team_id', 'in', team_ids)]
                    else:
                        domain += [('x_crm_team_id', 'in', team_ids)]
                elif group_consultant or group_therapist:
                    domain += [('user_id', '=', user.id)]
                else:
                    domain = [('id', '=', 0)]

        return super(DataSet, self).do_search_read(model, fields, offset, limit, domain, sort)

