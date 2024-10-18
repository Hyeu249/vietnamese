# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from . import CONST


class TechnicalInspectionTaskMetadata(models.Model):
    _name = "ship.technical.inspection.task.metadata"
    _description = "Technical inspection task metadata records"
    _inherit = ["utilities.notification"]
    _check_company_auto = True

    name = fields.Char("Name", tracking=True)
    description = fields.Char("Description", tracking=True)

    # relations
    technical_inspection_task_ids = fields.One2many(
        "ship.technical.inspection.task",
        "technical_inspection_task_metadata_id",
        string="Technical inspection task",
        tracking=True,
    )
    technical_inspection_scope_metadata_id = fields.Many2one(
        "ship.technical.inspection.scope.metadata",
        string="Technical inspection scope metadata",
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
            model_name = "ship.technical.inspection.task.metadata"
            vals["ref"] = self.env["ir.sequence"].next_by_code(model_name)
        return super(TechnicalInspectionTaskMetadata, self).create(vals_list)

    def name_get(self):
        result = []
        for report in self:
            name = report.name or _("New")
            result.append((report.id, name))
        return result
