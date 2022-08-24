# -*- coding: utf-8 -*-
from odoo import fields, models, api,_
from dateutil.relativedelta import relativedelta
from odoo import SUPERUSER_ID

class ResPartner(models.Model):
    _inherit = 'res.partner'

    opinion_sat = fields.Binary(string='Opinion del SAT', copy=False)
    valid_until = fields.Date(string='Valido hasta', copy=False)
    estado_opinion = fields.Selection(string='Estado de la opinion', default='invalida', copy=False,
                                      selection=[('valida', 'Válida'), ('invalida', 'No válida'), ('revision', 'En revisión')])
    opinion_msg_stat = fields.Char(string='Detalle del estado', copy=False)
    exigir_complemento = fields.Boolean(string='Exigir carga de complemento', default=False, copy=False)

    @api.onchange('estado_opinion')
    def _onchange_estado_opinion(self):
        if self.estado_opinion and self.estado_opinion == 'valida':
            self.valid_until = fields.Date.today() + relativedelta(days=90)
            self.opinion_msg_stat = 'Documentación validada con éxito.'

    @api.model
    def _cron_opinion_sat_expira(self):
        su_id = self.env['res.partner'].browse(SUPERUSER_ID)
        for partner in self.search([]):
            if partner.estado_opinion == 'valida':
                expira = partner.valid_until
                hoy = fields.Date.today()
                faltan = (expira - hoy).days
                if faltan in (15, 10, 5): #podria hacerse configurable
                    template_id = self.env['ir.model.data'].get_object_reference('portal_imjm', 'email_template_edi_opinion_sat')[1]
                    template_browse = self.env['mail.template'].browse(template_id)
                    if template_browse:
                        values = template_browse.generate_email(partner.id,
                                                                ['subject', 'body_html', 'email_from',
                                                                 'email_to', 'partner_to', 'email_cc',
                                                                 'reply_to', 'scheduled_date', 'attachment_ids'])
                        values['email_from'] = su_id.email
                        values['email_to'] = partner.email
                        values['res_id'] = False
                        values['author_id'] = self.env['res.users'].browse(self.env['res.users']._context['uid']).partner_id.id
                        if not values['email_to'] and not values['email_from']:
                            pass
                        msg_id = self.env['mail.mail'].create({
                            'email_to': values['email_to'],
                            'auto_delete': True,
                            'email_from': values['email_from'],
                            'subject': values['subject'] + ' en %s días.'%faltan,
                            'body_html': values['body_html'],
                            'author_id': values['author_id']})
                        mail_mail_obj = self.env['mail.mail']
                        if msg_id:
                            mail_mail_obj.sudo().send(msg_id)
                if faltan < 1:
                    partner.estado_opinion = 'invalida'
                    partner.opinion_msg_stat = 'Expirada: han pasado 90 días desde la última renovación.'
        return True