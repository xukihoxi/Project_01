 # -*- coding: utf-8 -*-

from odoo import api, fields, models, SUPERUSER_ID, _
from datetime import date
from odoo.exceptions import UserError, ValidationError, MissingError, except_orm


class AccountInvoice(models.Model):
    _inherit = "account.invoice"

    x_pos_order_id = fields.Many2one('pos.order', readonly=True)

    def action_invoice_payment(self):
        # Kiểm tra mở phiên
        session = self.env['pos.session'].search([('config_id', '=', self.env.user.x_pos_config_id.id), ('state', '=', 'opened')], limit=1)
        if not session:
            raise MissingError("Chưa mở phiên, bạn không thể thực hiện thu công nợ của khách hàng!")
        ctx = dict(self._context or {})
        invoice_id = ctx.get('invoice_id', False)
        invoice_obj = self.env['account.invoice']
        invoice = invoice_obj.browse(invoice_id)
        if not invoice: raise except_orm('Thông báo', 'Không tìm thấy hóa đơn có id: %s' % (str(invoice_id),))
        ctx.update({
            'default_invoice_id': invoice_id,
            'default_session_id': session.id,
            'default_amount': invoice.residual,
            'readonly_by_pass': True,
        })
        return {
            'name': _('Payment'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'invoice.make.payment',
            'view_id': self.env.ref('izi_pos_custom_backend.view_invoice_make_payment_form').id,
            'target': 'new',
            'context': ctx,
        }
