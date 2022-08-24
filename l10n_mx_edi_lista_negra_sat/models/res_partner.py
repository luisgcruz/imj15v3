# -*- coding: utf-8 -*-
from odoo import fields, models, api, SUPERUSER_ID
import io
import requests, base64
import csv
from odoo.exceptions import UserError


class ResPartner(models.Model):
    _inherit = 'res.partner'

    estado_listado_sat = fields.Selection([
        ('novalidado', 'No Validado'),
        ('correcto', 'Correcto, no listado'),
        ('presunto', 'En Lista: Presunto'),
        ('sentencia favorable', 'En Lista: Sentencia Favorable'),
        ('desvirtuado', 'En Lista: Desvirtuado'),
        ('definitivo', 'En Lista: Definitivo'),
    ], default='novalidado', string='Estado en la lista')

    def write(self, values):
        if 'estado_listado_sat' in values:
            self.message_post(body=('Se cambió el estado en la lista negra del SAT a: %s.'%values['estado_listado_sat']))
        return super(ResPartner, self).write(values)


class ResPartnerListaNegra(models.Model):
    _name = 'res.partner.lista.negra'
    _description = "Modelo para guardar las listas negras del sat"

    lista_negra_csv = fields.Binary(string='Lista negra del SAT.csv', help='Archivo .csv descargado del sitio del SAT.', copy=False)
    fecha_sincro = fields.Datetime(string='Sincronizada el', copy=False, help='Fecha en la que se realizó la última sincronización con el SAT.')
    name = fields.Char(string='Descripción', required=True)
    state = fields.Selection([('activo', 'Activo'), ('inactivo', 'Inactivo')], string = 'Estado', default='inactivo')
    csv_filename = fields.Char(string='Nombre del archivo', default='Lista negra Sat.csv')
    resultado_sinc = fields.Char(string='Resultado')


    def sincronizar_lista_sat(self):
        if self.fecha_sincro:
            tiempo_delta = fields.Datetime.now() - self.fecha_sincro
            if (tiempo_delta.seconds//300) < 1: #si no ha pasado 5 minutos
                raise UserError('Por favor espera 5 minutos desde la última sincronización para volver a sincronizar')
        liga_sat = 'http://omawww.sat.gob.mx/cifras_sat/Documents/Listado_Completo_69-B.csv'
        response = requests.get(liga_sat)
        archivo_csv = io.StringIO(response.text)
        datos_csv = archivo_csv.read()
        lines = datos_csv.splitlines()
        reader = csv.reader(lines, delimiter=',')
        datos = {}
        for fila in reader:
            datos[fila[1]] = {'Razon social': fila[2], 'Situacion': fila[3], 'num_fila': fila[0]}
        todos_partners_ids = self.env['res.partner'].search([])
        query = "UPDATE res_partner SET estado_listado_sat = 'correcto'"
        self._cr.execute(query)
        partners_rfc = todos_partners_ids.read(['vat'])
        rfc_list = list(map(lambda x: x['vat'], partners_rfc))
        res = 'Sincronización exitosa: ninguno de sus contactos está en la lista negra del SAT'
        for prfc in rfc_list:
            if prfc != '' and prfc in datos:
                if datos[prfc]['Razon social']:
                    bad_partner = self.env['res.partner'].search([('vat', '=', prfc)])
                    bad_partner.estado_listado_sat = datos[prfc]['Situacion'].lower()
                    res = 'Advertencia: Se encontró al menos uno de sus contactos en la lista negra del SAT. Vaya a la lista vista y utilize el filtro -Lista negra SAT'
        self.write({'lista_negra_csv': base64.b64encode(datos_csv.encode('UTF-8')), 'fecha_sincro': fields.Datetime.now(), 'resultado_sinc': res})
        archivo_csv.close()
        return True

    def mark_this_active(self):
        todas = self.search([])
        todas.state = 'inactivo'
        self.state = 'activo'
        return True

    @api.model
    def _cron_sincronizar_lista_sat(self):
        for lista in self.search([]):
            if lista.state == 'activo':
                lista.sincronizar_lista_sat()
        return True