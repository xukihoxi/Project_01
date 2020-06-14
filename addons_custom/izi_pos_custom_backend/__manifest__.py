# -*- coding: utf-8 -*-
{
    'name': "Custom Pos Backend",

    'summary': """
        Custom Pos Backend""",

    'description': """
        Custom Pos Backend
    """,

    'author': "IZISolution",
    'website': "http://www.izisolution.vn",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    # 'depends': ['base', 'point_of_sale', 'izi_vip', 'izi_virtual_money', 'pos_payment_config', 'account'],
    'depends': ['base', 'point_of_sale', 'izi_virtual_money', 'pos_payment_config', 'account'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'security/security.xml',
        'views/menu_service.xml',
        'views/pos_order_custom.xml',
        'views/pos_sessions_custom.xml',
        'views/pos_config_custom_view.xml',
        # 'views/customer_pos_view.xml',
        'views/payment_methods.xml',
        'views/res_partner_debt.xml',
        'views/sell_virtual_money.xml',
        'views/pop_up_customer_signature_view.xml',
        'views/res_users_view.xml',
        'views/custome_invoice.xml',
        'views/res_partner_view.xml',
    ],
    "qweb": [
            'static/src/xml/order_line_detail.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}