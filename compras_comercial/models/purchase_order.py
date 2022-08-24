# -*- coding: utf-8 -*-
from odoo import fields, models, api,_

class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    supplier_ref = fields.Char(string='Nombre Comercial', related='partner_id.ref', readonly=False, store=True)