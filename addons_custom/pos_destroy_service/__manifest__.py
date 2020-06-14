# -*- coding: utf-8 -*-
{
    'name': "Destroy Service",

    'summary': """
        Destroy Service""",

    'description': """
        Destroy Service
    """,

    'author': "ErpViet",
    'website': "http://www.izisolution.vn",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'Pos',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'point_of_sale','izi_use_service_card', 'web_digital_sign', 'mail'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'security/security.xml',
        'data/ir_sequence_data.xml',
        'views/popup_customer_destroy_service_view.xml',
        'views/stock_production_lot.xml',
        'views/destroy_service_view.xml',
        'views/res_partner_view.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}