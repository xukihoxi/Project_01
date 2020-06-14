# -*- coding: utf-8 -*-
{
    'name': "Exchange Service",

    'summary': """
        Exchange Service
    """,

    'description': """
        Exchange Service
    """,

    'author': "ERPViet",
    'website': "http://www.izisolution.vn",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'point_of_sale',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base','point_of_sale','izi_use_service_card'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'security/security.xml',
        'data/ir_sequence_data.xml',
        'views/exchange_service_view.xml',
        'views/stock_production_lot.xml',
        'views/popup_customer_rate_view.xml',
        'views/res_partner_view.xml',
    ],
}