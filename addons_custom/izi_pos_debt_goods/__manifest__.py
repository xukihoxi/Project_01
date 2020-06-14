# -*- coding: utf-8 -*-
{
    'name': "POS Debt goods",

    'summary': """
        Bán nợ hàng trên Pos""",

    'description': """
        Bán nợ hàng trên Pos
    """,

    'author': "ERPViet",
    'website': "http://www.izisolution.vn",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'point_of_sale',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base','izi_pos_custom_backend','stock','product'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'data/ir_sequence_data.xml',
        # 'views/pos_debit_good_view.xml',
        'views/pos_config_custom_view.xml',
        'views/pop_up_customer_signature_view.xml',
    ],
}