{
    'name':'VIP customer management',
    'description': '',
    'version':'1.0',
    'author':'IZISolution',

    'data': [
        'security/rules.xml',
        'security/ir.model.access.csv',
        'data/data.xml',
        # 'views/vip.xml',
        # 'views/wizards.xml',
        # 'views/settings.xml',
    ],
    'website': '',
    'depends': ['crm', 'point_of_sale', 'pos_security', 'res_partner_custom'],
    "qweb": [
        'static/src/xml/templates.xml',
    ],
    'application': False,
}
