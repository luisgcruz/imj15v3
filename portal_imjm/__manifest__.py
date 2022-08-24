# -*- coding: utf-8 -*-
{
    'name': "Portal customization for IMJM",
    'summary': """
        This module makes some arrangements to portal views for IMJM
        """,
    'author': "InuX",
    'website': "https://github.com/fmanime",
    'category': 'portal',
    'version': '2.0',
    'depends': ['purchase','portal','l10n_mx_edi'],
    'data': [
        'security/product_security_group.xml',
        'security/ir.model.access.csv',
        'edi/checar_opinion_sat_action_data.xml',
        'views/templates.xml',
        'views/res_partner_view.xml',
        'views/checar_opinion_sat_cron.xml',
        'views/account_view.xml',
        'wizard/product_view.xml',
    ],
    'license': 'LGPL-3',
}
