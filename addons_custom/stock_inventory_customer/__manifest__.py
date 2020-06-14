# -*- coding: utf-8 -*-
{
    'name': "Update Inventory Customer",

    'summary': """
            Update Inventory Customer
    """,

    'description': """
            Update Inventory Customer
    """,

    'author': "ERPViet",
    'website': "http://www.izisolution.vn",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'stock',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base','mail','izi_pos_custom_backend','pos_security'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'data/ir_sequence_data.xml',
        'views/import_view.xml',
    ],
}