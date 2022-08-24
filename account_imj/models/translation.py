# -*- coding: utf-8 -*-

from odoo import fields, models, tools


class IrTranslation(models.Model):
    _inherit = 'ir.translation'

    def _retraducir_terminos_purchase(self):
        terminos = self.search([('value','ilike','cotizaci'), ('module','=','purchase'), ('lang','=','es_MX')])
        cont = 0
        for term in terminos:
            term.value = term.value.replace('cotización', 'presupuesto').replace('cotizaciones', 'presupuestos')
            cont += 1
        print ('términos traducidos: ',cont)
        return True