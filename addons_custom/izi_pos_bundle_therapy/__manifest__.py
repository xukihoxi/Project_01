# -*- coding: utf-8 -*-
{
    'name': "izi_pos_bundle_therapy",

    'summary': """
        izi_pos_bundle_therapy""",

    'description': """
        izi_pos_bundle_therapy
    """,

    'author': "IZISolution",
    'website': "http://www.izisolution.vn",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'izi_pos_custom_backend', 'izi_therapy_record'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views/body_area_view.xml',
        'views/bundle_therapy_view.xml',
        'views/bundle_therapy_barem_view.xml',
        'views/pos_order_custom.xml',
        'views/therapy_record_view.xml',

    ],
    # only loaded in demonstration mode

}