from odoo import models, api, fields , _
from odoo.exceptions import except_orm
from odoo.osv import expression

class ResPartnerCustom(models.Model):
    _inherit = 'res.partner'

    lot_ids = fields.One2many('stock.production.lot', 'x_customer_id', string="Lot Id")
    service_ids = fields.One2many('izi.service.card.detail', 'partner_id', string="Service")
    coupon_ids = fields.One2many('stock.production.lot', 'x_customer_id', string="Lot Id",domain=[('x_product__tmpl_id', '!=', False)])
