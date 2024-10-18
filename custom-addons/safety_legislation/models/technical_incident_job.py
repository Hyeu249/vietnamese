# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from ...utilities.models import CONST as UTILITIES_CONST
from . import CONST
from odoo.exceptions import ValidationError


class MaterialAssignment(models.Model):
    _inherit = "ship.material.assignment"

    technical_incident_job_id = fields.Many2one("legis.technical.incident.job")


class TechnicalIncidentJob(models.Model):
    _name = "legis.technical.incident.job"
    _description = "Technical incident job records"
    _inherit = ["utilities.notification"]
    _check_company_auto = True

    name = fields.Char("Name", tracking=True)
    description = fields.Char("Description", tracking=True)
    finished_at = fields.Date("Finished at", tracking=True)

    # relations
    technical_incident_id = fields.Many2one(
        "legis.technical.incident",
        string="Technical incident",
        tracking=True,
    )

    material_assignment_ids = fields.One2many(
        "ship.material.assignment",
        "technical_incident_job_id",
        string="Material assignment",
        tracking=True,
    )

    # company
    company_id = fields.Many2one(
        "res.company", required=True, default=lambda self: self.env.company
    )

    # sequential
    ref = fields.Char(string="Code", default=lambda self: _("New"))

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            model_name = "legis.technical.incident.job"
            vals["ref"] = self.env["ir.sequence"].next_by_code(model_name)
        result = super(TechnicalIncidentJob, self).create(vals_list)

        return result

    def write(self, vals):
        self.ensure_one()
        result = super(TechnicalIncidentJob, self).write(vals)

        return result

    def name_get(self):
        result = []
        for report in self:
            name = report.ref or _("New")
            result.append((report.id, name))
        return result
