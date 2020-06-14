# -*- coding: utf-8 -*-
{
    'name': "Stock Picking",

    'summary': """
        Stock picking custom
    """,

    'description': """
        Stock picking custom
    """,

    'author': "ERPViet",
    'website': "http://www.izisolution.vn",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'stock',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base','stock'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'views/stock_picking.xml',
        'views/stock_change_product_qty_custom.xml',
        'views/stock_picking_type_custom.xml'
    ],
}