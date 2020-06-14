# -*- coding: utf-8 -*-
{
    'name': "Cash Management",
    'summary': """Cash Management""",
    'description': """
        ash Management
    """,
    'author': "",
    'website': "",
    'category': 'Accounting & Finance',
    'version': '0.1',
    'depends': ['base', 'account', 'mail', 'hr_expense', 'izi_branch'],
    'data': [
        'security/ir.model.access.csv',
        'security/security_view.xml',
        'wizard/refuse_reason_views.xml',
        'views/payment_card_view.xml',
        'views/report_payment_bills.xml',
        # 'views/report_hr_expense.xml',
        'views/account_view.xml',
    ],
    'application': False
}
