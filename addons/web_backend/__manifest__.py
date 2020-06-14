# -*- coding: utf-8 -*-

{
    'name': 'Web Backend v1',
    'category': 'Hidden',
    'version': '1.0',
    'description':
        """
Odoo Web Client.
        """,
    'depends': ['web'],
    'auto_install': False,
    'data': [
        'views/webclient_templates.xml',
    ],
    'qweb': [
        "static/src/xml/*.xml",
    ],
}
