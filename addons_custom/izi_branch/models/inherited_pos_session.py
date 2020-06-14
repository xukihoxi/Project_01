# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, SUPERUSER_ID,  _
from odoo.exceptions import UserError, except_orm


class pos_session(models.Model):
    _inherit = 'pos.session'

    '''@api.model
    def _get_pos_session_default_branch(self):
        user_pool = self.env['res.users']
        branch_id = user_pool.browse(self.env.uid).branch_id.id  or False
        return branch_id'''

    @api.model
    def create(self, vals):
        user_pool = self.env['res.users']
        if not user_pool.browse(self.env.uid).branch_id: raise except_orm('Thông báo', 'Tài khoản người dùng %s chưa chọn chi nhánh. Vui lòng liên hệ Admin để được giải quyết!' % (str(user_pool.browse(self.env.uid).name)))
        vals['branch_id'] = ('branch_id' in vals) and vals['branch_id'] or user_pool.browse(self.env.uid).branch_id.id
        res = super(pos_session, self).create(vals)
        for line in res.statement_ids:
            line.branch_id = res.branch_id.id
        return res

    @api.multi
    def action_pos_session_close(self):
        # Close CashBox
        for session in self:
            company_id = session.config_id.company_id.id
            ctx = dict(self.env.context, force_company=company_id, company_id=company_id,session=self)
            for st in session.statement_ids:
                if abs(st.difference) > st.journal_id.amount_authorized_diff:
                    # The pos manager can close statements with maximums.
                    if not self.user_has_groups("point_of_sale.group_pos_manager"):
                        raise UserError(_("Your ending balance is too different from the theoretical cash closing (%.2f), the maximum allowed is: %.2f. You can contact your manager to force it.") % (st.difference, st.journal_id.amount_authorized_diff))
                # if (st.journal_id.type not in ['bank', 'cash']):
                #     raise UserError(_("The journal type for your payment method should be bank or cash."))
                st.with_context(ctx).sudo().button_confirm_bank()
        self.with_context(ctx)._confirm_orders()
        self.write({'state': 'closed'})
        return {
            'type': 'ir.actions.client',
            'name': 'Point of Sale Menu',
            'tag': 'reload',
            'params': {'menu_id': self.env.ref('point_of_sale.menu_point_root').id},
        }

    @api.onchange('config_id')
    def _onchange_config_id(self):
        self.branch_id = self.config_id.pos_branch_id.id

    branch_id = fields.Many2one('res.branch', 'Branch')  
