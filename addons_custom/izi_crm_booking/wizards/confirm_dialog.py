# -*- coding: utf-8 -*-
# Created by Hoanglv on 9/4/2019

from odoo import api, fields, models

from addons_custom.izi_message_dialog.message_dialog_config import MessageDialogConfig


class ConfirmDialog(models.TransientModel):
    _name = 'confirm.dialog'
    _inherit = ['message.dialog']

    message = fields.Text(string='Message')

    def get_no_sale_confirm_dialog(self):
        view_id = self.env.ref('izi_crm_booking.meeting_no_sale_confirm_dialog').id
        ctx = self._context.copy()
        ctx.update({
            'dialog_size': MessageDialogConfig.MessageDialogSize.SMALL,
            'izi_dialog': True,
            'izi_type': MessageDialogConfig.MessageDialogType.ERROR
        })
        return {
            'name': 'Would you like to create another meeting?',
            'type': 'ir.actions.act_window',
            'res_model': 'confirm.dialog',
            'view_type': 'form',
            'view_mode': 'form',
            'views': [(view_id, 'form')],
            'target': 'new',
            'context': ctx,
        }

    @api.multi
    def action_yes(self):
        meeting_id = self._context.get('meeting_id')
        action_state = self._context.get('action_state')
        meeting = self.env['service.booking'].browse(meeting_id)
        if meeting.type == 'meeting':
            if action_state == 'no_sale':
                meeting.state = 'no_sale'
            else:
                meeting.state = 'cancel'
        else:
            meeting.state = 'cancel'

        view_id = self.env.ref('izi_crm_booking.service_booking_form_view').id
        ctx = self._context.copy()
        if meeting.type == 'meeting':
            ctx.update({'default_customer_id': ctx.get('customer_id'),
                        'default_parent_id': meeting.id,
                        'default_crm_lead_id': meeting.crm_lead_id.id if meeting.crm_lead_id else False,
                        'default_type': 'meeting'})
        else:
            ctx.update({'default_customer_id': ctx.get('customer_id'),
                        'default_parent_id': meeting.id,
                        'default_crm_lead_id': meeting.crm_lead_id.id if meeting.crm_lead_id else False,
                        'default_type': 'service'})
        return {
            'name': 'Meeting',
            'type': 'ir.actions.act_window',
            'res_model': 'service.booking',
            'view_type': 'form',
            'view_mode': 'form',
            'views': [(view_id, 'form')],
            'target': 'current',
            'context': ctx,
        }

    @api.multi
    def action_no(self):
        view_id = self.env.ref('izi_crm_booking.message_form_dialog').id
        ctx = self._context.copy()
        ctx.update({
            'dialog_size': MessageDialogConfig.MessageDialogSize.MEDIUM,
            'izi_dialog': True,
            'izi_type': MessageDialogConfig.MessageDialogType.ERROR
        })
        return {
            'name': 'Why not create a new meeting?',
            'type': 'ir.actions.act_window',
            'res_model': 'confirm.dialog',
            'view_type': 'form',
            'view_mode': 'form',
            'views': [(view_id, 'form')],
            'target': 'new',
            'context': ctx,
        }

    @api.multi
    def action_save_region(self):
        meeting_id = self._context.get('meeting_id')
        meeting = self.env['service.booking'].browse(meeting_id)
        action_state = self._context.get('action_state')
        if action_state == 'no_sale':
            meeting.write({'reason_no_sale': self.message,
                           'state': 'no_sale'})
        else:
            meeting.write({'reason_no_sale': self.message,
                           'state': 'cancel'})
        if meeting.crm_lead_id:
            meeting.crm_lead_id.action_set_lost()
