# -*- coding: utf-8 -*-
{
    'name': "Product Custom",

    'summary': """
        Product Custom""",

    'description': """
        Product Custom
    """,

    'author': "IZISolution",
    'website': "http://www.izisolution.vn",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'Product',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base','izi_product_release','pos_security'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views/product_category_custom_view.xml',
        'views/product_service_view.xml',
        'views/product_template_custom_view.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}