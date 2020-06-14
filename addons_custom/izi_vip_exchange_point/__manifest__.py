# -*- coding: utf-8 -*-
{
    'name': "Exchange point",

    'summary': """
        Exchange point and point bonus
    """,

    'description': """
        Exchange point and point bonus
    """,

    'author': "ERPViet",
    'website': "http://www.izisolution.vn",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'crm',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'izi_pos_custom_backend','izi_vip_config'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'data/ir_sequence_data.xml',
        # 'views/pos_order_point_views.xml',
        'views/exchange_point_views.xml',
    ],
}
