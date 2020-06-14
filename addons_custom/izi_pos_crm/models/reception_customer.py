# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError, except_orm, ValidationError


class ReceptionCustomer(models.Model):
    _name = 'reception.customer'
    _description = "Reception customer"
    _order = 'create_date DESC'

    name = fields.Char(string='Keyword')
    name_of_lead = fields.Char(string='Name of Lead')
    phone_number = fields.Char(string='Phone number')
    partner_name = fields.Char(string="Partner name")
    address = fields.Char(string="Address")
    birthday = fields.Date(string="Birthday")
    email = fields.Char(string="Email")
    partner_id = fields.Many2one('res.partner', string="Partner")
    lead_ids = fields.Many2many('crm.lead', string="Leads")
    count_lead = fields.Integer(string="Count lead")
    search_result = fields.Selection([('not_search', 'Not search'), ('not_found', 'Not Found'), ('found_one', 'Found one'), ('found_many', 'Found many')], default="not_search", string="Search result")
    user_id = fields.Many2one('res.users',string='User')
    team_id = fields.Many2one('crm.team', string='Team')
    campaign_id = fields.Many2one('utm.campaign', string="Campaign")
    date_meeting = fields.Datetime(string='Date')
    note = fields.Text(string='Note')
    state = fields.Selection([('new', 'New'), ('done', 'Done')], default='new',string='State')

    @api.multi
    def action_search_lead(self):
        Obj_lead = self.env['crm.lead']
        UserObj = self.env['res.users']
        TeamObj = self.env['crm.team']
        user = UserObj.search([('id', '=', self._uid)], limit=1)
        branch_ids = [user.branch_id and user.branch_id.id or 0]
        for branch in user.branch_ids:
            branch_ids.append(branch.id)
        team_ids = TeamObj.get_team_ids_by_branches(branch_ids)
        leads = Obj_lead.search(['|', ('partner_name', 'ilike', self.name), ('phone', '=', self.name), ('x_state', 'in', ['opportunity', 'meeting']), ('team_id', 'in', team_ids)])
        if not self.name or self.name.strip() == '': raise except_orm("Thông báo", "Bạn phải nhập tên hoặc số điện thoại của khách hàng.")
        if not leads:
            self.search_result = 'not_found'
            self.name_of_lead = False
            self.birthday = False
            self.address = False
            self.email = False
            self.partner_id = False
            self.note = False
            self.user_id = False
            self.team_id = False
            self.lead_ids = False
            if self.name.replace(' ', '').isalpha():
                self.partner_name = self.name
                self.phone_number = False
            else:
                self.partner_name = False
                self.phone_number = self.name
            return {
                'effect': {
                    'message': "Không tìm thấy một kết quả cho  từ khóa '%s' " % (str(self.name)),
                    'img_url': 'izi_pos_crm/static/src/img/sad_face.png',
                }
            }
        elif len(leads) == 1:
            self.search_result = 'found_one'
            self.name_of_lead = leads.name
            self.lead_ids = leads
            self.partner_name = leads.partner_name
            self.phone_number = leads.phone
            self.birthday = leads.x_birthday
            self.address = leads.street
            self.email = leads.partner_id and leads.partner_id.email or ''
            self.partner_id = leads.partner_id and leads.partner_id.id or False
            self.date_meeting = leads.time_booking
            self.note = leads.description
            self.user_id = leads.user_id
            self.team_id = leads.team_id
            return {
                'effect': {
                    'fadeout': 'slow',
                    'message': "Tìm thấy một kết quả cho  từ khóa '%s' " % (str(self.name)),
                }
            }
        elif len(leads) > 1:
            self.search_result = 'found_many'
            self.lead_ids = leads
            return {
                'effect': {
                    'fadeout': 'slow',
                    'message': "Tìm thấy %s kết quả cho  từ khóa '%s' " % (len(self.lead_ids),str(self.name)),
                }
            }
        else:
            raise except_orm("Thông báo", "Có lỗi xảy ra! Tìm thấy %s lead" % (str(len(leads))))

    @api.multi
    def action_create_lead(self):
        self.search_result = 'not_search'
        self.partner_name = False
        self.phone_number = False
        self.birthday = False
        self.address = False
        self.email = False
        self.partner_id = False
        self.note = False
        self.user_id = False
        self.team_id = False
        self.lead_ids = False

    @api.multi
    def action_assign_lead(self):
        if self.search_result == 'not_search' or self.search_result == 'not_found':
            if not self.team_id or not self.user_id:
                raise except_orm("Thông báo", "Bạn phải nhập nhóm bán hàng và nhân viên bán hàng trước khi giao lead")
            self.env['crm.lead'].create({
                'name': self.name_of_lead,
                'partner_name': self.partner_name,
                'phone': self.phone_number,
                'x_birthday': self.birthday,
                'email_from': self.email,
                'description': self.note,
                'street': self.address,
                'user_id': self.user_id.id,
                'team_id': self.team_id.id,
                'x_state': 'to_shop',
            })
            self.state = 'done'
        elif self.search_result == 'found_one':
            if not self.team_id or not self.user_id:
                raise except_orm("Thông báo", "Bạn phải nhập nhóm bán hàng và nhân viên bán hàng trước khi giao lead")
            for lead in self.lead_ids:
                if lead.service_booking_ids:
                    for service_booking in lead.service_booking_ids:
                        if service_booking.state == 'ready':
                            service_booking.write({'state': 'met'})
                lead.update({
                    'user_id': self.user_id.id,
                    'team_id': self.team_id.id,
                    'x_state': 'to_shop',
                })
            self.state = 'done'
        elif self.search_result == 'found_many':
            #Không chọn các lead khác sdt
            phones = [self.lead_ids[0].phone]
            for lead in self.lead_ids:
                if lead.phone not in phones:
                    raise except_orm("Thông báo", "Nếu tìm thấy nhiều cơ hội bán hàng, hệ thống sẽ tự động trộn lại khi bạn bấm nút \"Giao lead\". "
                                                  "Nhưng các cơ hội này khác số điện thoại nên không thể trộn, bạn vui lòng xóa bớt các cơ hội không đúng để tiếp tục.")
                phones.append(lead.phone)
            #Không cho chọn nếu có  nhiều hơn 1 lịch hẹn ready
            count_service_booking = 0
            for lead in self.lead_ids:
                for service_booking in lead.service_booking_ids:
                    if service_booking.state == 'ready':
                        count_service_booking += 1
            if count_service_booking > 1:
                raise except_orm("Thông báo", "Nếu tìm thấy nhiều cơ hội bán hàng, hệ thống sẽ tự động trộn lại khi bạn bấm nút \"Giao lead\". "
                                              "Nhưng trong các lead bạn đã xác định trộn thì có nhiều hơn 1 lead có lịch hẹn nên không thể trộn, vui lòng xóa bớt các lead vi phạm để tiếp tục.")


            #Mở popup chọn nhân viên tư vấn và fill đầy đủ dữ liệu
            # self.partner_name = ''
            lead_host = self.lead_ids[0]
            for lead in self.lead_ids:
                for service_booking in lead.service_booking_ids:
                    if service_booking.state == 'ready':
                        lead_host = lead
                        break
            description_host = ''
            for lead in self.lead_ids:
                description_host += '%s \n' % (str(lead.description and lead.description or ''))
            self.note = description_host
            self.partner_name = lead_host.partner_name
            self.phone_number = lead_host.phone
            self.team_id = lead_host.team_id.id
            self.user_id = lead_host.user_id.id

            view_id = self.env.ref('izi_pos_crm.reception_customer_assign_form_view').id
            ctx = self._context.copy()
            ctx.update({
                'lead_host_id': lead_host.id,
            })
            return {
                'name': 'Giao lead',
                'type': 'ir.actions.act_window',
                'res_model': 'reception.customer',
                'res_id': self.id,
                'view_type': 'form',
                'view_mode': 'form',
                'views': [(view_id, 'form')],
                'target': 'new',
                'context': ctx,
            }
        else:
            raise except_orm("Thông báo", "Không tồn tại kết quả tìm kiếm %s vui lòng liên hệ Admin để được giải quyết!" % (str(self.search_result)))

    @api.multi
    def action_confirm(self):
        ctx = self._context.copy()
        lead_host_id = ctx.get('lead_host_id', False)
        if not lead_host_id: raise except_orm("Thông báo", "Không nhận được lead gốc, vui lòng liên hệ Admin để được giải quyết. lead_host_id: %s" % (str(lead_host_id)))
        lead_host = self.env['crm.lead'].search([('id', '=', lead_host_id)], limit=1)
        if not lead_host: raise except_orm("Thông báo", "Không tìm thấy lead gốc theo id, vui lòng liên hệ Admin để được giải quyết. lead_host_id: %s" % (str(lead_host_id)))
        for lead in self.lead_ids:
            for interaction in lead.interaction_ids:
                interaction.write({'crm_lead_id': lead_host.id})
            if lead.id != lead_host.id:
                lead.write({'active': False})

        if lead_host.service_booking_ids:
            for service_booking in lead_host.service_booking_ids:
                if service_booking.state == 'ready':
                    service_booking.write({'state': 'met'})

        lead_host.write({
            'team_id': self.team_id.id,
            'user_id': self.user_id.id,
            'campaign_id': self.campaign_id.id,
            'description': self.note,
            'x_state': 'to_shop'
        })
        self.write({'state': 'done'})