# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError

class AccountMove(models.Model):
    _inherit = "account.move"


    l10n_mx_supplier_cfdi_uuid = fields.Char(string='Fiscal Folio Proveedor', copy=False, readonly=True,)
    estado_factura_portal = fields.Selection(string='Estado factura desde portal', default='pendiente', copy=False,
                                       selection=[('pendiente', 'Por Cargar'), ('revision', 'En Revision'),
                                                  ('aceptado', 'Aceptado'), ('rechazado', 'Rechazado')])
    purchase_from_portal_id = fields.Many2one('purchase.order', 'Creada de órden de portal', copy=False)


    def action_post(self):
        if self.move_type == 'in_invoice':
            if self.purchase_from_portal_id and self.purchase_from_portal_id.state not in ['purchase','done']:
                raise UserError('La factura no se puede aprobar porque su órden de compra no está en estado <confirmado>.')
            self.estado_factura_portal = 'aceptado'
        return super(AccountMove, self).action_post()

    def rechazar_factura_portal(self):
        self.estado_factura_portal = 'rechazado'
        self.button_cancel()
        if self.purchase_from_portal_id:
            self.purchase_from_portal_id.invoice_status = 'to invoice'

    def action_create_invoice_from_po(self, order_rec):
        """Create the invoice associated to the PO.
        """
        factura = self.env['account.move'].create({
            'partner_id': order_rec.partner_id.id,
            'purchase_id': order_rec.id,
            'move_type': 'in_invoice',
            'date': fields.Date.today(),
            'invoice_origin': order_rec.name,
        })
        factura.purchase_vendor_bill_id = order_rec.id
        po_lines = order_rec.order_line - factura.line_ids.mapped('purchase_line_id')
        new_lines = self.env['account.move.line']
        for line in po_lines.filtered(lambda l: not l.display_type):
            if line.product_id.purchase_method == 'purchase':
                qty = line.product_qty - line.qty_invoiced
            else:
                qty = line.qty_received - line.qty_invoiced
            fiscal_position = factura.fiscal_position_id
            accounts = line.product_id.product_tmpl_id.get_product_accounts(fiscal_pos=fiscal_position)
            new_line = new_lines.create({
                'name': '%s: %s' % (order_rec.name, line.name),
                'move_id': factura.id,
                'currency_id': factura.currency_id.id,
                'purchase_line_id': line.id,
                'date_maturity': factura.invoice_date_due,
                'product_uom_id': line.product_uom.id,
                'product_id': line.product_id.id,
                'price_unit': line.price_unit,
                'quantity': qty,
                'partner_id': factura.commercial_partner_id.id,
                'analytic_account_id': line.account_analytic_id.id,
                'analytic_tag_ids': [(6, 0, line.analytic_tag_ids.ids)],
                'tax_ids': [(6, 0, line.taxes_id.ids)],
                'display_type': line.display_type,
                'account_id': accounts['expense'].id,
            })
            new_line._onchange_price_subtotal()
        return factura

class AccountPaymentMixin(models.Model):

    _name = 'account.payment'
    _inherit = ['account.payment', 'portal.mixin']

    estado_rep_cfdi = fields.Selection(string='Estado del cfdi de pago', default='pendiente',
                                      selection=[('pendiente', 'Por Cargar'), ('cargado', 'Cargado'),
                                                 ('rechazado', 'Rechazado')], copy=False)

    def _compute_access_url(self):
        super(AccountPaymentMixin, self)._compute_access_url()
        for pago in self:
            pago.access_url = '/my/pago/%s' % (pago.id)

    def _get_report_base_filename(self):
        self.ensure_one()
        return 'Recibo de pago-%s' % (self.name)