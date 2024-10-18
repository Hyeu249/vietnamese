# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from . import CONST


class Job(models.Model):
    _name = "docking.job"
    _description = "Job records"
    _inherit = ["utilities.notification"]
    _check_company_auto = True

    name = fields.Char("Name", tracking=True)
    description = fields.Char("Description", tracking=True)

    # relations
    supplier_ids = fields.Many2many(
        "docking.supplier", string="Supplier", tracking=True
    )
    job_quote_id = fields.Many2one(
        "docking.job.quote",
        string="Job quote",
        tracking=True,
    )
    job_quote_ids = fields.One2many(
        "docking.job.quote",
        "job_id",
        string="Job quote",
        tracking=True,
    )
    maintenance_scope_id = fields.Many2one(
        "docking.maintenance.scope",
        string="Maintenance scope",
        tracking=True,
    )
    job_final_cost_formula_id = fields.Many2one(
        "docking.job.final.cost.formula",
        string="Job final cost formula",
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
            vals["ref"] = self.env["ir.sequence"].next_by_code("docking.job")
        return super(Job, self).create(vals_list)

    def name_get(self):
        result = []
        for report in self:
            name = report.name or _("New")
            result.append((report.id, name))
        return result
