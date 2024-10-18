# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from . import CONST


class EquipmentSurveyGroup(models.Model):
    _name = "docking.equipment.survey.group"
    _description = "Equipment survey group records"
    _inherit = ["utilities.notification"]
    _check_company_auto = True

    name = fields.Char("Name", tracking=True)
    description = fields.Char("Description", tracking=True)

    # relations
    docking_plan_ids = fields.Many2many(
        "docking.docking.plan",
        string="Docking plan",
        tracking=True,
    )
    equipment_survey_metadata_ids = fields.One2many(
        "docking.equipment.survey.metadata",
        "equipment_survey_group_id",
        string="Equipment survey metadata",
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
            vals["ref"] = self.env["ir.sequence"].next_by_code(
                "docking.equipment.survey.group"
            )
        return super(EquipmentSurveyGroup, self).create(vals_list)

    def name_get(self):
        result = []
        for report in self:
            name = report.name or _("New")
            result.append((report.id, name))
        return result
