# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from . import CONST
from odoo.exceptions import ValidationError


class EquipmentSurveyMetadata(models.Model):
    _name = "docking.equipment.survey.metadata"
    _description = "Equipment survey metadata records"
    _inherit = ["utilities.notification"]
    _check_company_auto = True

    name = fields.Char("Name", tracking=True)
    description = fields.Char("Description", tracking=True)

    # relations
    equipment_survey_group_id = fields.Many2one(
        "docking.equipment.survey.group",
        string="Equipment survey group",
        required=False,
        tracking=True,
    )
    maintenance_scope_ids = fields.One2many(
        "docking.maintenance.scope",
        "equipment_survey_metadata_id",
        string="Maintenance scope",
        tracking=True,
    )
    equipment_survey_data_ids = fields.One2many(
        "docking.equipment.survey.data",
        "equipment_survey_metadata_id",
        string="Equipment survey data",
        tracking=True,
    )

    # sequential
    ref = fields.Char(string="Code", default=lambda self: _("New"))

    # company
    company_id = fields.Many2one(
        "res.company", required=True, default=lambda self: self.env.company
    )

    # @api.constrains("maintenance_scope_ids")
    # def _check_required_maintenance_scope(self):
    #     for record in self:
    #         if not record.maintenance_scope_ids:
    #             raise ValidationError("Bắt buộc nhập hạng mục sửa chữa!!")

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            vals["ref"] = self.env["ir.sequence"].next_by_code(
                "docking.equipment.survey.metadata"
            )
        return super(EquipmentSurveyMetadata, self).create(vals_list)

    def name_get(self):
        result = []
        for report in self:
            name = report.name or _("New")
            result.append((report.id, name))
        return result
