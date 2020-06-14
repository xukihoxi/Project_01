# -*- coding: utf-8 -*-
{
    'name': "Work Service Allocation",

    'summary': """
        Work Service Allocation""",

    'description': """
        Work Service Allocation
    """,

    'author': "ERPVIET",
    'website': "http://www.izisolution.vn",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base','mail', 'izi_use_service_card','izi_pos_custom_backend'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'data/ir_sequence_data.xml',
        'views/service_card_using_view.xml',
        'views/pos_work_service_allocation_view.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}