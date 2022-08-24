from odoo import models, fields, api, _
from odoo.exceptions import UserError
from dateutil.relativedelta import relativedelta


# class WizCam(models.TransientModel):
#     _register = False


#     # Attention, we don't set a domain, because there is a journal_type key
#     # in the context of the action
    

#     def run(self):
#         context = dict(self._context or {})
#         active_model = context.get('active_model', False)
#         active_ids = context.get('active_ids', [])

#         records = self.env[active_model].browse(active_ids)

#         return self._run(records)

#     def _run(self, records):
#         for box in self:
#             for record in records:
#                 if not record.journal_id:
#                     raise UserError(_("Please check that the field 'Journal' is set on the Bank Statement"))
#                 if not record.journal_id.company_id.transfer_account_id:
#                     raise UserError(_("Please check that the field 'Transfer Account' is set on the company."))
#                 box._create_bank_statement_line(record)
#         return {}

#     def _create_bank_statement_line(self, record):
#         for box in self:
#             if record.state == 'confirm':
#                 raise UserError(_("You cannot put/take money in/out for a bank statement which is closed."))
#             values = box._calculate_values_for_statement_line(record)
#             record.write({'line_ids': [(0, False, values)]})


class WizardDuplicarPurchaseOrder(models.TransientModel):
    _name = 'wizard.duplicar.purchase.order'
    _description = 'Este modelo se usa para duplicar ordenes de compra de imj'

    name = fields.Many2one('purchase.order', 'Orden', required=True)
    num = fields.Integer('Meses', required=True)

    def run(self):
        for wiz in self:
            if not wiz.name.release_date:
                raise UserError("La orden no tiene fecha de liberación")
            news=[]
            rel_date = fields.Date.from_string(wiz.name.release_date)
            for i in range(wiz.num):
                # rel_date = fields.Date.from_string(wiz.release_date)
                new_date=rel_date + relativedelta(months=i+1)
                date_release=fields.Date.to_string(new_date)
                news.append(wiz.name.copy({'release_date':date_release, 'date_order':date_release}).id)
            tree_view_id = self.env.ref('purchase.purchase_order_tree').id
            form_view_id = self.env.ref('purchase.purchase_order_form').id
            domain = [('state', '=', 'draft'),('id', 'in', news)]
            action = {
                'type': 'ir.actions.act_window',
                'views': [(tree_view_id, 'tree'), (form_view_id, 'form')],
                'view_mode': 'tree,form',
                'name': _('Nuevas OC'),
                'res_model': 'purchase.order',
                'domain': domain,
            }
            return action

    # def _calculate_values_for_statement_line(self, record):
    #     if not record.journal_id.company_id.transfer_account_id:
    #         raise UserError(_("You have to define an 'Internal Transfer Account' in your cash register's journal."))
    #     amount = self.amount or 0.0
    #     return {
    #         'date': record.date,
    #         'statement_id': record.id,
    #         'journal_id': record.journal_id.id,
    #         'amount': amount,
    #         'account_id': record.journal_id.company_id.transfer_account_id.id,
    #         'name': self.name,
    #     }