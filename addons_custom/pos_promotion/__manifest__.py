{
    'name':'IZI Promotions program',
    'description': '',
    'version':'1.0',
    'author':'IZISOLUTION',

    'data': [
        'security/rules.xml',
        'security/ir.model.access.csv',
        'data/data.xml',
        'views/views.xml',
    ],
    'website': '',
    'depends': ['izi_pos_custom_backend', 'mail'],
    "qweb": [
        'static/src/xml/templates.xml',
    ],
    'application': False,
}
