{
    'name':'PoS Config',
    'description': 'PoS Config',
    'version':'1.0',
    'author':'IZISolution',

    'data': [
        'security/rules.xml',
        'security/ir.model.access.csv',
        'data/data.xml',
        'views/pos_config.xml',
    ],
    'website': '',
    'depends': ['point_of_sale', 'account'],
    "qweb": [
        'static/src/xml/templates.xml',
    ],
    'application': False,
}
