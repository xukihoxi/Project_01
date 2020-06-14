# -*- coding: utf-8 -*-
{
    'name': "Guarantee service",

    'summary': """
            Guarantee service
    """,

    'description': """
            Guarantee service
    """,

    'author': "",
    'website': "",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'point_of_sale',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base','izi_pos_custom_backend'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'data/ir_sequence_data.xml',
        'views/views.xml',
        'views/guarantee.xml',
    ],
}