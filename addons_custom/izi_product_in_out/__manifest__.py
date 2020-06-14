# -*- coding: utf-8 -*-
{
    'name': "Xuất hàng hóa chi phí",

    'summary': """
       Chức năng phục vụ việc xuất hàng hóa vào chi phí như xuất hàng hành chính, VPP, CCDC ..""",

    'description': """
    Chức năng phục vụ việc xuất hàng hóa vào chi phí như xuất hàng hành chính, VPP, CCDC...
    """,

    'author': "IZISolution",
    'website': "http://www.izisolution.vn",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base','stock','account'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views/product_delivery.xml',
        'views/stock_move.xml',
        'views/stock_picking_reason.xml',
        'views/stock_scrap_inherit_view.xml',
        'views/res_partner_view.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}