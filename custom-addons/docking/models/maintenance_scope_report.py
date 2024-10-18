# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from . import CONST
from ...ship_management.models import CONST as SHIP_CONST
from odoo.exceptions import ValidationError


class MaintenanceScopeReport(models.Model):
    _name = "docking.maintenance.scope.report"
    _description = "Báo cáo sửa chữa-docking"
    _inherit = ["ship.maintenance.scope.report.template", "utilities.approval.status"]
    _check_company_auto = True

    result_evaluate = fields.Char("Result Evaluation", tracking=True)

    # related
    name_for_noti = fields.Char(
        related="maintenance_scope_id.name",
        string="Name",
    )

    # sequential
    ref = fields.Char(string="Code", default=lambda self: _("New"))

    # company
    company_id = fields.Many2one(
        "res.company", required=True, default=lambda self: self.env.company
    )
    result_evaluate = fields.Char(
        "Result Evaluation",
        tracking=True,
    )

    # related
    equipment_name = fields.Char(
        related="equipment_survey_metadata_id.name",
        string="Equipment",
        tracking=True,
    )
    maintenance_type = fields.Selection(
        SHIP_CONST.MAINTENANCE_TYPE,
        string="Maintenance Type",
        related="maintenance_scope_id.maintenance_type",
        tracking=True,
    )
    department_in_charge = fields.Selection(
        SHIP_CONST.DEPARTMENT_IN_CHARGE,
        related="maintenance_scope_id.department_in_charge",
        string="Department in charge",
        tracking=True,
    )
    inspection_date = fields.Date(
        "Inspection Date",
        tracking=True,
    )
    survey_type = fields.Selection(
        CONST.ARISE_SELECTION,
        string="Survey type",
        related="equipment_survey_data_id.survey_type",
        store=True,
        tracking=True,
    )
    docking_plan_id = fields.Many2one(
        "docking.docking.plan",
        related="equipment_survey_data_id.docking_plan_id",
        string="Docking plan",
        store=True,
        tracking=True,
    )

    # relations
    maintenance_scope_id = fields.Many2one(
        "docking.maintenance.scope",
        string="Maintenance scope",
        domain="[('equipment_survey_metadata_id', '=', equipment_survey_metadata_id)]",
        tracking=True,
    )
    job_quote_ids = fields.One2many(
        "docking.job.quote",
        "maintenance_scope_report_id",
        string="Job quote",
        tracking=True,
    )
    equipment_survey_data_id = fields.Many2one(
        "docking.equipment.survey.data",
        string="Equipment survey data",
        tracking=True,
    )
    equipment_survey_metadata_id = fields.Many2one(
        "docking.equipment.survey.metadata",
        related="equipment_survey_data_id.equipment_survey_metadata_id",
        tracking=True,
    )

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            vals["ref"] = self.env["ir.sequence"].next_by_code(
                "docking.maintenance.scope.report"
            )
        result = super(MaintenanceScopeReport, self).create(vals_list)

        for record in result:
            ship_scope_id = record.maintenance_scope_id.ship_maintenance_scope_id
            ship_scope_id.is_docking = True

        return result

    def write(self, vals):

        result = super(MaintenanceScopeReport, self).write(vals)

        if "approval_status" in vals:
            self._restrict_approval_flow()

        return result

    def unlink(self):
        for record in self:
            ship_scope_id = record.maintenance_scope_id.ship_maintenance_scope_id
            ship_scope_id.is_docking = False

            record.job_quote_ids.unlink()

        return super(MaintenanceScopeReport, self).unlink()

    def name_get(self):
        result = []
        for report in self:
            name = report.ref or _("New")
            result.append((report.id, name))
        return result

    def action_approve(self):
        self.ensure_one()
        self.ref_job_state = CONST.TODO
        super(MaintenanceScopeReport, self).action_approve()

    def action_reject(self):
        self.ensure_one()
        self.ref_job_state = CONST.UNAPPROVED
        super(MaintenanceScopeReport, self).action_reject()

    def set_ref_job_state(self):
        self.ensure_one()
        if self._is_approved():
            super(MaintenanceScopeReport, self).set_ref_job_state()
        else:
            self.ref_job_state = CONST.UNAPPROVED

    def _restrict_approval_flow(self):
        self.ensure_one()
        docking_plan_id = self.equipment_survey_data_id.docking_plan_id
        survey = self.equipment_survey_data_id
        start_date = docking_plan_id.start_date
        today = fields.Date.today()

        valid_survey = self._is_approved_expected_cost_report() or survey._is_arise()
        valid_docking_date = start_date and today >= start_date
        valid_expected_date = self._have_expected_date_end_and_start()

        if not survey._is_arise():
            if not valid_survey:
                raise ValidationError("Chưa duyệt dự toán chi phí")

        if not valid_docking_date:
            raise ValidationError("Ngày docking phải bé hơn hoặc bằng hôm nay!")

        if not valid_expected_date:
            raise ValidationError("Chưa có ngày dự kiến ở báo cáo sửa chữa!")

    def _have_expected_date_end_and_start(self):
        if self.expected_implement_date and self.expected_implement_date:
            return True
        else:
            return False

    def _is_approved_expected_cost_report(self):
        self.ensure_one()
        docking_plan_id = self.equipment_survey_data_id.docking_plan_id
        expected_cost_report_id = docking_plan_id._get_expected_cost_report_id()
        return expected_cost_report_id and expected_cost_report_id._is_approved()

    def custom_export_pms_form_to_xlsx(self):
        self.ensure_one

    def custom_export_pms_review_to_xlsx(self):
        self.ensure_one

    def finish_report_if_all_job_quote_finished(self):
        self.ensure_one()
        if self._are_confirmed_all_job_quotes():
            scope_id = self.maintenance_scope_id
            ship_scope_id = self.maintenance_scope_id.ship_maintenance_scope_id

            scope_id.last_maintenance_date = self.finished_at
            ship_scope_id.is_docking = False
            ship_scope_id.last_maintenance_date = self.finished_at
            ship_scope_id.create_new_report_if_threshold_maintenance()

    def open_record(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "res_model": self._name,
            "view_mode": "form",
            "res_id": self.id,
            "target": "current",
            "context": self.env.context,
        }
