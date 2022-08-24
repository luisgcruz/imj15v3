# -*- coding: utf-8 -*-

from odoo import api, fields, models, _


class ProductUnspscCode(models.Model):
    _inherit = 'product.unspsc.code'

    aceptable = fields.Boolean(help='Si no es aceptable, rechazará el intento de crear la factura desde el portal.', default=False)