# -*- coding: utf-8 -*-
{
    'name': "Stock report",

    'summary': """
        Warehouse report
        """,

    'description': """
        IZISolution's new thinking development report
    """,

    'author': "IZISolution",
    'website': "http://www.izisolution.vn",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'stock',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base','stock','stock_account'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'data/stock_report_data.xml',
        'views/izi_inventory_report_views.xml',
        'views/izi_data_warehouse.xml',
        'views/izi_inventory_value_report_views.xml',
        'views/izi_in_out_inventory_report_views.xml',
        'views/izi_in_out_warehouse.xml',
    ],
}