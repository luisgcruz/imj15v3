# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

from odoo import models, fields, exceptions, api, _
from odoo.exceptions import Warning


class ProductoSatAceptable(models.TransientModel):
    _name = "product.sat.aceptable"
    _description = "Productos aceptables en el portal"

    def _get_default_code(self):
        product_sat_obj = self.env['product.unspsc.code']
        ya_aceptados = product_sat_obj.search([('aceptable','=',True)])
        return ya_aceptados.ids

    name = fields.Char('Nombre')
    sat_code_aceptado_ids = fields.Many2many('product.unspsc.code', 'product_dynamic_fields_aceptado_rel', 'wiz_id', 'satcode_id', default=_get_default_code)

    def aceptar_estos_productos(self):
        product_sat_obj = self.env['product.unspsc.code']
        if len(self.sat_code_aceptado_ids) < 1:
            raise Warning(_('Necesitas seleccionar al menos un codigo del SAT para aceptar'))
        todos_codes = product_sat_obj.search([])
        todos_codes.sudo().write({'aceptable': False})
        for codigo in self.sat_code_aceptado_ids:
            codigo.sudo().write({'aceptable': True})
        return True