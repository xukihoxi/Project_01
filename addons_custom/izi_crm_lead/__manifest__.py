# -*- coding: utf-8 -*-
{
    'name': "CRM Lead",

    'summary': """
        CRM Lead
    """,

    'description': """
        CRM Lead
    """,

    'author': "ERPViet",
    'website': "http://www.izisolution.vn",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'crm',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'crm', 'sale_crm','izi_use_service_card','sales_team', 'pos_customer_deposit'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views/pos_order_views.xml',
        'data/ir_sequence_data.xml',
        'views/crm_lead_views.xml',
        'views/crm_team_views.xml',

    ],
}
