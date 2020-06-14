# -*- coding: utf-8 -*-

{
    'name': 'Web Gantt',
    'category': 'Hidden',
    'description': """
OpenERP Web Gantt chart view.

""",
    'version': '2.0',
    'depends': ['web'],
    'data' : [
        'views/web_gantt_templates.xml',
    ],
    'qweb': [
        'static/src/xml/*.xml',
    ],
}
