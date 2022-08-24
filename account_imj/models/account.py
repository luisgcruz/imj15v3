from odoo import api, fields, models


class AccountJournal(models.Model):
    _inherit = 'account.journal'

    no_publicable = fields.Boolean(string="Sin Publicar")


class AccountMove(models.Model):
    _inherit = 'account.move'

    no_publicable = fields.Boolean(string="Sin Publicar", related='journal_id.no_publicable')