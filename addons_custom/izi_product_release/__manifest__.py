# -*- coding: utf-8 -*-
{
    'name': "Product release",

    'summary': """
        Phát hành thẻ DV, voucher, coupon ...""",

    'description': """
        Phát hành thẻ DV, voucher, coupon ...
    """,

    'author': "ERPViet",
    'website': "http://www.izisolution.vn",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'Stock',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base','stock','product','point_of_sale','utm'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'data/ir_sequence_data.xml',
        'views/product_template_custom.xml',
        'views/izi_product_release.xml',
        'views/code_card_qweb.xml',
        'views/res_partner_view.xml',
    ],
}