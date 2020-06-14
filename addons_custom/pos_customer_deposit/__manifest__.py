# -*- coding: utf-8 -*-
{
    'name': "Pos Customer Deposit",

    'summary': """

    """,

    'description': """

    """,

    'author': "ERPViet",
    'website': "http://www.izisolution.vn",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'Point_of_sale',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base','izi_pos_custom_backend','pos_security','pos_revenue_allocation'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'security/security.xml',
        'data/ir_sequence_data.xml',
        'views/pos_customer_deposit_view.xml',
        'views/pos_customer_deposit_line_view.xml',
        'views/res_partner_debt.xml',
        'views/templates.xml',
        'views/invoice.xml',
    ],
}