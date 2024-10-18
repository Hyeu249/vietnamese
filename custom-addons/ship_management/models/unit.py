# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from . import CONST


class Unit(models.Model):
    _name = "ship.unit"
    _description = "Unit records"
    _inherit = ["utilities.notification"]

    name = fields.Char("Name", tracking=True)
    description = fields.Char("Description", tracking=True)
    store_type = fields.Selection(
        CONST.STORE_TYPE,
        string="Store Type",
        default=CONST.EACH_ENTITY,
        tracking=True,
    )

    # Define SQL constraint
    _sql_constraints = [
        (
            "unique_name",
            "unique (name)",
            "name must be unique.",
        ),
    ]

    # relations
    material_ids = fields.One2many(
        "ship.material",
        inverse_name="unit_id",
        string="Material",
        tracking=True,
    )

    # sequential
    ref = fields.Char(string="Code", default=lambda self: _("New"))

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            vals["ref"] = self.env["ir.sequence"].next_by_code("ship.unit")
        return super(Unit, self).create(vals_list)

    def name_get(self):
        result = []
        for report in self:
            name = report.name or _("New")
            result.append((report.id, name))
        return result
