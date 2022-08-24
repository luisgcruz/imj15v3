# -*- coding: utf-8 -*-

from odoo import api, fields, models
from odoo.exceptions import AccessError, UserError, ValidationError
from datetime import datetime
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT


class ProductCategory(models.Model):
    _inherit = "product.category"

    cost_edit = fields.Boolean('Modificar Costo', copy=False)
    limit_purchase = fields.Float('Limite Compras', copy=False)
    users_aprov_ids= fields.Many2many('res.users', 'categ_res_aut_rel', 'category_id', 'user_id', string='Usuarios Autoriza')
    users_limit_ids= fields.Many2many('res.users', 'categ_res_rel', 'cat_id', 'uid', string='Usuarios Admin')

    def write(self, values):
        res = super(ProductCategory, self).write(values)
        if 'cost_edit' in values:
            templates=self.env['product.template']
            ids_tmp=templates.search([('categ_id','=',self.id)])
            ids_tmp.write({'cost_edit':values.get('cost_edit')})
        return res


class ProductTemplate(models.Model):
    _inherit = "product.template"

    cost_edit = fields.Boolean('Modificar Costo', copy=False)


class PurchaseOrderLine(models.Model):
    _inherit = "purchase.order.line"

    cost_edit = fields.Boolean(related='product_id.cost_edit', string='Modificar Costo', copy=False)

    @api.onchange('product_id')
    def onchange_product_id(self):
        if not self.product_id:
            return

        # Reset date, price and quantity since _onchange_quantity will provide default values
        self.date_planned = datetime.today().strftime(DEFAULT_SERVER_DATETIME_FORMAT)
        self.price_unit = self.product_qty = 0.0
        self.cost_edit=self.product_id.cost_edit
        self._product_id_change()
        self._suggest_quantity()
        self._onchange_quantity()


class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    approval = fields.Boolean('Visto bueno', copy=False)
    release = fields.Boolean('Liberada', compute='_compute_release',store=False)
    release_date = fields.Date('Fecha Liberacion', copy=False)
    gpo = fields.Integer('Grupo', copy=False)
    
    @api.depends('release_date')
    def _compute_release(self):
        for order in self:
            order.release=True
            # users= self.env.ref("budget_purchase_imj.group_purchase_release" ).users
            # if self._uid in users.ids:
            #     order.release=True
            # else:
            #     order.release=False

    def write(self, values):
        res = super(PurchaseOrder, self).write(values)
        if 'approval' in values:
            if values['approval']:
                self.message_post(
                    body=('Visto Bueno aceptado'))
            else:
                self.message_post(
                    body=('Se elimino el Visto Bueno'))
        if self.approval == True:# and self.state == 'purchase':
            campos_permitidos = ['state', 'message_main_attachment_id', 'access_token', 'invoice_from_portal', 'invoice_status']
            for campo in campos_permitidos:
                if campo in values:
                    return res
            categ = self.order_line[0].product_id.categ_id
            if categ and self._uid not in categ.users_aprov_ids.ids and self._uid not in categ.users_limit_ids.ids:
                raise UserError(('No tienes permiso para modificar una orden que ya tiene visto bueno. Modificación: %s -'%str(values)))

    @api.onchange('approval')
    def onchange_approval(self):
        for order in self:
            categ=False
            if order.ids:
                if not order.release_date:
                    raise UserError(('No tienes fecha de liberación, no puedes dar el VoBo'))
                if order.release_date > fields.Date.today():
                    raise UserError(('La fecha de liberación, debe ser menor o igual a hoy'))
                for line in order.order_line:
                    if categ and line.product_id.categ_id.id != categ.id:
                        raise UserError(('Diferentes categorias de productos en las lineas'))
                    else:
                        categ=line.product_id.categ_id
                if categ and self._uid not in categ.users_aprov_ids.ids and self._uid not in categ.users_limit_ids.ids:
                    raise UserError(('Usuario sin perimosos para dar el visto bueno'))
                if categ and self.amount_total > categ.limit_purchase and self._uid not in categ.users_limit_ids.ids:
                    raise UserError(('Usuario sin perimosos para dar el visto bueno con monto superior ($ %.0f) de la categoria'%categ.limit_purchase))
            

    def button_confirm(self):
        budget = self.env['crossovered.budget']
        for order in self:
            if not order.approval:
                raise UserError(('No puedes confirmar una OC sin el Visto Bueno:'))
            positivo=False
            id_budget=budget.search([('date_from', '<=', fields.Date.context_today(self)),('date_to', '>=', fields.Date.context_today(self)),('state','=','validate')])
            if id_budget:
                for pline in order.order_line:
                    for p in id_budget:
                        for line in p.crossovered_budget_line:
                            prod_account_id=pline.product_id.product_tmpl_id.get_product_accounts(fiscal_pos=order.fiscal_position_id)['expense']
                            if (line.analytic_account_id.id==pline.account_analytic_id.id) and (line.account_id.id==prod_account_id.id):
                                positivo=True
                                break
                if not positivo:
                    raise UserError(('No existe linea de presupuesto activo para las lineas de presupuesto:'))


                for pline in order.order_line:
                    for p in id_budget:
                        for line in p.crossovered_budget_line:
                            if line.planned_amount > 0.0:
                                amount_purchase=(line.planned_amount - line.amount_purchase)
                                prod_account_id=pline.product_id.product_tmpl_id.get_product_accounts(fiscal_pos=order.fiscal_position_id)['expense']
                                if (line.analytic_account_id.id==pline.account_analytic_id.id) and (line.account_id.id==prod_account_id.id):
                                    if pline.price_subtotal > amount_purchase:
                                        raise UserError(('El monto del producto:  "%s" y la Cuenta: "%s" Sobrepasan el presupuesto: "%s" ') % (pline.product_id.name_get()[0][1],line.account_id.name,p.name))
                                    else:
                                        line.write({'amount_purchase':line.amount_purchase + pline.price_subtotal})
            else:
                raise UserError(('No hay presupuesto activo para la fecha:'))
        super(PurchaseOrder, self).button_confirm() 
        return True
    
    def button_cancel(self):
        budget = self.env['crossovered.budget']
        for order in self:
            if order.state=='purchase':
                if order.approval == True:
                    categ = order.order_line[0].product_id.categ_id
                    if categ and self._uid not in categ.users_aprov_ids.ids and self._uid not in categ.users_limit_ids.ids:
                        raise UserError(('No tienes permiso para cancelar una orden que ya tiene visto bueno'))
                id_budget=budget.search([('date_from', '<=', fields.Date.context_today(self)),('date_to', '>=', fields.Date.context_today(self)),('state','=','validate')])
                if id_budget:
                    for pline in order.order_line:
                        for p in id_budget:
                            for line in p.crossovered_budget_line:
                                if line.planned_amount > 0.0:
                                    prod_account_id=pline.product_id.product_tmpl_id.get_product_accounts(fiscal_pos=order.fiscal_position_id)['expense']
                                    if (line.analytic_account_id.id==pline.account_analytic_id.id) and (line.account_id.id==prod_account_id.id):
                                        line.write({'amount_purchase':line.amount_purchase - pline.price_subtotal})
        super(PurchaseOrder, self).button_cancel()