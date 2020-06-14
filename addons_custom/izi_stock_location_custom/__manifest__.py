# -*- coding: utf-8 -*-
{
    'name': "Stock Location and Security",

    'summary': """
        Code location and menu Security""",

    'description': """
        Code location and menu Security
    """,

    'author': "ERPViet",
    'website': "http://www.izisolution.vn",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'Stock',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base','stock'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'views/stock_picking_type.xml',
        'views/stock_picking.xml',
        'views/stock_location.xml',
    ],
}