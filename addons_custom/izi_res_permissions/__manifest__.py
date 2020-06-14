# -*- coding: utf-8 -*-
{
    'name': "izi_res_permissions",

    'summary': """
        Short (1 phrase/line) summary of the module's purpose, used as
        subtitle on modules listing or apps.openerp.com""",

    'description': """
        Long description of module's purpose
    """,

    'author': "IZISolution",
    'website': "http://www.izisolution.vn",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/12.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'point_of_sale', 'izi_use_service_card', 'pos_customer_deposit', 'izi_pos_custom_backend'],

    # always loaded
    'data': [
        'security/res_groups_branch.xml',
        'security/res_groups_uid_telesales.xml',
        'security/res_groups_general.xml',
        'security/ir.model.access.csv',
        'security/ir_rule_revenue_control.xml',
        'security/ir_rule_business_manager.xml',
        'security/ir_rule_revenue_accountant.xml',
        'security/ir_rule_cost_accountant.xml',
        'security/ir_rule_branch.xml',
        'views/crm_views.xml',
        'views/point_of_sale_views.xml',
        'views/stock_views.xml',
        'views/account_views.xml',
        'views/contacts_views.xml',
        'views/calendar_views.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}