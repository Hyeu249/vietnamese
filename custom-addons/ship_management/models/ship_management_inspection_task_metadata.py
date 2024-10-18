# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from . import CONST


class ShipManagementInspectionTaskMetadata(models.Model):
    _name = "ship.ship.management.inspection.task.metadata"
    _description = "Ship management inspection task metadata records"
    _inherit = ["utilities.notification"]
    _check_company_auto = True

    name = fields.Char("Name", tracking=True)
    description = fields.Char("Description", tracking=True)

    # relations
    ship_management_inspection_task_ids = fields.One2many(
        "ship.ship.management.inspection.task",
        "ship_management_inspection_task_metadata_id",
        string="Ship management inspection task",
        tracking=True,
    )
    ship_management_inspection_scope_metadata_id = fields.Many2one(
        "ship.ship.management.inspection.scope.metadata",
        string="Ship management inspection scope metadata",
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
            model_name = "ship.ship.management.inspection.task.metadata"
            vals["ref"] = self.env["ir.sequence"].next_by_code(model_name)
        return super(ShipManagementInspectionTaskMetadata, self).create(vals_list)

    def name_get(self):
        result = []
        for report in self:
            name = report.name or _("New")
            result.append((report.id, name))
        return result
