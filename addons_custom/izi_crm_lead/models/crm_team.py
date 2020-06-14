# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.tools.safe_eval import safe_eval


class IziCrmTeam(models.Model):
    _inherit = 'crm.team'

    x_member_ids = fields.Many2many('res.users',string='User')
    team_type = fields.Selection([('sales', 'Sales'), ('website', 'Website'), ('pos', 'Point of Sale'), ('uid_tele', 'UID - Telesales')], string='Channel Type', default='pos',
                                 required=True,
                                 help="The type of this channel, it will define the resources this channel uses.")

    def get_team_ids_by_branches(self, branch_ids):
        team_ids = []
        branches = self.env['res.branch'].search([('id', 'in', branch_ids)])
        for branch in branches:
            teams = self.env['crm.team'].search([('x_branch_id', '=', branch.id)])
            if teams:
                for team in teams:
                    team_ids.append(team.id)
        return team_ids

    def get_all_employee_ids(self):
        employee_ids = []
        if self.x_member_ids:
            for member in self.x_member_ids:
                employee = self.env['hr.employee'].search([('user_id', '=', member.id)])
                if employee:
                    employee_ids.append(employee.id)
        return employee_ids

    # TODO JEM : refactor this stuff with xml action, proper customization,
    @api.model
    def action_your_pipeline(self):
        action = self.env.ref('izi_crm_lead.izi_crm_lead_opportunities_tree_view').read()[0]
        user_team_id = self.env.user.sale_team_id.id
        if not user_team_id:
            user_team_id = self.search([], limit=1).id
            action['help'] = """<p class='oe_view_nocontent_create'>Click here to add new opportunities</p><p>
            Looks like you are not a member of a sales channel. You should add yourself
            as a member of one of the sales channel.
        </p>"""
            if user_team_id:
                action[
                    'help'] += "<p>As you don't belong to any sales channel, Odoo opens the first one by default.</p>"

        action_context = safe_eval(action['context'], {'uid': self.env.uid})

        tree_view_id = self.env.ref('izi_crm_lead.izi_crm_case_tree_view_oppor').id
        form_view_id = self.env.ref('izi_crm_lead.izi_crm_case_form_view_oppor').id
        kanb_view_id = self.env.ref('izi_crm_lead.izi_crm_case_kanban_view_leads').id
        action['views'] = [
            [kanb_view_id, 'kanban'],
            [tree_view_id, 'tree'],
            [form_view_id, 'form'],
            [False, 'graph'],
            [False, 'calendar'],
            [False, 'pivot']
        ]
        action['context'] = action_context
        return action

    @api.model
    @api.returns('self', lambda value: value.id if value else False)
    def _get_default_team_id(self, user_id=None):
        if not user_id:
            user_id = self.env.uid
        company_id = self.sudo(user_id).env.user.company_id.id
        team_id = self.env['crm.team'].sudo().search([
            '|', ('user_id', '=', user_id), ('x_member_ids', '=', user_id),
            '|', ('company_id', '=', False), ('company_id', 'child_of', [company_id])
        ], limit=1)
        if not team_id and 'default_team_id' in self.env.context:
            team_id = self.env['crm.team'].browse(self.env.context.get('default_team_id'))
        if not team_id:
            default_team_id = self.env.ref('sales_team.team_sales_department', raise_if_not_found=False)
            if default_team_id and (self.env.context.get('default_type') != 'lead' or default_team_id.use_leads):
                team_id = default_team_id
        return team_id





