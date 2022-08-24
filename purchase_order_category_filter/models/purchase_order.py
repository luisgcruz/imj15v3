# -*- coding: utf-8 -*-
from odoo import fields, models, api, _


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    def obtener_ids_para_filtro(self):
        self._cr.execute("SELECT category_id FROM product_category_res_users_domain_rel WHERE user_id=%s" % self._uid)
        record = self._cr.fetchall()
        categs = []
        for tupla in record:
            categs.append(tupla[0])
        params = ','.join(map(str, categs))
        if not params:
            return []
        self._cr.execute("""SELECT distinct (pol.order_id)
            FROM purchase_order_line as pol
            JOIN product_product pp ON pp.id=pol.product_id
            JOIN product_template pt ON pt.id = pp.product_tmpl_id
            JOIN product_category pc ON pc.id=pt.categ_id
           WHERE pc.id IN (%s)"""%params)
        record = self._cr.fetchall()
        filtro = []
        for elem in record:
            filtro.append(elem[0])
        return filtro


class ProductCategory(models.Model):
    _inherit = 'product.category'

    usuarios_vision_ids = fields.Many2many(
        'res.users',
        'product_category_res_users_domain_rel',
        'category_id', 'user_id', string='Visible para')


class IrRule(models.Model):
    _inherit = "ir.rule"

    @api.model
    def _eval_context(self):
        context = super(IrRule, self)._eval_context()
        context.update({'ids_compras_imj': self.env['purchase.order'].obtener_ids_para_filtro()})
        return context
