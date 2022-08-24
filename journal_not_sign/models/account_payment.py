# -*- coding: utf-8 -*-

from odoo import fields, models, api, SUPERUSER_ID, _


class AccountPayment(models.Model):
    _inherit = 'account.payment'


    def l10n_mx_edi_is_required(self):
        result = super(AccountPayment, self).l10n_mx_edi_is_required()
        return result and not self.journal_id.not_invoice_sign