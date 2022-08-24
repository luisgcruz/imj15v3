# -*- coding: utf-8 -*-

from odoo import api, fields, models

class PurchaseOrderLine(models.Model):
    _inherit = "purchase.order.line"

    mes_campana = fields.Date(string='Mes Campaña')


class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    def copy(self, default=None):
        self.ensure_one()
        order_rec = super(PurchaseOrder, self).copy(default=default)
        for linea in order_rec.order_line:
            linea.mes_campana = linea.date_planned
        return order_rec