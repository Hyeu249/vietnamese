# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from . import CONST


class MaterialGroup(models.Model):
    _name = "docking.material.group"
    _description = "Material group records"
    _inherit = ["utilities.notification"]
    _check_company_auto = True

    name = fields.Char("Name", tracking=True)
    description = fields.Char("Description", tracking=True)

    # relations
    material_survey_metadata_ids = fields.One2many(
        "docking.material.survey.metadata",
        "material_group_id",
        string="Material survey metadata",
        tracking=True,
    )
    approval_flow_id = fields.Many2one(
        "utilities.approval.flow", string="Approval flow", required=True, tracking=True
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
            vals["ref"] = self.env["ir.sequence"].next_by_code("docking.material.group")
        return super(MaterialGroup, self).create(vals_list)

    def name_get(self):
        result = []
        for report in self:
            name = report.name or _("New")
            result.append((report.id, name))
        return result
