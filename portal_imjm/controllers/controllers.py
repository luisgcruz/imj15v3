# -*- coding: utf-8 -*-
import base64

from odoo import http, fields
from odoo.http import content_disposition, Controller, request, route
from odoo.addons.portal.controllers.portal import CustomerPortal
from odoo.tools.mimetypes import guess_mimetype
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as DF
from lxml import objectify
from dateutil.relativedelta import relativedelta
from datetime import datetime as DT

File_Type = ['application/pdf']  # allowed file type
File_xml_type = ['image/svg+xml']  # tipo xml

CustomerPortal.OPTIONAL_BILLING_FIELDS.append('valid_until')
CustomerPortal.OPTIONAL_BILLING_FIELDS.append('partner')
CustomerPortal.OPTIONAL_BILLING_FIELDS.append('attachment')
CustomerPortal.OPTIONAL_BILLING_FIELDS.append('estado_opinion')
CustomerPortal.OPTIONAL_BILLING_FIELDS.append('opinion_msg_stat')

class CustomerPortal(CustomerPortal):


    @http.route(['/upload/opinion/'], type='http', auth="user", method="post", csrf=False, website=True)
    def upload_opinion_sat(self, **post):
        partner_id_int = post.get('partner') and int(post.get('partner')) or False
        partner_id = request.env['res.partner'].browse(partner_id_int)
        if partner_id.parent_id:
            partner_id = partner_id.parent_id
        select_value = dict(request.env['res.partner']._fields['estado_opinion'].selection)
        if post.get('attachment', False):
            file = post.get('attachment')
            attachment = file.read()
            mimetype = guess_mimetype(base64.b64decode(base64.encodebytes(attachment)))
            if mimetype in File_Type:
                partner_id.sudo(True).write({'opinion_sat': base64.encodebytes(attachment), 'estado_opinion': 'revision'})
            else:
                return request.render('portal_imjm.portal_imjm_template_partner', {'error':{'opinion_msg_stat': 'Archivo no valido'},
                                                                                   'partner': partner_id,
                                                                                   'estado_opinion': 'Su archivo no pudo ser enviado! Motivo:',
                                                                                   'opinion_msg_stat': 'El archivo no se identifico como .PDF v??lido'})

        return request.render('portal_imjm.portal_imjm_template_partner', {'error':{'partner': 'Correcto'},
                                                                           'partner': partner_id,
                                                                           'opinion_msg_stat': 'El archivo fue subido correctamente.',
                                                                           'estado_opinion': select_value.get(partner_id.estado_opinion) or 'En revisi??n',
                                                                           'valid_until': partner_id.valid_until or 'Fecha: por definir'})

    #funcion para subir xmls y pdfs de factura
    @http.route(['/upload/archivos_factura/'], type='http', auth="user", method="post", csrf=False, website=True)
    def upload_archivos_factura(self, orden_id=None, access_token=None, **post):
        order_id_int = orden_id and int(orden_id) or None
        order_sudo = request.env['purchase.order'].sudo().browse(order_id_int)
        if not order_id_int:
            #lo ideal seria que retornara con return request.redirect(order_sudo.get_portal_url()) #pero al no tener order_id, truena
            return request.redirect('/my/purchase')
        errores = ''
        validacion_partner = self.validar_partner_con_sat(order_sudo.partner_id)
        if validacion_partner:
            errores += 'Error en proveedor! ' + validacion_partner
        values = self._purchase_order_get_page_view_values(order_sudo, access_token, **post)
        para_escribir = {}
        if post.get('adjunto_pdf', False) and post.get('adjunto_xml', False):
            file = post.get('adjunto_pdf')
            attachment = file.read()
            mimetype = guess_mimetype(base64.b64decode(base64.encodebytes(attachment)))
            if mimetype in File_Type:
                para_escribir['ultimo_pdf'] = base64.encodebytes(attachment)
            else:
                errores += 'Error de usuario! El archivo .pdf no es un archivo .pdf v??lido.'
            #fin analisis de pdf, comienza xml
            file = post.get('adjunto_xml')
            attachment = file.read()
            #mimetype = guess_mimetype(base64.b64decode(base64.encodebytes(attachment)))
            #if mimetype in File_xml_type: #la validacion ya la hace validar xml portal()
            validacion = self.validar_xml_portal(attachment, order_sudo)
            if validacion[0]:
                errores += 'Error en xml! ' + validacion[1]
            else:
                para_escribir['ultimo_xml'] = base64.encodebytes(attachment)
            #else:
            #    errores += 'Error de usuario! El archivo .xml no es un archivo .xml v??lido.'
        else:
            errores += 'Error de usuario! Ambos archivos son requeridos al adjuntar.'
        #parte final
        if not errores:
            if order_sudo.invoice_status == 'invoiced':
                values['upload_status_msg'] = 'Error de usuario! El pedido de compra ya cuenta con una factura activa previa.'
            else:
                new_inv = order_sudo.action_create_invoice()
                if new_inv:
                    new_inv.l10n_mx_edi_cfdi_uuid = validacion[1] #no esta funcionando en v13
                    new_inv.date = validacion[2]
                    new_inv.invoice_date = validacion[2]
                    new_inv.estado_factura_portal = 'revision'
                    order_sudo.invoice_from_portal = new_inv.id
                    request.env['ir.attachment'].sudo().create(
                        {
                            'name': validacion[1] + '.xml',
                            'datas': para_escribir['ultimo_xml'],
                            'res_model': request.env['account.move']._name,
                            'res_id': new_inv.id,
                            'type': 'binary'
                        })
                    request.env['ir.attachment'].sudo().create(
                        {
                            'name': validacion[1] + '.pdf',
                            'datas': para_escribir['ultimo_pdf'],
                            'res_model': request.env['account.move']._name,
                            'res_id': new_inv.id,
                            'type': 'binary'
                        })
                    order_sudo.invoice_status = 'invoiced'
                    new_inv.l10n_mx_edi_cfdi_name = validacion[1] + '.xml'
                values['upload_status_msg'] = 'Correcto'
        else:
            values['upload_status_msg'] = errores
        return request.render('portal_imjm.portal_imjm_template_purchase_order_form', values)

    def get_node(self, cfdi_node, attribute, namespaces):
        if hasattr(cfdi_node, 'Complemento'):
            node = cfdi_node.Complemento.xpath(attribute, namespaces=namespaces)
            return node[0] if node else None
        else:
            return None

    def validar_xml_portal(self, arch_xml, purch_order_rec):
        try:
            xml_tree = objectify.fromstring(arch_xml)
        except:
            try:
                cadena = arch_xml.decode('utf-8')
                cadena = cadena.replace('xmlns:schemaLocation="http://www.sat.gob.mx/reg',
                                        'xsi:schemaLocation="http://www.sat.gob.mx/reg')
                xml_tree = objectify.fromstring(cadena)
            except:
                return (True, 'El archivo xml no tiene una estructura v??lida. cont: %s.' % str(arch_xml)[:30])
        tipo_cfdi = xml_tree.get('TipoDeComprobante', 'F').upper()
        if tipo_cfdi != 'I':
            tipos_cfdi = {'P': 'un complemento de pago', 'E': 'una nota de cr??dito', 'T': 'una Carta Porte', 'N': 'de n??mina', 'F': 'inv??lido'}
            return (True, 'El CFDI no es una factura, es %s. Verifique que el archivo a subir es el correcto.' % tipos_cfdi.get(tipo_cfdi))
        errores = ''
        conteoe = 0
        if hasattr(xml_tree, 'Emisor') and hasattr(xml_tree, 'Receptor'):
            rfc_emisor = xml_tree.Emisor.attrib['Rfc'].upper()
            rfc_receptor = xml_tree.Receptor.attrib['Rfc'].upper()
            if purch_order_rec.partner_id.vat and (purch_order_rec.partner_id.vat.upper() != rfc_emisor):
                errores += '\n -El RFC del proveedor del xml no coincide con el del sistema. (%s vs %s) '%(rfc_emisor, purch_order_rec.partner_id.vat)
                conteoe += 1
            if purch_order_rec.company_id.vat.upper() != rfc_receptor:
                errores += '\n -El RFC del receptor del xml no coincide con el del sistema. (%s vs %s) '%(rfc_receptor, purch_order_rec.company_id.vat)
                conteoe += 1
        else:
            return (True, 'El archivo xml no contiene los nodos de emisor y receptor.')
        #termina analisis de rfcs, continua analisis de monto
        monto_xml = float(xml_tree.get('Total', 0))
        monto_orden = purch_order_rec.amount_total
        #if monto_orden != monto_xml:
        if not (monto_xml >= monto_orden - 0.5 and monto_xml <= monto_orden + 0.5):
            errores += '\n -El monto del xml no coincide con el total de la orden de compra. (%s vs %s) ' % (monto_xml, monto_orden)
            conteoe += 1
        #comienza chequeo de que sea un producto aceptable
        product_sat_obj = request.env['product.unspsc.code']
        aceptados = product_sat_obj.search([('aceptable', '=', True)])
        lista_codigos = [x.code for x in aceptados]
        for e in xml_tree.findall('.//'):
            if e.tag == "{http://www.sat.gob.mx/cfd/3}Concepto":
                claveprod = e.attrib['ClaveProdServ']
                if claveprod not in lista_codigos:
                    errores += '\n -El codigo de producto %s no es aceptado por nuestra compa????a. '%claveprod
                    conteoe += 1
        #fin analisis de productos
        fecha_factura = DT.strptime(xml_tree.get('Fecha', 'Sin nodo fecha')[:10], '%Y-%m-%d')
        metodopago = xml_tree.get('MetodoPago', 'Ninguno')
        if metodopago.upper() != 'PPD':
            errores += '\n -La factura no tiene el m??todo de pago PPD (encontrado: %s)' % metodopago
            conteoe += 1
        #comienza chequeo de existencia del uuid
        acc_move_obj = request.env['account.move']
        tfd_node = self.get_node(xml_tree, 'tfd:TimbreFiscalDigital[1]', {'tfd': 'http://www.sat.gob.mx/TimbreFiscalDigital'},)
        uuid_factura = tfd_node.get('UUID')
        if not uuid_factura:
            errores += '\n No se encontr?? el folio fiscal UUID en el archivo, verificar que sea el correcto.'
            conteoe += 1
        try:
            nombre_arch = xml_tree.attrib['Serie'] + xml_tree.attrib['Folio']
        except:
            nombre_arch = uuid_factura
        facturas_cargadas = acc_move_obj.search([('l10n_mx_supplier_cfdi_uuid', '=', uuid_factura), ('move_type', '=', 'in_invoice')])
        if facturas_cargadas:
            for factura in facturas_cargadas:
                errores += '\n -El UUID %s ya fue cargado en la factura %s.' % (uuid_factura, factura.name)
                conteoe += 1
        if conteoe == 0:
            return (False, uuid_factura, fecha_factura, nombre_arch)
        else:
            return (True, 'Errores encontrados: %s. Descripci??n: %s.' % (conteoe, errores))

    def validar_partner_con_sat(self, partner):
        if partner.parent_id:
            partner = partner.parent_id
        fecha_validez = partner.valid_until
        if not fecha_validez:
            return 'Por favor cargue el documento de la Opinion del SAT en el men?? "Mi cuenta" antes de intentar subir facturas.'
        fecha_hoy = fields.date.today()
        if (fecha_validez - fecha_hoy).days < 1:
            return 'La opini??n del SAT del proveedor ha expirado: tiene m??s de 90 d??as.'
        if partner.estado_opinion not in ['valida']:
            return 'La opini??n del SAT del proveedor no es v??lida.'
        # validar que el RFC del proveedor no est?? en la lista negra del sat. ##Hecho en modulo aparte
        pagos_obj = request.env['account.payment']
        #fecha_limite = fields.Date.today() - relativedelta(days=30)
        fecha_limite = fields.Date.today() - relativedelta(day=1, hour=0, minute=0, second=0, microsecond=0)  # busca el mes anterior
        if partner.exigir_complemento:
            pagos_sin_rep = pagos_obj.search(
                [('date', '<', fecha_limite.strftime(DF)), ('partner_id', '=', partner.id),
                 ('state', '=', 'posted'), ('partner_type', '=', 'supplier'), ('estado_rep_cfdi', '!=','cargado')])
            for pago in pagos_sin_rep:
                if fields.Datetime.now() > fields.Date.today() - relativedelta(day=11, hour=0, minute=0): #dia 5 del mes
                    return 'El proveedor tiene complementos de pago sin subir del mes anterior. (%s)' % pago.ref
        return None

    ###subir complemento de pago
    @http.route(['/upload/archivos_cpago/'], type='http', auth="user", method="post", csrf=False, website=True)
    def upload_archivos_complemento(self, orden_id=None, access_token=None, **post):
        order_id_int = orden_id and int(orden_id) or None
        order_sudo = request.env['account.payment'].sudo().browse(order_id_int)
        if not order_id_int:
            # lo ideal seria que retornara con return request.redirect(order_sudo.get_portal_url()) #pero al no tener order_id, truena
            return request.redirect('/my/pago')
        errores = ''
        values = self._account_payment_get_page_view_values(order_sudo, access_token, **post)
        para_escribir = {}
        if post.get('adjunto_pdf', False) and post.get('adjunto_xml', False):
            file = post.get('adjunto_pdf')
            attachment = file.read()
            mimetype = guess_mimetype(base64.b64decode(base64.encodebytes(attachment)))
            if mimetype in File_Type:
                para_escribir['ultimo_pdf'] = base64.encodebytes(attachment)
            else:
                errores += 'Error de usuario! El archivo .pdf no es un archivo .pdf v??lido.'
            # fin analisis de pdf, comienza xml
            file = post.get('adjunto_xml')
            attachment = file.read()
            #mimetype = guess_mimetype(base64.b64decode(base64.encodebytes(attachment)))
            #if mimetype in File_xml_type: #la validacion ya la hace metodo validar xml pago
            validacion = self.validar_xml_pago(attachment, order_sudo)
            if validacion[0]:
                errores += 'Error en xml! ' + validacion[1]
            else:
                para_escribir['ultimo_xml'] = base64.encodebytes(attachment)
            #except:
            #    errores += 'Error de usuario! El archivo .xml no es un archivo .xml v??lido.'
        else:
            errores += 'Error de usuario! Ambos archivos son requeridos al adjuntar.'
        # parte final
        if not errores:
            if order_sudo.estado_rep_cfdi == 'cargado':
                values[
                    'upload_status_msg'] = 'Error de usuario! El complemento de pago ya ha sido cargado para este registro.'
            else:
                request.env['ir.attachment'].sudo().create(
                    {
                        'name': validacion[3] + '.pdf',
                        'datas': para_escribir['ultimo_pdf'],
                        'res_model': request.env['account.payment']._name,
                        'res_id': order_sudo.id,
                        'type': 'binary'
                    })
                request.env['ir.attachment'].sudo().create(
                    {
                        'name': validacion[3] + '.xml',
                        'datas': para_escribir['ultimo_xml'],
                        'res_model': request.env['account.payment']._name,
                        'res_id': order_sudo.id,
                        'type': 'binary'
                    })
                values['upload_status_msg'] = 'Correcto'
                order_sudo.write({'estado_rep_cfdi': 'cargado',
                                  'l10n_mx_edi_cfdi_name': validacion[3] + '.xml',
                                  'l10n_mx_edi_pac_status': 'retry'})
        else:
            values['upload_status_msg'] = errores
        return request.render('portal_imjm.portal_my_pago', values)

    def validar_xml_pago(self, arch_xml, acc_paymnt_rec):
        try:
            xml_tree = objectify.fromstring(arch_xml)
        except:
            try:
                cadena = arch_xml.decode('utf-8')
                cadena = cadena.replace('xmlns:schemaLocation="http://www.sat.gob.mx/reg',
                                        'xsi:schemaLocation="http://www.sat.gob.mx/reg')
                xml_tree = objectify.fromstring(cadena)
            except:
                return (True, 'El archivo xml no tiene una estructura v??lida. cont: %s.' % str(arch_xml)[:30])
        tipo_cfdi = xml_tree.get('TipoDeComprobante', 'F').upper()
        if tipo_cfdi != 'P':
            tipos_cfdi = {'I': 'una factura', 'E': 'una nota de cr??dito', 'T': 'una Carta Porte', 'N': 'de n??mina', 'F': 'inv??lido'}
            return (True, 'El CFDI no es de pagos, es %s. Verifique que el archivo a subir es el correcto.'%tipos_cfdi.get(tipo_cfdi))
        conteoe = 0
        errores = ''
        if hasattr(xml_tree, 'Emisor') and hasattr(xml_tree, 'Receptor'):
            rfc_emisor = xml_tree.Emisor.attrib['Rfc'].upper()
            rfc_receptor = xml_tree.Receptor.attrib['Rfc'].upper()
            if acc_paymnt_rec.partner_id.vat and (acc_paymnt_rec.partner_id.vat.upper() != rfc_emisor):
                errores += '\n -El RFC del proveedor del xml no coincide con el del sistema. (%s vs %s)'%(rfc_emisor, acc_paymnt_rec.partner_id.vat)
                conteoe += 1
            if acc_paymnt_rec.company_id.vat.upper() != rfc_receptor:
                errores += '\n -El RFC del receptor del xml no coincide con el del sistema. (%s vs %s)'%(rfc_receptor, acc_paymnt_rec.company_id.vat)
                conteoe += 1
        else:
            return (True, 'El archivo xml no contiene los nodos de emisor y receptor.')
        #termina analisis de rfcs, continua analisis de monto
        monto_xml = 0
        for e in xml_tree.findall('.//'):
            if e.tag == "{http://www.sat.gob.mx/Pagos}Pago" or e.tag == "{http://www.sat.gob.mx/Pagos20}Pago":  # version 1.0
                monto_xml = float(e.get('Monto'))
                fecha_pago = DT.strptime(e.get('FechaPago', 'Error fecha')[:10], '%Y-%m-%d')
                forma_pagop = e.get('FormaDePagoP')
                lineas_pago = e.getchildren()
        monto_orden = acc_paymnt_rec.amount
        if monto_orden != monto_xml:
            errores += '\n -El monto del xml no coincide con el total del pago. (%s vs %s)' % (monto_xml, monto_orden)
            conteoe += 1
        if fecha_pago.strftime('%Y-%m-%d') != acc_paymnt_rec.date.strftime('%Y-%m-%d'):
            errores += '\n -La fecha del xml no coincide con la del pago. (%s vs %s)' % (fecha_pago, acc_paymnt_rec.date)
            conteoe += 1
        forma_pago_odoo = acc_paymnt_rec.l10n_mx_edi_payment_method_id.code
        if forma_pagop != forma_pago_odoo:
            errores += '\n -La forma de pago del xml no coincide con la del registro. (%s vs %s)' % (forma_pagop, forma_pago_odoo)
            conteoe += 1
        #uuid_factura = acc_paymnt_rec.communication
        uuid_factura = ''
        facturas_sin_uuid = ''
        for linea in acc_paymnt_rec.reconciled_bill_ids:
            if not linea.l10n_mx_edi_cfdi_uuid:
                facturas_sin_uuid = facturas_sin_uuid + linea.name + ' '
                conteoe += 1
                continue
            uuid_factura = uuid_factura + linea.l10n_mx_edi_cfdi_uuid + ' '
        if facturas_sin_uuid:
            errores += '\n -Las facturas %s asociadas a este pago no cuentan con archivo xml cargado, no es posible validar el pago.' % facturas_sin_uuid
            return (True, 'Errores encontrados: %s. Descripci??n: %s.' % (conteoe, errores))
        for pagol in lineas_pago:
            if pagol.get('IdDocumento'):
                if pagol.get('IdDocumento').upper() not in uuid_factura.upper():
                    errores += '\n -El uuid pagado del xml no coincide con la de la factura. (%s vs %s)' % (pagol.attrib['IdDocumento'], uuid_factura)
                    conteoe += 1
        if not lineas_pago:
            errores += '\n -El complemento de pago no tiene ninguna factura a la que se le est?? aplicando el pago, por favor vuelva a generar su complemento de pago.'
            conteoe += 1
        #fin de validaciones
        tfd_node = self.get_node(xml_tree, 'tfd:TimbreFiscalDigital[1]', {'tfd': 'http://www.sat.gob.mx/TimbreFiscalDigital'},)
        uuid_factura = tfd_node.get('UUID')
        if not uuid_factura:
            errores += '\n No se encontr?? el folio fiscal UUID del CFDI, por favor revise que sea el archivo correcto'
            conteoe += 1
        try:
            nombre_arch = xml_tree.attrib['Serie'] + xml_tree.attrib['Folio']
        except:
            nombre_arch = uuid_factura
        if conteoe == 0:
            return (False, uuid_factura, fecha_pago, nombre_arch)
        else:
            return (True, 'Errores encontrados: %s. Descripci??n: %s.' % (conteoe, errores))