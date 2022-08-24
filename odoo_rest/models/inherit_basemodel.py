from odoo.models import BaseModel
import odoo
from odoo import api
from odoo.http import request
from odoo import api, fields, models, _, SUPERUSER_ID
from odoo.exceptions import AccessDenied, AccessError, UserError, ValidationError ,MissingError
import logging
_logger = logging.getLogger(__name__)


class BaseModel(models.AbstractModel):
    _inherit = 'base'

    def read(self, fields=None, load='_classic_read'):
        if request.context.get("odoo_rest_api"):
            fields = self.check_field_access_rights('read', fields)
            # fetch stored fields from the database to the cache
            stored_fields = set()
            for name in fields:
                field = self._fields.get(name)
                if not field:
                    raise ValueError("Invalid field %r on model %r" % (name, self._name))
                if field.store:
                    stored_fields.add(name)
                elif field.compute:
                    # optimization: prefetch direct field dependencies
                    for dotname in field.depends:
                        f = self._fields[dotname.split('.')[0]]
                        if f.prefetch and (not f.groups or self.user_has_groups(f.groups)):
                            stored_fields.add(f.name)
            self._read(stored_fields)

            # retrieve results from records; this takes values from the cache and
            # computes remaining fields
            data = [(record, {'id': record._ids[0]}) for record in self]
            use_name_get = (load == '_classic_read')
            for name in fields:
                convert = self._fields[name].convert_to_read
                for record, vals in data:
                    # missing records have their vals empty
                    if not vals:
                        continue
                    try:
                        vals[name] = convert(record[name], record, use_name_get)
                        if record._fields.get(name).type == "datetime":

                            vals[name] = odoo.fields.Datetime.to_string(vals[name])
                        elif record._fields.get(name).type == "date":
                            vals[name] = odoo.fields.Date.to_string(vals[name])
                        elif record._fields.get(name).type == "binary":
                            vals[name] = vals[name].decode('utf-8')

                    except MissingError:
                        vals.clear()
            result = [vals for record, vals in data if vals]

            return result

        else:
            result = super(BaseModel,self).read(fields=fields, load=load)
            return result
