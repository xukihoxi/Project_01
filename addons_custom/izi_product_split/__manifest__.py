# -*- coding: utf-8 -*-
{
    'name': "Split product",

    'summary': """
        Split multi product""",

    'description': """
        Split multi product
    """,

    'author': "ERPViet",
    'website': "http://www.izisolution.vn",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'product',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base','stock'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'data/ir_sequence_data.xml',
        'views/product_split_view.xml',
        'views/product_split_detail_view.xml',
        'views/stock_warehouse.xml'
    ],
}