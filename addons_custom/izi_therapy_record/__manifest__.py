# -*- coding: utf-8 -*-
{
    'name': "izi_therapy_record",

    'summary': """
        izi_therapy_record""",

    'description': """
        izi_therapy_record
    """,

    'author': "IZISolution",
    'website': "http://www.izisolution.vn",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'point_of_sale', 'izi_vip'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views/therapy_record_view.xml',
        'views/prescription_task_view.xml',

    ],
    # only loaded in demonstration mode

}