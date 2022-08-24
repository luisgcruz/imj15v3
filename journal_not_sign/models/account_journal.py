# -*- coding: utf-8 -*-

from odoo import fields, models, api, SUPERUSER_ID, _


class AccountJournal(models.Model):
    _inherit = 'account.journal'


    not_invoice_sign = fields.Boolean(string="Sin Timbrar")