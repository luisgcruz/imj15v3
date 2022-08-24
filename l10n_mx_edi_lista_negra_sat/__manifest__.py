# -*- coding: utf-8 -*-

{
    'name': 'Lista Negra del SAT mx',
    'version': '14.0',
    'depends': ['purchase', 'contacts'],
    'author': 'InuX',
    'category': 'fiscal',
    'website': 'www.google.com',
    'summary': 'Este módulo crea un nuevo modelo para revisar si los contactos se encuentran en las listas negras del SAT',
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'data/lista_negra_default.xml',
        'views/actualizar_lista_negra_cron.xml',
        'views/res_partner_view.xml',
        'views/res_partner_lista_negra_views.xml',
    ],
    'license': 'LGPL-3',
}