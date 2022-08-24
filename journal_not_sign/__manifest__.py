# -*- coding: utf-8 -*-

{
    "name": "Journal Not Sign",
    "version": "1.0",
    'author': "Quemari Developers",
    'website': "http://www.quemari.com",
    'category': '',
    "description": """
           
    """,
    "depends": [
        "account",
        "l10n_mx_edi",
    ],
    "data": [
        "views/account_journal_view.xml",
        "views/account_move_view.xml",
        # 'security/ir.model.access.csv',
        
    ],
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}
