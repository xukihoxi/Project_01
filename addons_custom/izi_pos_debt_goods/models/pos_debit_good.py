# -*- coding: utf-8 -*-
from werkzeug._internal import _log
from odoo import models, fields, api
from odoo.exceptions import ValidationError
from odoo.tools.translate import _
from odoo.exceptions import except_orm, Warning as UserError


class DebitGoods(models.Model):
    _name = "pos.debit.good"
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char("Name", default="New", copy=False, track_visibility='onchange')
    partner_id = fields.Many2one('res.partner', string="Partner")
    code = fields.Char(string='Code')
    old_code = fields.Char(string='Old code')
    phone = fields.Char(string='Phone')
    mobile = fields.Char(string='Mobile')
    picking_id = fields.Many2one('stock.picking')

    state = fields.Selection([('debit', 'Debited'),('approved','Approved'), ('waiting', 'Waiting'),('rate', 'Rate'),('done', 'Done')], 'State',
                             default='debit', track_visibility='onchange')

    line_ids = fields.One2many('pos.debit.good.line', 'debit_id',string="Line")
    history_ids = fields.One2many('pos.debit.good.history', 'debit_id',string="History")

    @api.model
    def create(self, vals):
        if vals.get('name', _('New')) == _('New'):
            vals['name'] = self.env['ir.sequence'].next_by_code('pos.debit.good') or _('New')
        return super(DebitGoods, self).create(vals)


    @api.multi
    def action_debit(self):
        if self.state != 'debit':
            return True
        pop_id  = self.env['pos.debit.good.transient'].create({'debit_id':self.id})
        for line in self.line_ids:
            if line.qty_debit > 0:
                vals= {
                    'order_id': line.order_id.id,
                    'product_id': line.product_id.id,
                    'qty_debit': line.qty_debit,
                    'qty_transfer': 0,
                    'line_id': pop_id.id,
                    'debit_line_id':line.id
                }
                self.env['pos.debit.good.transient.line'].create(vals)
        view = self.env.ref('izi_pos_debt_goods.view_debit_goods_transient')
        return {
            'name': _('Thẻ bảo hành'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'pos.debit.good.transient',
            'views': [(view.id, 'form')],
            'res_id': pop_id.id,
            'view_id': view.id,
            'target': 'new',
            'context': self.env.context,
        }
    @api.multi
    def action_cancel(self):
        if self.picking_id.state in ('done','cancel'):
            raise except_orm('Cảnh báo!', ('Đơn xuất kho đã hoàn thành hoặc hủy. Vui lòng liên hệ bộ phận kho để xác nhận'))
        self.picking_id.action_cancel()
        for line in self.line_ids:
            line.qty_transfer = 0
        self.picking_id = False
        self.state = 'debit'
        return True

    @api.multi
    def action_cancel_approved(self):
        self.state = 'debit'
        return True

    @api.multi
    def action_done(self):
        his = self.env['pos.debit.good.history'].search([('picking_id','=',self.picking_id.id)],limit=1)
        view = self.env.ref('izi_pos_debt_goods.view_pos_debit_good_history')
        return {
            'name': _('Khách hàng xác nhận'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'pos.debit.good.history',
            'views': [(view.id, 'form')],
            'res_id': his.id,
            'view_id': view.id,
            'target': 'new',
            'context': self.env.context,
        }

    @api.multi
    def action_approved(self):
        if self.state != 'approved':
            return True
        pop_id = self.env['pos.debit.good.transient.approved'].create({'debit_id': self.id})
        for line in self.line_ids:
            if line.qty_debit > 0:
                vals = {
                    'order_id': line.order_id.id,
                    'product_id': line.product_id.id,
                    'qty_debit': line.qty_debit,
                    'qty_transfer': 0,
                    'line_id': pop_id.id,
                    'debit_line_id': line.id
                }
                self.env['pos.debit.good.transient.approved.line'].create(vals)
        view = self.env.ref('izi_pos_debt_goods.view_debit_goods_transient_approved')
        return {
            'name': _('Thẻ bảo hành'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'pos.debit.good.transient.approved',
            'views': [(view.id, 'form')],
            'res_id': pop_id.id,
            'view_id': view.id,
            'target': 'new',
            'context': self.env.context,
        }

