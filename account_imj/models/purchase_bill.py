# -*- coding: utf-8 -*-

from odoo import fields, models, tools
from odoo.tools import formatLang


class PurchaseBillUnion(models.Model):
    _inherit = 'purchase.bill.union'

    def name_get(self):
        #NOTE: base function is overriden by this one. Not using result = super(PurchaseBillUnion, self).name_get()
        result = []
        self.init()
        for doc in self:
            name = doc.name or ''
            if doc.reference:
                name += ' - ' + doc.reference
            amount = doc.amount
            #if doc.purchase_order_id and doc.purchase_order_id.invoice_status == 'no':
            #    amount = 0.0
            name += ': ' + formatLang(self.env, amount, monetary=True, currency_obj=doc.currency_id)
            #next line filters as requested:
            if doc.purchase_order_id and doc.purchase_order_id.invoice_status in ['no', 'to invoice'] and doc.purchase_order_id.approval:
                result.append((doc.id, name))
        return result