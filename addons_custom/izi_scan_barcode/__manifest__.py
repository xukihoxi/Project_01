# -*- coding: utf-8 -*-
{
    'name': "izi_scan_barcode",

    'summary': """
        Short (1 phrase/line) summary of the module's purpose, used as
        subtitle on modules listing or apps.openerp.com""",

    'description': """
        Long description of module's purpose
    """,

    'author': "My Company",
    'website': "http://www.yourcompany.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base'],

    # always loaded
    'data': [
        'security/scan_barcode_security.xml',
        'views/scan_barcode_izi_service_card_using_line_views.xml',
        'views/scan_barcode_view.xml',
    ],
    'qweb': ['static/src/xml/scan_barcode.xml'],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}