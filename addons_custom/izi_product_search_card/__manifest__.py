# -*- coding: utf-8 -*-
{
    'name': "Search card ",

    'summary': """
        Search card
    """,

    'description': """
        Search card from serial, code customer or phone
    """,

    'author': "ERPViet",
    'website': "http://www.izisolution.vn",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'Product',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base','izi_pos_custom_backend','izi_use_service_card','izi_pos_exchange_service','izi_vip_exchange_point', 'pos_customer_deposit'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'views/izi_product_search_card.xml',
        'views/report_history_use_service.xml',
        'views/templates.xml',
        'views/res_partner.xml',
    ],
}