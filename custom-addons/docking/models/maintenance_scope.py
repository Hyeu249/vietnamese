# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from . import CONST
from odoo.exceptions import ValidationError


class MaintenanceScope(models.Model):
    _name = "docking.maintenance.scope"
    _description = "Maintenance scope records"
    _inherit = ["ship.maintenance.scope.template"]
    _check_company_auto = True

    # relations
    job_ids = fields.One2many(
        "docking.job",
        "maintenance_scope_id",
        string="Job",
        tracking=True,
    )
    maintenance_scope_report_ids = fields.One2many(
        "docking.maintenance.scope.report",
        "maintenance_scope_id",
        string="Maintenance scope report",
        tracking=True,
    )
    equipment_survey_metadata_id = fields.Many2one(
        "docking.equipment.survey.metadata",
        string="Equipment survey metadata",
        tracking=True,
    )
    ship_maintenance_scope_id = fields.Many2one(
        "ship.maintenance.scope",
        string="Maintenance scope",
        tracking=True,
    )
    job_ids = fields.One2many(
        "docking.job",
        "maintenance_scope_id",
        string="Job",
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
            vals["ref"] = self.env["ir.sequence"].next_by_code(
                "docking.maintenance.scope"
            )
        result = super(MaintenanceScope, self).create(vals_list)
        return result

    def name_get(self):
        result = []
        for report in self:
            name = report.name or _("New")
            result.append((report.id, name))
        return result

    def _is_ship_under_a_maintenance(self):
        self.ensure_one()

        return self.ship_maintenance_scope_id._is_under_maintenance()
