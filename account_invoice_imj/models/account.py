# -*- coding: utf-8 -*-

from odoo import api, fields, models


class AccountMove(models.Model):
    _inherit = 'account.move'

    l10n_mx_edi_payment_policy = fields.Selection(selection=[('PPD', 'PPD'), ('PUE', 'PUE')], string='Método de Pago',
                                          default='PPD', store=True, required=False)
    l10n_mx_edi_cfdi_uuid = fields.Char(string='Fiscal Folio', copy=False, readonly=False,
                                        help='Folio in electronic invoice, is returned by SAT when send to stamp.',
                                        compute=False)

    def _l10n_mx_edi_get_payment_policy(self):
        self.ensure_one()
        # Se sobreescribe funcion original que calculaba, ahora es totalemente seleccionable
        if self.move_type == 'out_refund':
            self.l10n_mx_edi_payment_policy = 'PUE'
            return 'PUE'
        else:
            return self.l10n_mx_edi_payment_policy

class AccountPayment(models.Model):
    _inherit = 'account.payment'

    notas = fields.Char(string="Notas")
    #aux_mx_edi_cfdi_uuid = fields.Char(string='Fiscal Folio', copy=False)
    #l10n_mx_edi_cfdi_uuid = fields.Char(string='Fiscal Folio', copy=False, compute='_compute_cfdi_uuid')

    #@api.depends('aux_mx_edi_cfdi_uuid')
    #def _compute_cfdi_uuid(self):
    #    '''Fill the invoice fields from the cfdi values.
    #    '''
    #    for move in self:
    #        if move.payment_type == 'outbound':
    #            move.l10n_mx_edi_cfdi_uuid = move.aux_mx_edi_cfdi_uuid
    #        else:#manda error por falta del método aqui mismo
    #            cfdi_infos = move._l10n_mx_edi_decode_cfdi()
    #
    #            move.l10n_mx_edi_cfdi_uuid = cfdi_infos.get('uuid')
    #            move.l10n_mx_edi_cfdi_supplier_rfc = cfdi_infos.get('supplier_rfc')
    #            move.l10n_mx_edi_cfdi_customer_rfc = cfdi_infos.get('customer_rfc')
    #            move.l10n_mx_edi_cfdi_amount = cfdi_infos.get('amount_total')