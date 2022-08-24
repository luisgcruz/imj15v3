# -*- coding: utf-8 -*-
from odoo import fields, models, api,_

class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    @api.depends('order_line')
    def _compute_analytic_lines(self):
        for record in self:
            if record.order_line:
                record.line_analitic_account = record.order_line[0].account_analytic_id.id
                break

    line_analitic_account = fields.Many2one(string='Cuenta Analitica', compute='_compute_analytic_lines', comodel_name='account.analytic.account' ,store=True)