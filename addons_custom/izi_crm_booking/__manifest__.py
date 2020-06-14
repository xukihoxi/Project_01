# -*- coding: utf-8 -*-
{
    'name': "Booking/Meeting",

    'summary': """Quản lý lịch hẹn chăm sóc và lịch hẹn làm dịch vụ""",

    'description': """
        Quản lý lịch hẹn chăm sóc và lịch hẹn làm dịch vụ
    """,

    'author': "Izisolution",
    'website': "http://www.izisolution.vn",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/12.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Customer Relationship Management',
    'version': '1.0',

    # any module necessary for this one to work correctly
    'depends': ['base', 'crm', 'sale', 'izi_branch', 'web_gantt',
                'calendar', 'izi_message_dialog', 'izi_crm_lead', 'point_of_sale'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        # 'security/booking_security.xml',
        'data/sequence.xml',
        'views/service_booking.xml',
        'views/pos_use_service.xml',
        'views/crm_lead.xml',
        # 'views/crm_team_bed.xml',
        # 'views/hr_employee.xml',
        'views/product_template.xml',
        'views/product_product.xml',
        'views/pos_order.xml',
        'views/res_partner.xml',
        'wizards/list_booking_by_employee.xml',
        'wizards/confirm_dialog.xml',

    ],
    # only loaded in demonstration mode
    'demo': [],
}