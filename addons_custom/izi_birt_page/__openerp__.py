# -*- coding: utf-8 -*-
{
    'name': "Embedded Birt page",

    'summary': """Embedded birt report viewer to odoo with iframe""",

    'description': """
        Nothing to description
    """,

    'author': "Longdt",

    'category': 'Custom',
    'version': '0.1',
    'qweb': ['static/src/xml/*.xml'],
    # any module necessary for this one to work correctly
    'depends': ['point_of_sale'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'views/views.xml',
        # 'views/templates.xml',
    ],
}