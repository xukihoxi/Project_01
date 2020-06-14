# -*- coding: utf-8 -*-

from odoo import api, fields, models, SUPERUSER_ID, _
from datetime import date
from odoo.exceptions import UserError, ValidationError, MissingError


class PosSession(models.Model):
    _inherit = 'pos.session'

    def _confirm_orders(self):
        super(PosSession, self)._confirm_orders()
        for session in self:
            orders = session.order_ids.filtered(lambda order: order.state in ['invoiced'])
            orders.update({'state': 'done'})

    @api.multi
    def action_pos_session_close(self):
        # Ghi đè toàn bộ hàm ban đầu
        for session in self:
            company_id = session.config_id.company_id.id
            ctx = dict(self.env.context, force_company=company_id, company_id=company_id)
            for st in session.statement_ids:
                if abs(st.difference) > st.journal_id.amount_authorized_diff:
                    # The pos manager can close statements with maximums.
                    if not self.user_has_groups("point_of_sale.group_pos_manager"):
                        raise UserError(_(
                            "Your ending balance is too different from the theoretical cash closing (%.2f), the maximum allowed is: %.2f. You can contact your manager to force it.") % (
                                        st.difference, st.journal_id.amount_authorized_diff))
                if (st.journal_id.type not in ['bank', 'cash', 'general']):
                    raise UserError(_("The type of the journal for your payment method should be bank or cash "))
                st.with_context(ctx).sudo().button_confirm_bank()
            if self.picking_count != 0:
                raise UserError(_("Vui lòng hoàn thành hết các đơn xuất, nhập kho bán trước khi đóng phiên "))
        self.with_context(ctx)._confirm_orders()
        self.write({'state': 'closed'})
        return {
            'type': 'ir.actions.client',
            'name': 'Point of Sale Menu',
            'tag': 'reload',
            'params': {'menu_id': self.env.ref('point_of_sale.menu_point_root').id},
        }
        # Kết thúc ghi đè toàn bộ hàm ban đầu


    @api.multi
    def open_frontend_cb(self):
        if not self.ids:
            return {}
        for session in self.filtered(lambda s: s.user_id.id != self.env.uid):
            raise UserError(_("You cannot use the session of another user. This session is owned by %s. "
                              "Please first close this one to use this point of sale.") % session.user_id.name)
        self.ensure_one()
        ctx = self.env.context.copy()
        ctx.update({'default_session_id': self.id,
                    'default_user_id': self.env.uid})
        view = self.env.ref('point_of_sale.view_pos_pos_form')
        return {
            'name': _('Pos Order'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'pos.order',
            'views': [(view.id, 'form')],
            'view_id': view.id,
            'target': '',
            'context': ctx,
        }

