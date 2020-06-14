# -*- coding: utf-8 -*-
{
    'name': "Stock request",

    'summary': """
        Requirements and coordination of goods""",

    'description': """
    """,
    #tiendz
    'author': "ERPViet",
    'website': "http://www.izisolution.vn",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'Stock',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'stock','izi_stock_transfer'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'data/ir_sequence_data.xml',
        'views/stock_request_go.xml',
        'views/stock_request_come.xml',
        'views/stock_request_coordinator.xml',
    ],
}
