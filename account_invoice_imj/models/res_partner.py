# -*- coding: utf-8 -*-
from odoo import fields, models, api,_

class ResPartner(models.Model):
    _inherit = 'res.partner'

    es_vendedor = fields.Boolean(string="¿Es vendedor?", default=False)