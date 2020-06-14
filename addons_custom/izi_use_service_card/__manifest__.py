# -*- coding: utf-8 -*-
{
    'name': "Use Service Card",

    'summary': """
        Use Service Card""",

    'description': """
        Use Service Card
    """,

    'author': "IZISolution",
    'website': "http://www.izisolution.vn",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'hr', 'mail','product', 'izi_product_release', 'pos_security', 'web_digital_sign', 'guarantee_service','point_of_sale'],

    # always loaded
    'data': [
        'views/service_bom_view.xml',
        'views/product_view.xml',
        'security/ir.model.access.csv',
        'security/security.xml',
        'data/ir_sequence_data.xml',
        'data/ir_sequence_resquest_materail.xml',
        'views/pop_up_refund_view.xml',
        'views/pop_up_payment_view.xml',
        'views/use_service_card_view.xml',
        'views/pos_use_material_view.xml',
        'views/popup_customer_rate_view.xml',
        'views/pos_use_material_cosmetic_surgery_view.xml',
        'views/request_material_view.xml',
        'views/pop_up_change_service_view.xml',
        'views/tmp_pos_use_material.xml',
        'views/res_partner_view.xml',
        'qweb/qweb_work_service.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}