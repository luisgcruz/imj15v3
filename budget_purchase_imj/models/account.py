# -*- coding: utf-8 -*-

from odoo import api, fields, models


class CrossoveredBudge(models.Model):
    _inherit = "crossovered.budget"

    start_date = fields.Date('Inicio')
    end_date = fields.Date('Fin')
    margen_real = fields.Float(' % Margen Real', compute='_compute_margen')
    margen_planeed = fields.Float('% Margen Planeado', compute='_compute_margen')

    def _compute_margen(self):
        for budget in self:
            venta_planed=0
            compra_planed=0
            venta_real=0
            compra_real=0
            for line in budget.crossovered_budget_line:
                if line.account_id:
                    if float(line.account_id.code.split('.')[0]) > 400 and float(line.account_id.code.split('.')[0]) < 410:
                        venta_planed += line.planned_amount
                        venta_real += line.amount_purchase
                    if float(line.account_id.code.split('.')[0]) > 500 and float(line.account_id.code.split('.')[0]) < 510:
                        compra_planed += line.planned_amount
                        compra_real += line.amount_purchase
            if venta_planed != 0:
                budget.margen_planeed = ((venta_planed - compra_planed) / venta_planed ) * 100
            else:
                budget.margen_planeed=0
            if venta_real != 0:
                budget.margen_real = ((venta_real - compra_real) / venta_real) * 100
            else:
                budget.margen_real = 0

    @api.onchange('start_date','end_date')
    def _onchange_dates(self):
        for budget in self:
            if budget.start_date and budget.end_date:
                days=fields.Date.from_string(budget.end_date) - fields.Date.from_string(budget.start_date)
                for line in budget.crossovered_budget_line:
                    line.duration=days.days


class CrossoveredBudgetLines(models.Model):
    _inherit = "crossovered.budget.lines"

    amount_purchase = fields.Float(string='Importe Compras')
    qty = fields.Float(string='Cantidad')
    price = fields.Float(string='Precio')
    duration = fields.Integer(string='Duración', compute='_compute_duration_imj')
    planned_amount = fields.Monetary(
        'Cantidad Planeada', required=True,
        help="Cantidad planeada para ganar/gastar. Registra una cantidad positiva si es una ganancia o una negativa si es un gasto.")

    def _compute_duration_imj(self):
        for line in self:
            if line.crossovered_budget_id.start_date and line.crossovered_budget_id.end_date:
                days=fields.Date.from_string(line.crossovered_budget_id.end_date) - fields.Date.from_string(line.crossovered_budget_id.start_date)
                line.duration=days.days
            else:
                line.duration=0

    @api.onchange('qty','price','duration')
    def _onchange_planned(self):
        for line in self:
            if line.qty and line.price:
                line.planned_amount = line.qty * line.price
            else:
                line.planned_amount = 0

    def _compute_purchase(self):
        for line in self:
                line.amount_purchase = 0.00