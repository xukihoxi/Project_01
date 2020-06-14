# -*- coding: utf-8 -*-
{
    'name': "Purchase Order Custom",

    'summary': """
            Purchase Order Custom
            """,

    'description': """
            Purchase Order Custom
            """,
    'author': "ERPViet",
    'website': "http://www.izisolution.vn",
    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/12.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'purchase',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'purchase'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'views/purchase_order_views.xml',
    ],
}