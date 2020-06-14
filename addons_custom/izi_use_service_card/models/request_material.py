from odoo import models, fields, api, _
from datetime import datetime, timedelta, date
from odoo.exceptions import except_orm


class PosRequestMaterial(models.Model):
    _name = "pos.request.material"
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char("Name", default='/', track_visibility='onchange')
    date = fields.Date("Date", track_visibility='onchange')
    employee_ids = fields.Many2many('hr.employee', string="Employee", track_visibility='onchange')
    origin = fields.Char("Origin", track_visibility='onchange')
    using_service_id = fields.Many2one('izi.service.card.using', "Using service", track_visibility='onchange')
    # state = fields.Selection([('draft', "Draft"), ('wait_material', "Wait Material"), ('wait_confirm', "Wait Confirm"),
    #                           ('exported', "Exported"), ('adjust', "Adjust"), ('done', "Done"), ('cancel', "Cancel")],
    #                          default='draft', track_visibility='onchange')
    request_material_ids = fields.One2many('pos.request.material.line', 'request_material_id', "Use Move Line")
    # adjust_active = fields.Boolean('Adjust Active', default=False, track_visibility='onchange')
    # picking_id = fields.Many2one('stock.picking', "Picking", track_visibility='onchange')
    # check_send = fields.Boolean("Check send", default=False)
    type = fields.Selection([('output', "OutPut"), ('input', "Input")], default='output', track_visibility='onchange')
    customer_id = fields.Many2one('res.partner', "Customer", track_visibility='onchange')
    service_ids = fields.Many2many('product.product', string="Service", track_visibility='onchange')
    quantity = fields.Float("Quantity")
    src_location = fields.Many2one('stock.location', "Location")
    picking_type_id = fields.Many2one('stock.picking.type', "Stock Picking Type")

    @api.model
    def create(self, vals):
        if vals.get('name', _('New')) == _('New'):
            vals['name'] = self.env['ir.sequence'].next_by_code('pos.request.material') or _('New')
        return super(PosRequestMaterial, self).create(vals)

    @api.onchange('service_ids')
    def onchange_service(self):
        count_service_pttm = 0
        count_service = 0
        for line in self.service_ids:
            if line.product_tmpl_id.categ_id.x_category_code == '109' or line.product_tmpl_id.categ_id.parent_id.x_category_code == '109' or line.product_tmpl_id.categ_id.parent_id.parent_id.x_category_code == '109':
                count_service_pttm += 1
                self.picking_type_id = self.using_service_id.pos_session_id.config_id.x_cosmetic_surgery_picking_type.id
            else:
                count_service += 1
                self.picking_type_id = self.using_service_id.pos_session_id.config_id.x_material_picking_type_id.id
        if count_service_pttm != 0 and count_service != 0:
            raise except_orm("Cảnh báo!",
                             ("Bạn không thể lập phiếu yêu cầu nguyên vật liệu cho dịch vụ xuất từ 2 kho khách nhau"))
    @api.multi
    def action_send_request_material(self):
        using_stock_move = self.env['izi.using.stock.move.line']
        use_material_obj = self.env['pos.user.material']
        argvss = {
            'employee_ids': [(4, x.id) for x in self.employee_ids],
            'using_service_id': self.using_service_id.id,
            'date': self.date,
            'origin': self.name,
            'customer_id': self.customer_id.id,
            'service_ids': [(4, x.id) for x in self.service_ids],
            'quantity': self.quantity,
            'picking_type_id': self.picking_type_id.id
        }
        use_material_id = use_material_obj.create(argvss)
        for i in self.request_material_ids:
            request_material_line_obj = self.env['izi.using.stock.move.line'].search(
                [('use_material_id', '=', use_material_id.id),
                 ('material_id', '=', i.material_id.id)])
            if request_material_line_obj:
                request_material_line_obj.quantity += i.quantity
            else:
                if i.material_id.product_tmpl_id.uom_id.id != i.uom_id.id:
                    raise except_orm("Cảnh báo!", (
                        "Cấu hình đơn vị của nguyên vật liệu xuất khác với đơn vị tồn kho. Vui lòng kiểm tra lại"))
                argvs = {
                    'material_id': i.material_id.id,
                    'quantity': i.quantity,
                    'uom_id': i.uom_id.id,
                    'use_material_id': use_material_id.id,
                    'use': True
                }
                using_stock_move.create(argvs)

class PosRequestmaterialLien(models.Model):
    _name = "pos.request.material.line"

    name = fields.Char("Name")
    material_id = fields.Many2one('product.product', "Material", domain=[('type', '!=', 'service')])
    quantity = fields.Float("Quantity")
    uom_id = fields.Many2one('product.uom', 'Product Uom')
    # using_id = fields.Many2one('izi.service.card.using', "Using")
    request_material_id = fields.Many2one('pos.request.material', 'Use Material', ondelete='cascade')

    @api.onchange('material_id')
    def onchange_material_id(self):
        self.uom_id = self.material_id.product_tmpl_id.uom_id.id
