# -*- coding: utf-8 -*-

{
    'name' : 'Facturación IJM',
    'shortdesc': 'Facturación IJM',
    'version' : '1.2',
    'summary': 'Account modifications specifically for invoicing of IMJ',
    'description': """
        All small modifications to the account module will be placed inside this module.
         """,
    'category': 'Account',
    'author': 'InuX',
    'website': 'https://www.odoo.com/',
    'depends' : ['account','l10n_mx_edi'],
    'data': ['views/account_view.xml',
            'views/res_partner_view.xml',
            ],
    'demo': [],
    'qweb': [],
    'installable': True,
    'auto_install': False,
    'license': 'LGPL-3',
}
