# -*- coding: utf-8 -*-

from odoo import api, fields, models
from odoo.exceptions import UserError, ValidationError


class ResPartner(models.Model):
    _inherit = 'res.partner'

    vat = fields.Char(string='Tax ID', required=False, help="The Tax Identification Number. Complete it if the contact is subjected to government taxes. Used in some legal statements.")
    valid_rfc = fields.Boolean('Valida RFC', default=False)

    @api.constrains('vat','valid_rfc')
    def _check_vat_unique(self):
        if self.valid_rfc:
            old_vat=self.search([('vat', '=', self.vat),('id', '!=', self.id)])
            if old_vat:
                raise ValidationError('RFC debe ser Unico')
        

    # _sql_constraints = [
    #     ('vat_uniq', 'unique (vat)', 'El RFC debe ser Unico!')
    # ]