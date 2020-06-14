# -*- coding: utf-8 -*-
{
    'name': "Pos Digital Sign All",

    'summary': """
        Pos Digital Sign All""",

    'description': """
        Pos Digital Sign All
    """,

    'author': "ERPViet",
    'website': "http://www.izisolution.vn",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'izi_pos_custom_backend', 'izi_use_service_card', 'pos_destroy_service', 'izi_pos_debt_goods', 'izi_pos_exchange_service'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views/views.xml',
        'data/ir_sequence_data.xml',
        # 'views/templates.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}