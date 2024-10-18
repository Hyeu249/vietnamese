# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from . import CONST
from odoo.exceptions import ValidationError
from datetime import timedelta, datetime


class DefaultValueForRelation(models.Model):
    _name = "utilities.default.value.for.relation"
    _description = "Default value for relation records"
    _inherit = ["utilities.notification"]
    _check_company_auto = True

    text_1 = fields.Text(string="Field 1", tracking=True)
    text_2 = fields.Text(string="Field 2", tracking=True)

    # relations
    default_value_id = fields.Many2one(
        "utilities.default.value", string="Default value"
    )

    # sequential
    ref = fields.Char(string="Code", default=lambda self: _("New"))

    # company

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            model_name = "utilities.default.value.for.relation"
            vals["ref"] = self.env["ir.sequence"].next_by_code(model_name)

        result = super(DefaultValueForRelation, self).create(vals_list)
        return result

    def name_get(self):
        result = []
        for report in self:
            name = report.ref or _("New")
            result.append((report.id, name))
        return result
