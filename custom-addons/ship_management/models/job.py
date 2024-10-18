# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from . import CONST


class Job(models.Model):
    _name = "ship.job"
    _description = "Job records"
    _inherit = ["utilities.notification"]
    _check_company_auto = True

    name = fields.Char("Name", tracking=True)
    description = fields.Char("Description", tracking=True)
    assigned_group = fields.Char("Assigned group", tracking=True)

    # related
    maintenance_type = fields.Selection(
        CONST.MAINTENANCE_TYPE,
        related="maintenance_scope_id.maintenance_type",
        string="Maintenance Type",
        tracking=True,
    )

    # company
    company_id = fields.Many2one(
        "res.company", required=True, default=lambda self: self.env.company
    )

    # relations
    maintenance_scope_id = fields.Many2one(
        "ship.maintenance.scope", string="Maintenance scope", tracking=True
    )
    supplier_ids = fields.Many2many(
        "ship.supplier",
        string="Supplier",
        domain="[('classified_for_job', '=', True)]",
        tracking=True,
    )
    job_quote_ids = fields.One2many(
        "ship.job.quote", "job_id", string="Job quote", tracking=True
    )
    job_quote_id = fields.Many2one("ship.job.quote", string="Job quote", tracking=True)
    job_material_requirement_ids = fields.One2many(
        "ship.job.material.requirement",
        "job_id",
        string="Job Material Requirement",
        tracking=True,
    )
    job_paint_requirement_ids = fields.One2many(
        "ship.job.paint.requirement",
        "job_id",
        string="Job Paint Requirement",
        tracking=True,
    )

    # sequential
    ref = fields.Char(string="Code", default=lambda self: _("New"))

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            vals["ref"] = self.env["ir.sequence"].next_by_code("ship.job")
        return super(Job, self).create(vals_list)

    def name_get(self):
        result = []
        for report in self:
            name = report.name or _("New")
            maintenance_type = report.maintenance_type
            result.append((report.id, f"{name}({maintenance_type})"))
        return result
