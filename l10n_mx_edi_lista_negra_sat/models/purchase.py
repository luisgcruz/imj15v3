# -*- coding: utf-8 -*-
from odoo import fields, models
from odoo.exceptions import ValidationError


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'


    def button_confirm(self):
        if self.partner_id.estado_listado_sat in ['presunto', 'definitivo']:
            raise ValidationError('El proveedor se encuentra en la lista negra del SAT. La órden no fue confirmada')
        if self.partner_id.estado_listado_sat == 'novalidado':
            raise ValidationError('Por favor, primero actualice la lista negra del SAT para verificar el estado de este proveedor')
        return super(PurchaseOrder, self).button_confirm()

    def action_create_invoice(self):
        if self.partner_id.estado_listado_sat in ['presunto', 'definitivo']:
            raise ValidationError('El proveedor se encuentra en la lista negra del SAT. La factura no fue creada')
        if self.partner_id.estado_listado_sat == 'novalidado':
            raise ValidationError('Por favor, primero actualice la lista negra del SAT para verificar el estado de este proveedor')
        return super(PurchaseOrder, self).action_create_invoice()