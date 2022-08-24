# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
{
    'name' : 'Budget Purchase IMJ',
    'version' : '1.2',
    'summary': 'Visto bueno a compras de IMJ',
    'sequence': 1,
    'description': """
            Module add validation of budget in purchase""",
    'category': 'Account',
    'website': 'https://www.odoo.com/',
    'depends' : ['account','account_budget','purchase'],
    'data': ['security/imj_security.xml',
        'security/ir.model.access.csv',
        'views/account_view.xml',
        'views/purchase_view.xml',
        'wizard/wizard_duplicar_purchase_order_view.xml',
        ],
    'demo': [],
    'qweb': [],
    'installable': True,
    'auto_install': False,
    'license': 'LGPL-3',
}
