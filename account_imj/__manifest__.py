# -*- coding: utf-8 -*-

{
    'name' : 'Contabilidad IJM',
    'shortdesc': 'Contabilidad IJM',
    'version' : '1.1',
    'summary': 'Account modifications specifically for IMJ',
    'description': """
        All small modifications to the account module will be placed inside this module.
         """,
    'category': 'Account',
    'author': 'InuX',
    'website': 'https://www.odoo.com/',
    'depends' : ['account','purchase','budget_purchase_imj'],
    'data': ['views/account_view.xml',
             'data/retraducir_cron.xml',
            #'views/purchase_order_view.xml',
            ],
    'demo': [],
    'qweb': [],
    'installable': True,
    'auto_install': False,
    'license': 'LGPL-3',
}
