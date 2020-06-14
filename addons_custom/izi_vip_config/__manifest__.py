# -*- coding: utf-8 -*-
{
    'name': "Vip config",

    'summary': """
        Vip config
    """,

    'description': """
        Vip config
    """,

    'author': "ERPViet",
    'website': "http://www.izisolution.vn",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'crm',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base','izi_vip'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        # 'views/accumulation_views.xml',
        # 'views/eviction_views.xml',
        'views/templates.xml',
    ],
}