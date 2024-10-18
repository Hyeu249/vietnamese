# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from . import CONST
from odoo.exceptions import ValidationError


class FactorNoteOption(models.Model):
    _name = "docking.factor.note.option"
    _description = "Factor note option records"
    _inherit = ["utilities.notification"]
    _check_company_auto = True

    name = fields.Char("Name", tracking=True)
    value = fields.Float("Value", tracking=True)
    maintenance_scope_string = fields.Char(
        "Maintenance scope string",
        compute="_get_maintenance_scope_string",
        store=True,
        tracking=True,
    )

    # relations
    maintenance_scope_ids = fields.Many2many(
        "docking.maintenance.scope", string="Maintenance scope"
    )

    # sequential
    ref = fields.Char(string="Code", default=lambda self: _("New"))

    # company
    company_id = fields.Many2one(
        "res.company", required=True, default=lambda self: self.env.company
    )

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            model_name = "docking.factor.note.option"
            vals["ref"] = self.env["ir.sequence"].next_by_code(model_name)
        return super(FactorNoteOption, self).create(vals_list)

    def name_get(self):
        result = []
        for report in self:
            name = report.name or _("New")
            result.append((report.id, name))
        return result

    @api.depends("maintenance_scope_ids")
    def _get_maintenance_scope_string(self):
        for record in self:
            if record.maintenance_scope_ids:
                names = record.maintenance_scope_ids.mapped(lambda e: e.name)
                string = ",".join(names)
                record.maintenance_scope_string = string
            else:
                record.maintenance_scope_string = ""
