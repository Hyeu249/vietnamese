# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from . import CONST
from odoo.exceptions import ValidationError
import logging


class IrModel(models.Model):
    _inherit = "ir.model"

    name = fields.Char(string="Name", required=True)
    model = fields.Char(default=lambda self: self._get_model_name(), required=True)

    prefix_name = fields.Char(string="Prefix name")
    vietnamese_custom = fields.Boolean(string="Vietnamese custom")

    # sequential
    ref = fields.Char(string="Code", default=lambda self: _("New"))

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            self.set_sequence_and_model_name(vals)

        result = super(IrModel, self).create(vals_list)

        return result

    def write(self, vals):
        self.ensure_one()
        result = super(IrModel, self).write(vals)

        return result

    def unlink(self):

        return super(IrModel, self).unlink()

    def _get_model_name(self):
        model_name = "ir.model"
        number_next_actual = self.env["ir.sequence"].next_by_number(model_name)

        return f"x_vietnamese.table.{number_next_actual}"

    def set_sequence_and_model_name(self, vals):
        vals["model"] = self._get_model_name()
        vals["ref"] = self.env["ir.sequence"].next_by_code("ir.model")
