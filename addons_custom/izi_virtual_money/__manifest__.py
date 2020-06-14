{
    'name':'Virtual money',
    'description': 'Virtual money management',
    'version':'1.0',
    'author':'IZISolution',

    'data': [
        'security/rules.xml',
        'security/ir.model.access.csv',
        'data/data.xml',
        'views/views.xml',
        'views/sell_virtual_money.xml',

    ],
    'website': '',
    'depends': ['base', 'product', 'point_of_sale', 'izi_vip'],
    "qweb": [
        'static/src/xml/templates.xml',
    ],
    'application': False,
}
