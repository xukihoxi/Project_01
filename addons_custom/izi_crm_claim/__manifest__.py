# -*- coding: utf-8 -*-
{
    'name': "izi_crm_claim",

    'summary': """
        Short (1 phrase/line) summary of the module's purpose, used as
        subtitle on modules listing or apps.openerp.com""",

    'description': """
        Long description of module's purpose
    """,

    'author': "IZISOLUTION",
    'website': "http://www.izisolution.vn",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'res_partner_custom'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'views/root_views.xml',
        'views/crm_claim_type_views.xml',
        'views/crm_claim_views.xml',
        'views/crm_claim_report.xml',
    ],
    'qweb': ['static/src/xml/*.xml'],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}