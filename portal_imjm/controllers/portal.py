# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from collections import OrderedDict
import base64

from odoo import http, _
from odoo.exceptions import AccessError, MissingError
from odoo.http import request
from odoo.addons.portal.controllers.portal import CustomerPortal, pager as portal_pager
from odoo.tools import image_process
from odoo.addons.web.controllers.main import Binary


class CustomerPortal(CustomerPortal):

    def _prepare_home_portal_values(self, counters):
        values = super(CustomerPortal, self)._prepare_home_portal_values(counters)
        #if 'pagos_count' in counters:
        partner_id = request.env.user.partner_id.parent_id and request.env.user.partner_id.parent_id.id or request.env.user.partner_id.id
        if not request.env.user.has_group('base.group_portal'):
            values['pagos_count'] = request.env['account.payment'].sudo(True).search_count([('payment_type', '=', 'outbound'), ('state', '!=', 'cancel')])
        else:
            values['pagos_count'] = request.env['account.payment'].sudo(True).search_count([('payment_type', '=', 'outbound'), ('partner_id', '=', partner_id), ('state', '!=', 'cancel')])
        values['purchase_count'] = request.env['purchase.order'].search_count([('state', 'in', ['purchase', 'done', 'draft']), ('approval', '=', True)]) if request.env['purchase.order'].check_access_rights('read', raise_exception=False) else 0
        return values

    def _account_payment_get_page_view_values(self, payment, access_token, **kwargs):
        #
        #def resize_to_48(b64source):
        #    if not b64source:
        #        b64source = base64.b64encode(Binary.placeholder())
        #    return image_process(b64source, size=(48, 48))

        values = {
            'order': payment,
            #'resize_to_48': resize_to_48,
        }
        return self._get_page_view_values(payment, access_token, values, 'my_pago_history', False, **kwargs)

    #sobreescribir funcion de lista de purchase orders
    @http.route(['/my/purchase', '/my/purchase/page/<int:page>'], type='http', auth="user", website=True)
    def portal_my_purchase_orders(self, page=1, date_begin=None, date_end=None, sortby=None, filterby=None, **kw):
        values = self._prepare_portal_layout_values()
        PurchaseOrder = request.env['purchase.order']
        domain = []
        #domain = ['release_date', 'not in', False] #en caso de que no les guste ver vacios
        archive_groups = self._get_archive_groups('purchase.order', domain) if values.get('my_details') else []
        if date_begin and date_end:
            domain += [('create_date', '>', date_begin), ('create_date', '<=', date_end)]
        searchbar_sortings = {
            'date': {'label': _('Newest'), 'order': 'create_date desc, id desc'},
            'name': {'label': _('Name'), 'order': 'name asc, id asc'},
            'amount_total': {'label': _('Total'), 'order': 'amount_total desc, id desc'},
        }
        # default sort by value
        if not sortby:
            sortby = 'date'
        order = searchbar_sortings[sortby]['order']
        searchbar_filters = {
            'all': {'label': _('All'), 'domain': [('state', 'in', ['purchase', 'done', 'cancel', 'draft'])]},
            'purchase': {'label': _('Purchase Order'), 'domain': [('state', '=', 'purchase')]},
            'draft': {'label': _('Presupuesto'), 'domain': [('state', '=', 'draft')]},
            'done': {'label': _('Locked'), 'domain': [('state', '=', 'done')]},
        }
        # default filter by value
        if not filterby:
            filterby = 'all'
        domain += searchbar_filters[filterby]['domain']

        # count for pager
        purchase_count = PurchaseOrder.search_count(domain)
        # make pager
        pager = portal_pager(
            url="/my/purchase",
            url_args={'date_begin': date_begin, 'date_end': date_end},
            total=purchase_count,
            page=page,
            step=self._items_per_page
        )
        # search the purchase orders to display, according to the pager data
        orders = PurchaseOrder.search(
            domain,
            order=order,
            limit=self._items_per_page,
            offset=pager['offset']
        )
        request.session['my_purchases_history'] = orders.ids[:100]

        values.update({
            'date': date_begin,
            'orders': orders,
            'page_name': 'purchase',
            'pager': pager,
            'archive_groups': archive_groups,
            'searchbar_sortings': searchbar_sortings,
            'sortby': sortby,
            'searchbar_filters': OrderedDict(sorted(searchbar_filters.items())),
            'filterby': filterby,
            'default_url': '/my/purchase',
        })
        return request.render("purchase.portal_my_purchase_orders", values)

    # ------------------------------------------------------------
    # Mis pagos
    # ------------------------------------------------------------
    def _pago_get_page_view_values(self, pago, access_token, **kwargs):
        values = {
            'page_name': 'pago',
            'task': pago,
            'user': request.env.user
        }
        return self._get_page_view_values(pago, access_token, values, 'my_pago_history', False, **kwargs)

    #vista lista
    @http.route(['/my/pago', '/my/pago/page/<int:page>'], type='http', auth="user", website=True)
    def portal_my_pagos(self, page=1, date_begin=None, date_end=None, sortby=None, filterby=None, **kw):
        values = self._prepare_portal_layout_values()
        AccountPayment = request.env['account.payment'].sudo(True)
        partner_id = request.env.user.partner_id.parent_id and request.env.user.partner_id.parent_id.id or request.env.user.partner_id.id
        if not request.env.user.has_group('base.group_portal'):
            domain = []
        else:
            domain = [('partner_id', '=', partner_id)]

        if date_begin and date_end:
            domain += [('create_date', '>', date_begin), ('create_date', '<=', date_end)]

        searchbar_sortings = {
            'date': {'label': _('Newest'), 'order': 'create_date desc, id desc'},
            'name': {'label': _('Name'), 'order': 'name asc, id asc'},
        }
        # default sort by value
        if not sortby:
            sortby = 'date'
        order = searchbar_sortings[sortby]['order']

        searchbar_filters = {
            'all': {'label': _('All'), 'domain': [('state', 'in', ['draft', 'posted', 'cancel']),('payment_type', '=', 'outbound')]},
            'cancel': {'label': _('Cancelled'), 'domain': [('state', '=', 'cancel'),('payment_type', '=', 'outbound')]},
            'done': {'label': _('Locked'), 'domain': [('state', '=', 'posted'),('payment_type', '=', 'outbound')]},
        }
        # default filter by value
        if not filterby:
            filterby = 'all'
        domain += searchbar_filters[filterby]['domain']

        # count for pager
        pagos_count = AccountPayment.search_count(domain)
        # make pager
        pager = portal_pager(
            url="/my/pago",
            url_args={'date_begin': date_begin, 'date_end': date_end, 'sortby': sortby, 'filterby': filterby},
            total=pagos_count,
            page=page,
            step=self._items_per_page
        )
        # search the account payments to display, according to the pager data
        orders = AccountPayment.search(
            domain,
            order=order,
            limit=self._items_per_page,
            offset=pager['offset']
        )
        request.session['my_pago_history'] = orders.ids[:100] #no se que hace

        values.update({
            'date': date_begin,
            'orders': orders,
            'page_name': 'pagos',
            'pager': pager,
            'searchbar_sortings': searchbar_sortings,
            'sortby': sortby,
            'searchbar_filters': OrderedDict(sorted(searchbar_filters.items())),
            'filterby': filterby,
            'default_url': '/my/pago',
        })
        return request.render("portal_imjm.portal_my_pagos", values)

    #Vista form
    @http.route(['/my/pago/<int:order_id>'], type='http', auth="public", website=True)
    def portal_my_pago(self, order_id=None, access_token=None, **kw):
        try:
            order_sudo = self._document_check_access('account.payment', order_id, access_token=access_token)
        except (AccessError, MissingError):
            return request.redirect('/my')

        report_type = kw.get('report_type')
        if report_type in ('html', 'pdf', 'text'):
            return self._show_report(model=order_sudo, report_type=report_type, report_ref='account.action_report_payment_receipt', download=kw.get('download'))

        values = self._account_payment_get_page_view_values(order_sudo, access_token, **kw)
        return request.render("portal_imjm.portal_my_pago", values)

    def _account_payment_get_page_view_values(self, order, access_token, **kwargs):
        #
        def resize_to_48(b64source):
            if not b64source:
                b64source = base64.b64encode(Binary.placeholder())
            return image_process(b64source, size=(48, 48))

        values = {
            'order': order,
            'resize_to_48': resize_to_48,
        }
        return self._get_page_view_values(order, access_token, values, 'my_pago_history', False, **kwargs)