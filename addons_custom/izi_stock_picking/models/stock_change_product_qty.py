
from odoo import api, models, fields, tools,_
from odoo.exceptions import UserError

class izi_stock_change_product_qty(models.TransientModel):
    _inherit= 'stock.change.product.qty'

    @api.model
    def default_get(self, fields):
        res = super(izi_stock_change_product_qty, self).default_get(fields)
        if not res.get('product_id') and self.env.context.get('active_id') and self.env.context.get(
                'active_model') == 'product.template' and self.env.context.get('active_id'):
            res['product_id'] = self.env['product.product'].search(
                [('product_tmpl_id', '=', self.env.context['active_id'])], limit=1).id
        elif not res.get('product_id') and self.env.context.get('active_id') and self.env.context.get(
                'active_model') == 'product.product' and self.env.context.get('active_id'):
            res['product_id'] = self.env['product.product'].browse(self.env.context['active_id']).id
        # if 'location_id' in fields and not res.get('location_id'):
        #     company_user = self.env.user.company_id
        #     warehouse = self.env['stock.warehouse'].search([('company_id', '=', company_user.id)], limit=1)
        #     if warehouse:
        #         res['location_id'] = warehouse.lot_stock_id.id
        return res
