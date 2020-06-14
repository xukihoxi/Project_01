# -*- coding: utf-8 -*-

from odoo import fields, models, api, _
from datetime import timedelta, datetime, date
from odoo.exceptions import ValidationError, except_orm


class UseServiceCard(models.Model):
    _inherit = 'izi.service.card.using'

    @api.multi
    def action_done(self):
        super(UseServiceCard, self).action_done()

        if self.type == 'card':
            self._create_partner_interaction(self.service_card_ids, True, True, True)
        elif self.type == 'service':
            self._create_partner_interaction(self.service_card1_ids, True, False, True)
        elif self.type == 'guarantee':
            self._create_partner_interaction(self.service_card1_ids, True, False, False)

    @api.multi
    def action_confirm_refund(self):
        super(UseServiceCard, self).action_confirm_refund()
        interactions = self.env['partner.interaction'].search([('using_id', '=', self.id), ('state', '=', 'draft')])
        for interaction in interactions:
            interaction.write({
                'state': 'cancel',
                'note': 'Đơn sử dụng dịch vụ %s bị hủy nên tự động hủy nhắc lịch này.' % (str(self.name)),
            })

    def _create_partner_interaction(self, service_card_ids, taking_care_after_do_service, remind, remind_guarantee):
        InteractionObj = self.env['partner.interaction']
        InteractionTypeObj = self.env['partner.interaction.type']

        type_remind = InteractionTypeObj.search([('name', '=', 'Nhắc lịch liệu trình')])
        type_taking_care_after_do_service = InteractionTypeObj.search(
            [('name', '=', 'Chăm sóc sau khi khách làm dịch vụ')])
        type_remind_guarantee = InteractionTypeObj.search([('name', '=', 'Nhắc lịch bảo hành')])

        if not type_remind: raise except_orm('Thông báo',
                                             'Chưa cấu hình loại tương tác khách hàng là: Nhắc lịch liệu trình')
        if not type_taking_care_after_do_service: raise except_orm('Thông báo',
                                                                   'Chưa cấu hình loại tương tác khách hàng là: Chăm sóc sau khi khách làm dịch vụ')
        if not type_remind_guarantee: raise except_orm('Thông báo',
                                                       'Chưa cấu hình loại tương tác khách hàng là: Nhắc lịch bảo hành')

        redeem_date = (datetime.strptime(self.redeem_date, '%Y-%m-%d %H:%M:%S') + timedelta(hours=7)).date()

        for service_card in service_card_ids:
            period_remind = 0
            period_taking_care_after_do_service = 0
            period_remind_guarantee = 0
            # lấy thời gian nhắc nhở theo cấu hình của dịch vụ
            if service_card.service_id.x_service_remind_ids:
                for service_remind in service_card.service_id.x_service_remind_ids:
                    if service_remind.type == 'remind': period_remind = service_remind.value
                    if service_remind.type == 'taking_care_after_do_service': period_taking_care_after_do_service = service_remind.value
                    if service_remind.type == 'remind_guarantee': period_remind_guarantee = service_remind.value

            interactions = InteractionObj.search([('state', '=', 'draft'), ('using_line_id.service_id', '=', service_card.service_id.id),
                ('partner_id', '=', self.customer_id.id),
                ('type_id', 'in', [type_remind.id,type_remind_guarantee.id])])
            # nếu có lịch nhắc liệu trình hoặc bảo hành ở trạng thái nháp thì hủy
            if interactions:
                for interaction in interactions:
                    note = ''
                    if interaction.type_id == type_remind:
                        note = 'Khách hàng đến làm liệu trình trước khi nhắc.'
                    elif interaction.type_id == type_remind_guarantee:
                        note = 'Khách hàng đến làm bảo hành trước khi nhắc.'
                    else: pass # Vô lý không thể như vậy được
                    interaction.write({
                        'state': 'cancel',
                        'note': note,
                    })

            # nếu có cấu hình thời gian chăm sóc sau thì tạo tương tác
            if taking_care_after_do_service and period_taking_care_after_do_service:
                InteractionObj.create({
                    'partner_id': self.customer_id.id,
                    'type_id': type_taking_care_after_do_service.id,
                    'user_id': False,
                    'date': redeem_date + timedelta(days=period_taking_care_after_do_service),
                    'using_id': self.id,
                    'using_line_id': service_card.id,
                    'survey_id': type_taking_care_after_do_service.survey_id.id,
                })
            for card_detail in service_card.serial_id.x_card_detail_ids:
                # nếu còn liệu trình thì nhắc lịch
                if remind and period_remind and service_card.service_id.id == card_detail.product_id.id and card_detail.qty_hand > 0:
                    InteractionObj.create({
                        'partner_id': self.customer_id.id,
                        'type_id': type_remind.id,
                        'user_id': False,
                        'date': redeem_date + timedelta(days=period_remind),
                        'using_id': self.id,
                        'using_line_id': service_card.id,
                        'survey_id': type_remind.survey_id.id,
                    })
                # nếu có cấu hình thời gian nhắc lịch bảo hành
                elif remind_guarantee and period_remind_guarantee and service_card.service_id.id == card_detail.product_id.id and card_detail.qty_hand == 0:
                    InteractionObj.create({
                        'partner_id': self.customer_id.id,
                        'type_id': type_remind_guarantee.id,
                        'user_id': False,
                        'date': redeem_date + timedelta(days=period_remind_guarantee),
                        'using_id': self.id,
                        'using_line_id': service_card.id,
                        'survey_id': type_remind_guarantee.survey_id.id,
                    })


class UseServiceCardLine(models.Model):
    _inherit = 'izi.service.card.using.line'

    @api.multi
    def action_create_interaction(self):
        view_id = self.env.ref('izi_crm_interaction.partner_interaction_form_view').id
        ctx = {
            'default_partner_id': self.using_id.customer_id.id,
            'default_date': datetime.today(),
            'default_user_id': self._uid,
            'default_using_id': self.using_id.id,
            'default_using_line_id': self.id,
        }

        return {
            'name': 'Partner interaction',
            'type': 'ir.actions.act_window',
            'res_model': 'partner.interaction',
            'view_type': 'form',
            'view_mode': 'form',
            'views': [(view_id, 'form')],
            'target': 'current',
            'context': ctx,
        }
