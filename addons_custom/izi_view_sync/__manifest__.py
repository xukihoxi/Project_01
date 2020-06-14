# -*- coding: utf-8 -*-
{
    'name': "View Synchronize",

    'summary': """
        Using pos.longpolling for sync process
        """,

    'description': """
        Hỗ trợ đồng bộ view: kanban, tree, form
        Khi gửi request dồng bộ: env['bus.bus'].sendone(channel, message)
        hoặc: env['bus.bus'].sendmany([[channel,message],[channel,message2],...])
        Với: channel: dbname+'izi.view_synchronize'
        message: {"model": model, type: tree}
        Điều kiện thực hiện đồng bộ lại view:
         - form view: model, đúng bản ghi (id)
         - list, kanban view: model, type (list,kanban)
    """,

    'author': "Longdt",
    'website': "http://www.IZISolution.com",

    'category': 'LDT',
    'version': '0.1',

    'depends': ['bus','izi_use_service_card', 'crm', 'izi_pos_exchange_service', 'pos_destroy_service'],

    # always loaded
    'data': [
        'views/templates.xml',
    ],
    # 'qweb': ['static/src/xml/*.xml'],
}
