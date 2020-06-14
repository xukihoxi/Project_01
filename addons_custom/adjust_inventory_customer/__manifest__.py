# -*- coding: utf-8 -*-
{
    'name': "Adjust inventory customer",

    'summary': """
            Adjust inventory customer
    """,

    'description': """
            Adjust inventory customer
    """,

    'author': "",
    'website': "",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'stock',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base','mail','stock_inventory_customer','pos_security','izi_vip','pos_customer_deposit'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views/views.xml',
        'views/line_view.xml'
    ],
}