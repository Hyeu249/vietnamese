# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from . import CONST


class ShipManagementInspectionScopeMetadata(models.Model):
    _name = "ship.ship.management.inspection.scope.metadata"
    _description = "Ship management inspection scope metadata records"
    _inherit = ["utilities.notification"]
    _check_company_auto = True

    name = fields.Char("Name", tracking=True)
    description = fields.Char("Description", tracking=True)

    # relations
    ship_management_inspection_scope_ids = fields.One2many(
        "ship.ship.management.inspection.scope",
        "ship_management_inspection_scope_metadata_id",
        string="Ship management inspection scope",
        tracking=True,
    )
    ship_management_inspection_task_metadata_ids = fields.One2many(
        "ship.ship.management.inspection.task.metadata",
        "ship_management_inspection_scope_metadata_id",
        string="Ship management inspection task metadata",
        tracking=True,
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
            model_name = "ship.ship.management.inspection.scope.metadata"
            vals["ref"] = self.env["ir.sequence"].next_by_code(model_name)
        return super(ShipManagementInspectionScopeMetadata, self).create(vals_list)

    def name_get(self):
        result = []
        for report in self:
            name = report.name or _("New")
            result.append((report.id, name))
        return result
