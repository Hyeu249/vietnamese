# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _


class JobMaterialRequirement(models.Model):
    _name = "ship.job.material.requirement"
    _description = "Job material requirement records"
    _inherit = ["utilities.notification"]
    _check_company_auto = True

    required_quantity = fields.Float("Required quantity", tracking=True)

    # relation field
    unit = fields.Char(
        related="material_id.unit",
        string="Unit",
        store=False,
    )

    # company
    company_id = fields.Many2one(
        "res.company", required=True, default=lambda self: self.env.company
    )

    # relations
    job_id = fields.Many2one("ship.job", string="Job", tracking=True)
    material_id = fields.Many2one("ship.material", string="Material", tracking=True)

    # sequential
    ref = fields.Char(string="Code", default=lambda self: _("New"))

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            vals["ref"] = self.env["ir.sequence"].next_by_code(
                "ship.job.material.requirement"
            )
        return super(JobMaterialRequirement, self).create(vals_list)

    def name_get(self):
        result = []
        for report in self:
            name = report.ref or _("New")
            result.append((report.id, name))
        return result

    def are_there_enough_materials(self):
        self.ensure_one()
        available_quantity = self.material_id.available_quantity
        required_quantity = self.required_quantity
        enough_stock = available_quantity >= required_quantity
        return enough_stock
