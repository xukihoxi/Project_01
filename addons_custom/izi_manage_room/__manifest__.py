# -*- coding: utf-8 -*-
{
    'name': "Manage Room",

    'summary': """
        Manage Room""",

    'description': """
        Manage room
    """,

    'author': "IZISolution",
    'website': "http://www.izisolution.vn",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'point_of_sale', 'izi_use_service_card', 'izi_pos_custom_backend'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'security/room_security_view.xml',
        'views/room_view.xml',
        'views/bed_view.xml',
        'views/inherit_use_service_view.xml',
        'views/use_service_line_view_kanban.xml',
        'views/use_service_line_view.xml',
        'views/view_drashboard.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}