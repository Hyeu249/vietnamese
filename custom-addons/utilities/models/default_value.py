# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from . import CONST
from odoo.exceptions import ValidationError


class DefaultValue(models.Model):
    _name = "utilities.default.value"
    _description = "Default value records"
    _inherit = ["utilities.notification"]

    variable_name = fields.Selection(
        CONST.DEFAULT_VALUE_VARIABLE_NAMES,
        string="Variable name",
        tracking=True,
    )

    value_type = fields.Selection(
        CONST.VALUE_TYPES,
        string="Value type",
        compute="_get_value_type",
        tracking=True,
    )

    description = fields.Char(string="Description", tracking=True)
    str_field = fields.Char(string="String value", tracking=True)
    int_field = fields.Integer(string="Int value", tracking=True)
    float_field = fields.Float(string="Float value", tracking=True)
    date_field = fields.Date(string="Date value", tracking=True)
    html_field = fields.Html(string="Html value", tracking=True)

    def get_description(self):
        for record in self:
            record.description = record.variable_name

    # Define SQL constraint
    _sql_constraints = [
        (
            "unique_variable_name",
            "unique (variable_name)",
            "variable_name must be unique.",
        ),
    ]

    # relations
    user_ids = fields.Many2many("res.users", string="Users")
    group_ids = fields.Many2many("res.groups", string="Groups")
    default_value_for_relation_ids = fields.One2many(
        "utilities.default.value.for.relation",
        "default_value_id",
        string="Default values for relation",
    )

    # sequential
    ref = fields.Char(string="Code", default=lambda self: _("New"))

    # company

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            model_name = "utilities.default.value"
            vals["ref"] = self.env["ir.sequence"].next_by_code(model_name)

        result = super(DefaultValue, self).create(vals_list)
        return result

    def name_get(self):
        result = []
        for report in self:
            name = report.ref or _("New")
            result.append((report.id, name))
        return result

    def _get_value_type_by_its_variable_name(self):
        self.ensure_one()
        message_1 = f"Tên biên không hợp lệ cho giá trị mặc định-{self.variable_name}!"
        message_2 = f"Tên biên không chứa loại giá trị cho giá trị mặc định-{self.variable_name}!"

        if not self.variable_name:
            return

        split_var = self.variable_name.split("_")
        first_char_value_type = split_var[0]
        TYPES_VALUES = [tupple[0] for tupple in CONST.VALUE_TYPES]

        if not split_var:
            raise ValidationError(message_1)

        if first_char_value_type not in TYPES_VALUES:
            raise ValidationError(message_2)

        return first_char_value_type

    @api.depends("variable_name")
    def _get_value_type(self):
        for record in self:
            first_char_value_type = record._get_value_type_by_its_variable_name()

            if not first_char_value_type:
                record.value_type = False

            if first_char_value_type == CONST.STRING:
                record.value_type = CONST.STRING

            if first_char_value_type == CONST.INTEGER:
                record.value_type = CONST.INTEGER

            if first_char_value_type == CONST.FLOAT:
                record.value_type = CONST.FLOAT

            if first_char_value_type == CONST.DATE:
                record.value_type = CONST.DATE

            if first_char_value_type == CONST.HTML:
                record.value_type = CONST.HTML

            if first_char_value_type == CONST.USERS:
                record.value_type = CONST.USERS

            if first_char_value_type == CONST.GROUPS:
                record.value_type = CONST.GROUPS

            if first_char_value_type == CONST.RELATION:
                record.value_type = CONST.RELATION

    def _get_default_value_by_variable_name(self, variable_name, raise_error=True):
        record = self.search([("variable_name", "=", variable_name)], limit=1)
        message = f"Không tìm thấy tên biến cho giá trị mặc định {variable_name}"

        if not record and raise_error:
            raise ValidationError(message)

        if record.value_type == CONST.STRING:
            return record.str_field

        if record.value_type == CONST.INTEGER:
            return record.int_field

        if record.value_type == CONST.FLOAT:
            return record.float_field

        if record.value_type == CONST.DATE:
            return record.date_field

        if record.value_type == CONST.HTML:
            return record.html_field

        if record.value_type == CONST.USERS:
            return record.user_ids

        if record.value_type == CONST.GROUPS:
            return record.group_ids

        if record.value_type == CONST.RELATION:
            return record.default_value_for_relation_ids

    def get_all_fields(self):
        self.ensure_one()
        model = self.env[self.str_field].search([])
        if model:
            all_fields = ",".join(model.fields_get())
            all_fields = all_fields.split("write_date")
            all_fields = all_fields[1]
            self.str_field = all_fields
