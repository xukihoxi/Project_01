# -*- coding: utf-8 -*-
{
    'name': "ResPartner Custom",

    'summary': """
        ResPartner Custom""",

    'description': """
        ResPartner Custom
    """,

    'author': "ERPViet",
    'website': "http://www.izisolution.vn",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': '',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'izi_brand', 'account'],

    # always loaded
    'data': [
        'security/res_partner_security.xml',
        'security/ir.model.access.csv',
        # 'views/source_res_partner_view.xml',
        'views/res_partner.xml',
        'data/sequence.xml',
        'views/partner_supplier_form.xml',
        'views/views.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        # 'demo/demo.xml',
    ],
}