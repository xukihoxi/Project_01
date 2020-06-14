# -*- coding: utf-8 -*-
{
    'name': "Payment Multi Currency",

    'summary': """
        Payment Multi Currency""",

    'description': """
        Payment Multi Currency
    """,

    'author': "IZISolution",
    'website': "http://www.izisolution.vn",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'Point Of Sale',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'point_of_sale', 'izi_pos_custom_backend', 'izi_use_service_card','account'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'views/pos_config_view.xml',
        'views/pos_payment_view.xml',
        'views/pos_order_view.xml',
        'views/res_currency_rate_view.xml',
        'views/invoice_make_payment_view.xml',
        'views/pos_payment_use_service_view.xml',
        'views/use_service_card_view.xml',
        'views/pos_session_view.xml',
        'views/account_journal_view.xml',
        'views/account_bank_statemant_view.xml',
        'views/pop_up_message_payment_servicce_view.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}