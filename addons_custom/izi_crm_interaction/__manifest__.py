# -*- coding: utf-8 -*-
{
    'name': "izi_crm_interaction",

    'summary': """
        Short (1 phrase/line) summary of the module's purpose, used as
        subtitle on modules listing or apps.openerp.com""",

    'description': """
        Long description of module's purpose
    """,

    'author': "IZISolution",
    'website': "http://www.izisolution.vn",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'crm', 'survey', 'izi_crm_booking'],

    # always loaded
    'data': [
        'data/partner_interaction_type_data.xml',

        # 'security/ir.model.access.csv',
        'views/partner_interaction_type_views.xml',
        'views/partner_interaction_views.xml',
        'views/res_partner_views.xml',
        'views/product_product_views.xml',
        'views/service_booking_views.xml',
        'views/izi_service_card_using_views.xml',
        'views/survey_user_input_views.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}