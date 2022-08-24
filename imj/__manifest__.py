# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
{
    'name' : 'IMJ',
    'version' : '1.2',
    'summary': 'Init',
    'sequence': 1,
    'description': """
            Init""",
    'category': 'Base',
    'website': 'https://www.odoo.com/',
    'depends' : ['account','account_budget','purchase','sale','base_address_city'],
    'data': ['views/account_view.xml',
            'views/res_partner.xml',
            'views/purchase_view.xml',
            'views/sale_view.xml',
            ],
    'demo': [],
    'qweb': [],
    'installable': True,
    'auto_install': False,
    'license': 'LGPL-3',
}
