# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError


class InheritResUser(models.Model):
    _inherit = 'res.users'

    x_pos_config_id = fields.Many2one('pos.config', "Pos Config")


class InheritPosConfig(models.Model):
    _inherit = 'pos.config'

    x_users_ids = fields.One2many('res.users', 'x_pos_config_id', "User")
    x_material_picking_type_id = fields.Many2one('stock.picking.type', "Material Picking Type")
    x_cosmetic_surgery_picking_type = fields.Many2one('stock.picking.type', " Cosmetic Surgery Picking Type")
    x_auto_export_import_materials = fields.Boolean(string="Automatically import and export raw materials")
    x_auto_export_import_goods = fields.Boolean(string="Automatically import and export goods")

    # x_owner_id = fields.Many2one('res.partner', "Owner", domain=[('x_shop', '=', True)])
    # x_material_location_id = fields.Many2one('stock.location', "Material Location", domain=[('usage', '=', 'internal')])
    # x_surgery_location_id = fields.Many2one('stock.location', "Surgery Location", domain=[('usage', '=', 'internal')])

    journal_ids = fields.Many2many('account.journal', 'pos_config_journal_rel',
        'pos_config_id', 'journal_id', string='Available Payment Methods', domain="[('journal_user', '=', True )]")
    x_location_code = fields.Char('Mã chi nhánh',
                                  help="Mã này dùng để phân biệt khách ở các chi nhánh khác nhau, yêu cầu 2 kí tự!")
    x_category_ids = fields.Many2many('pos.category', string="Category")

    @api.model
    def create(self, vals):
        if vals.get('x_location_code'):
            vals['x_location_code'] = vals['x_location_code'].upper()
        else:
            raise UserError("Vui lòng cấu mã chi nhánh ở điểm bán hàng  !")
        return super(InheritPosConfig, self).create(vals)

    @api.multi
    def write(self, vals):
        self.ensure_one()
        if vals.get('x_location_code'):
            vals['x_location_code'] = vals['x_location_code'].upper()
        return super(InheritPosConfig, self).write(vals)


    @api.multi
    def open_ui(self):
        """ open the pos interface """
        self.ensure_one()
        ctx = self.env.context.copy()
        ctx.update({'default_session_id': self.current_session_id.id,
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
