# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from . import CONST


class MaterialSurveyMetadata(models.Model):
    _name = "docking.material.survey.metadata"
    _description = "Material survey metadata records"
    _inherit = ["utilities.notification"]
    _check_company_auto = True

    name = fields.Char("Name", tracking=True)
    description = fields.Char("Description", tracking=True)
    spare_part_no = fields.Char("Spare part no", tracking=True)
    unit = fields.Char("Unit", tracking=True)
    origin = fields.Char("origin", tracking=True)
    material_type = fields.Selection(
        CONST.MATERIAL_TYPE,
        string="Material Type",
        default=CONST.MATERIAL,
        tracking=True,
    )

    # relations
    material_group_id = fields.Many2one(
        "docking.material.group", string="Material Group", required=True, tracking=True
    )
    supplier_ids = fields.Many2many(
        "docking.supplier", string="Supplier", tracking=True
    )
    material_survey_data_ids = fields.One2many(
        "docking.material.survey.data",
        "material_survey_metadata_id",
        string="Material Survey Data",
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
                "docking.material.survey.metadata"
            )
        return super(MaterialSurveyMetadata, self).create(vals_list)

    def name_get(self):
        result = []
        for report in self:
            name = report.name or _("New")
            result.append((report.id, name))
        return result
