# -*- coding: utf-8 -*-
from odoo import fields
from odoo.tools import sql

# ignore update column if the column is int4 and the field is int8
def update_db_column(self, model, column):
    """ Create/update the column corresponding to ``self``.

        :param model: an instance of the field's model
        :param column: the column's configuration (dict) if it exists, or ``None``
    """
    if not column:
        # the column does not exist, create it
        sql.create_column(model._cr, model._table, self.name, self.column_type[1], self.string)
        return
    if column['udt_name'] == self.column_type[0]:
        return
    # ignore the case when the column is int4 and the field is int8
    # so no field update needed
    if column['udt_name'] == 'int4' and self.column_type[0] == 'int8':
        return
    if column['is_nullable'] == 'NO':
        sql.drop_not_null(model._cr, model._table, self.name)
    self._convert_db_column(model, column)


fields.Field.update_db_column = update_db_column


# because odoo does not support int8 in following fields
# we directly modify the column_type of these fields globally

fields.Integer.column_type = ('int8', 'int8')
fields.Id.column_type = ('int8', 'int8')
fields.Many2one.column_type = ('int8', 'int8')


def convert_to_cache(self, value, record, validate=True):
    if not validate:
        return value or None
    if value and (
            self.column_type[0] == 'int4' or self.column_type[0] == 'int8'):
        value = int(value)
    if value in self.get_values(record.env):
        return value
    elif not value:
        return None
    raise ValueError("Wrong value for %s: %r" % (self, value))


fields.Selection.convert_to_cache = convert_to_cache


from . import models
