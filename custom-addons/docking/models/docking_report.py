# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from . import CONST
from odoo.exceptions import ValidationError


class ExpectedCostReport(models.Model):
    _name = "docking.expected.cost.report"
    _description = "Dự toán chi phí"
    _inherit = ["utilities.approval.status"]

    comment = fields.Char("Comment", tracking=True)

    # related
    name_for_noti = fields.Char(
        related="docking_plan_id.name",
        string="Docking name",
    )

    # relations
    docking_plan_id = fields.Many2one(
        "docking.docking.plan",
        string="Docking plan",
        tracking=True,
    )

    material_quote_ids = fields.One2many(
        "docking.material.quote",
        "expected_cost_report_id",
        related="docking_plan_id.material_survey_data_ids.material_quote_ids",
        string="Material Quote",
        tracking=True,
    )
    job_quote_ids = fields.One2many(
        "docking.job.quote",
        "expected_cost_report_id",
        related="docking_plan_id.equipment_survey_data_ids.maintenance_scope_report_ids.job_quote_ids",
        string="Job Quote",
        tracking=True,
    )

    # Define SQL constraint
    _sql_constraints = [
        (
            "unique_docking_plan_id",
            "unique (docking_plan_id)",
            "docking_plan_id must be unique.",
        ),
    ]

    # sequential
    ref = fields.Char(string="Code", default=lambda self: _("New"))

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            model_name = "docking.expected.cost.report"
            vals["ref"] = self.env["ir.sequence"].next_by_code(model_name)

        results = super(ExpectedCostReport, self).create(vals_list)
        return results

    def write(self, vals):
        result = super(ExpectedCostReport, self).write(vals)

        if "approval_status" in vals:
            docking_plan_id = self.docking_plan_id
            are_all_surveys_approved = docking_plan_id._are_all_survey_datas_approved()
            message = "Báo cáo chưa đủ điều kiện để tham gia luồng duyệt, vui lòng liên hệ quản trị viên!"

            if not are_all_surveys_approved:
                raise ValidationError(message)

        return result

    def name_get(self):
        result = []
        for report in self:
            name = report.ref or _("New")
            result.append((report.id, name))
        return result
