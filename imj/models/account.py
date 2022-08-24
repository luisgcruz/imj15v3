# -*- coding: utf-8 -*-

from odoo import api, fields, models


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    # Columns Section
    compartido = fields.Boolean(
        string='Compartido')

    listado = fields.Selection(
        selection=[('local','Local'),
                    ('foraneo','Foraneo'),
                ],
        string="Listado",
    )
    state_id = fields.Many2one("res.country.state", string='Estado', ondelete='restrict', domain="[('country_id', '=?', country_id)]")
    country_id = fields.Many2one('res.country', string='Pais', ondelete='restrict')
    city_id = fields.Many2one('res.city', string='Ciudad',domain="[('state_id', '=?', state_id)]")

class AccountAnalyticAccount(models.Model):
    _inherit = 'account.analytic.account'

    # Columns Section
    compartido = fields.Boolean(
        string='Compartido')

    listado = fields.Selection(
        selection=[('local','Local'),
                    ('foraneo','Foraneo'),
                ],
        string="Listado",
    )





class CrossoveredBudgetLines(models.Model):
    _inherit = "crossovered.budget.lines"

    percentage = fields.Float(
        compute='_compute_percentage', string='Achievement',
        help="Comparison between practical and theoretical amount. This measure tells you if you are below or over budget.")
    account_id = fields.Many2one('account.account', compute='_compute_account', string="Cuenta", store=False)

    def _compute_percentage(self):
        for line in self:
            if line.amount_purchase != 0.0:
                line.percentage = float((line.amount_purchase or 0.0) / line.planned_amount)
            else:
                line.percentage = 0.00

    def _compute_account(self):
        for line in self:
            if line.general_budget_id:
                if line.general_budget_id.account_ids:
                    line.account_id=line.general_budget_id.account_ids[0].id
                else:
                    line.account_id=False
            else:
                line.account_id=False






