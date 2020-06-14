
from odoo import models, fields, api
from odoo.exceptions import except_orm


class UseServiceQweb(models.Model):
    _inherit = 'izi.service.card.using'

    @api.multi
    def action_print(self):
        if self.pos_session_id.branch_id.brand_id.code in ['AMIA']:#Gangnam
            return {
                'type': 'ir.actions.act_url',
                'url': 'report/pdf/report_qweb.report_template_invoice_use_service_view_gangnam/%s' %(self.id),
                'target': 'new',
                'res_id': self.id,
            }
        else:
            raise except_orm('Thông báo', 'Chưa cấu hình phiếu in cho thương hiệu %s vui lòng liên hệ Admin để được giải quyết!' % (str(self.pos_session_id.branch_id.brand_id.name)))

    @api.multi
    def get_name_print_product(self, product):
        # TDE: this could be cleaned a bit I think
        # product = self.env['product.product'].search([('id', '=', product_id)])

        def _name_get(d):
            name = d.get('name', '')
            code = self._context.get('display_default_code', True) and d.get('default_code', False) or False
            if code:
                name = '[%s] %s' % (code, name)
            return name

        # partner_id = self._context.get('partner_id')
        # if partner_id:
        #     partner_ids = [partner_id, self.env['res.partner'].browse(partner_id).commercial_partner_id.id]
        # else:
        #     partner_ids = []
        #
        # # all user don't have access to seller and partner
        # # check access and use superuser
        # self.check_access_rights("read")
        # self.check_access_rule("read")

        result = []
        for product in product:
            # display only the attributes with multiple possible values on the template
            variable_attributes = product.attribute_line_ids.filtered(lambda l: len(l.value_ids) > 1).mapped(
                'attribute_id')
            variant = product.attribute_value_ids._variant_name(variable_attributes)

            name = variant and "%s (%s)" % (product.name, variant) or product.name
            # sellers = []
            # if partner_ids:
            #     sellers = [x for x in product.seller_ids if (x.name.id in partner_ids) and (x.product_id == product)]
            #     if not sellers:
            #         sellers = [x for x in product.seller_ids if (x.name.id in partner_ids) and not x.product_id]
            # if sellers:
            #     for s in sellers:
            #         seller_variant = s.product_name and (
            #                 variant and "%s (%s)" % (s.product_name, variant) or s.product_name
            #         ) or False
            #         mydict = {
            #             'id': product.id,
            #             'name': seller_variant or name,
            #             'default_code': s.product_code or product.default_code,
            #         }
            #         temp = _name_get(mydict)
            #         if temp not in result:
            #             result.append(temp)
            # else:
            mydict = {
                'id': product.id,
                'name': name,
                'default_code': product.default_code,
            }

        return _name_get(mydict)