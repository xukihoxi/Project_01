# -*- coding: utf-8 -*-
{
    'name': "Revenue Allocation",

    'summary': """
            Revenue Allocation
    """,

    'description': """
            Revenue Allocation
    """,

    'author': "ERPViet",
    'website': "http://www.izisolution.vn",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'point_of_sale',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base','izi_pos_custom_backend','mail', 'hr','izi_use_service_card','cash_management'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'data/ir_sequence_data.xml',
        'views/pos_revenue_allocation_view.xml',
        'views/pos_order.xml',
        'views/hr_employee_view.xml',
        'views/use_service.xml',
        'views/cash_management_view.xml',
    ],
}