# -*- coding: utf-8 -*-
{
    'name': "Pos Money",

    'summary': """
        Pos Money""",

    'description': """
        Pos Money
    """,

    'author': "ERPViet",
    'website': "http://www.izisolution.vn",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'point_of_sale',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'point_of_sale', 'izi_branch', 'account'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'security/pos_money_security.xml',
        'data/ir_sequence_data.xml',
        'views/pos_money_view.xml',
        'views/pop_up_fee_bank_view.xml',
        'views/ir_sequence_data.xml',
        'views/pos_session_view.xml',
    ]
}