# -*- coding: utf-8 -*-
{
    'name': "Report qweb",

    'summary': """
        Report""",

    'description': """
    """,

    'author': "ERPViet",
    'website': "http://www.izisolution.vn",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'Qweb',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'izi_stock_location_custom', 'izi_use_service_card','web'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'views/report_template.xml',
        'views/invoice.xml',
        'views/invoice_virual_money.xml',
        'views/request_material.xml',
        'views/internal_template.xml',
        'views/report_in_invoice_pament.xml',
        'views/stock_report_qweb_menu.xml',
        'views/stock_report_qweb_incoming.xml',
        'views/stock_report_qweb_outgoing.xml',
        'views/stock_report_qweb_internal.xml',
        'views/invoice_use_card.xml',
        'views/account_payment_bill.xml',
    ],
}
