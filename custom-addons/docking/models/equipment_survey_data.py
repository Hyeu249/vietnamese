# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from . import CONST
from odoo.exceptions import ValidationError


class EquipmentSurveyData(models.Model):
    _name = "docking.equipment.survey.data"
    _description = "Khảo sát thiết bị"
    _inherit = ["utilities.approval.status"]
    _check_company_auto = True

    code = fields.Char("Code", tracking=True)
    survey_date = fields.Date("Survey date", tracking=True)
    list_no = fields.Char("D/D List no", tracking=True)
    survey_type = fields.Selection(
        CONST.ARISE_SELECTION,
        string="Survey type",
        default=CONST.NORMAL,
        tracking=True,
    )

    # related
    name_for_noti = fields.Char(
        related="docking_plan_id.name",
        string="Docking name",
    )

    # relations
    maintenance_scope_report_ids = fields.One2many(
        "docking.maintenance.scope.report",
        "equipment_survey_data_id",
        string="Maintenance scope report",
        tracking=True,
    )
    docking_plan_id = fields.Many2one(
        "docking.docking.plan",
        required=True,
        string="Docking plan",
        tracking=True,
    )
    equipment_survey_metadata_id = fields.Many2one(
        "docking.equipment.survey.metadata",
        string="Equipment survey metadata",
        required=True,
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
            model_name = "docking.equipment.survey.data"
            vals["ref"] = self.env["ir.sequence"].next_by_code(model_name)
        result = super(EquipmentSurveyData, self).create(vals_list)
        for record in result:
            if record._is_arise():
                record.sudo_approve()
            if not record.maintenance_scope_report_ids:
                record.create_maintenance_scope_report()
        return result

    def write(self, vals):
        result = super(EquipmentSurveyData, self).write(vals)

        if "survey_type" in vals:
            raise ValidationError("Không được sửa trường survey_type!!")

        for record in self:
            if "approval_status" in vals and not record.maintenance_scope_report_ids:
                message = "Không có hạng mục sửa chữa, vui lòng kiểm tra lại!!"
                raise ValidationError(message)

            # if record._is_arise():
            #     message = "Không được tham gia luồng duyệt, khi khảo sát là phát sinh!!"
            #     if "approval_status" in vals:
            #         raise ValidationError(message)

        return result

    def unlink(self):
        for record in self:
            record.maintenance_scope_report_ids.unlink()
        return super(EquipmentSurveyData, self).unlink()

    def name_get(self):
        result = []
        for report in self:
            name = report.ref or _("New")
            result.append((report.id, name))
        return result

    def create_maintenance_scope_report(self):
        for record in self:
            maintenance_scope_ids = self._get_all_maintenance_scopes()
            for maintenance_scope_id in maintenance_scope_ids:
                self.maintenance_scope_report_ids.create(
                    {
                        "equipment_survey_data_id": record.id,
                        "maintenance_scope_id": maintenance_scope_id.id,
                    }
                )

    def _get_all_maintenance_scopes(self):
        self.ensure_one()
        equipment_survey_metadata_id = self.equipment_survey_metadata_id
        maintenance_scope_ids = equipment_survey_metadata_id.maintenance_scope_ids
        return maintenance_scope_ids

    def _is_arise(self):
        self.ensure_one()
        return self.survey_type == CONST.ARISE

    def propose_all_reports(self):
        self.ensure_one()
        for report in self.maintenance_scope_report_ids:
            report.action_propose()

    def unpropose_all_reports(self):
        self.ensure_one()
        for report in self.maintenance_scope_report_ids:
            report.action_unpropose()

    def action_approve_all_reports(self):
        self.ensure_one()
        for report in self.maintenance_scope_report_ids:
            report.action_approve()

    def action_reject_all_reports(self):
        self.ensure_one()
        for report in self.maintenance_scope_report_ids:
            report.action_reject()

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
