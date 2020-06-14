# -*- coding: utf-8 -*-
{
    'name': "izi_pos_crm",

    'summary': """
        izi_pos_crm""",

    'description': """
        izi_pos_crm
    """,

    'author': "IZISolution",
    'website': "http://www.izisolution.vn",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'point_of_sale', 'izi_crm_lead'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views/root_view.xml',
        'views/reception_customer_view.xml',
        'views/reception_customer_history_view.xml',
        'views/crm_lead_views.xml'
    ],
    # only loaded in demonstration mode

}